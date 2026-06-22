"""
find_published_duplicates.py — находит дубли среди УЖЕ ОПУБЛИКОВАННЫХ статей.

smart_cluster.py обрабатывал только status='pending' ключевики — все
статьи, опубликованные ДО появления кластеризации (включая известный
facebook-кейс: 3 статьи "delete facebook account" разными словами),
никогда не проверялись на дубли по смыслу.

Этот скрипт сканирует articles-meta.json, группирует ключевики уже
ОПУБЛИКОВАННЫХ статей через Gemini по совпадению намерения (не слов),
и для каждой найденной группы дублей оставляет статью с наибольшим
объёмом поиска, остальные — удаляет (mdx-файл) и помечает их ключевик
как status='duplicate' (не 'done', чтобы не путать дальнейшую
статистику и не мешать кластеризации в будущем).

ИСПОЛЬЗОВАНИЕ:
  py -3.11 find_published_duplicates.py en             # dry-run, отчёт
  py -3.11 find_published_duplicates.py en --apply      # удалить дубли
"""

import sqlite3
import json
import re
import sys
import time
import threading
import queue
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

DB_PATH      = ROOT / 'keywords.db'
META_FILE    = ROOT / 'data' / 'articles-meta.json'
CONTENT_DIR  = ROOT / 'content'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

BATCH_SIZE = 40
TIMEOUT_SEC = 75
SUPPORTED_LANGS = ('en', 'de', 'nl', 'sv')

# ==========================================
# ЗАЩИТНАЯ ПРОВЕРКА ГРУПП (после ответа Gemini, до применения)
# ==========================================
# Семантическая кластеризация LLM не идеальна — найдены реальные случаи
# ложного объединения: "fix a leaky faucet" + "fix a wobbly chair" (никак
# не связанные предметы, общее только "DIY guide"), "oil stains" + "ink
# stains" + "blood stains" (разные вещества, разные способы выведения),
# "facebook ACCOUNT" + "facebook PAGE" (разные сущности), "snapchat
# account" + "instagram account" (разные бренды). Без проверки скрипт
# удалил бы ценные уникальные статьи.
#
# Эта проверка — не замена семантике Gemini, а простая страховка поверх:
# требует общее значимое слово (предмет/вещество) у ВСЕХ участников
# группы, и блокирует объединение при разных брендах или конфликтующих
# по смыслу словах (account/page и т.п.), даже если что-то общее есть.

GENERIC_WORDS = {
    'a','an','the','to','your','you','my','i','do','does','can','how',
    'get','rid','of','out','off','from','for','with','without','and','or',
    'on','at','in','is','are','it','this','that',
    'easily','effectively','safely','quickly','permanently','completely',
    'properly','naturally','fast','simple','simply','guide','complete',
    'step','steps','by','diy','home','new','easy','safe','ways','way',
    'tips','tip','make','create','best','good','great','your','yours',
    # глаголы-действия, слишком общие сами по себе, чтобы быть единственным
    # основанием для объединения (нашли на тесте: "fix a leaky faucet" +
    # "fix a wobbly chair" совпали только по слову "fix" — разные предметы;
    # "clean washing machine" + "clean dishwasher" — та же проблема с "clean")
    'fix','repair','take','build','set','setup','install','change',
    'clean','wash','remove','replace','open','close','use','find',
    'put','add','run','start','stop','turn','keep','help','check',
    # шаблонные существительные в "remove X from clothes" — без этого
    # "oil stains" + "ink stains" + "blood stains" совпадали по словам
    # "stains"+"clothes", хотя вещество (распознающее слово) разное
    'stain','stains','clothe','clothes','clothing','spot','spots',
}

# UK/US и сокращённые варианты написания — без этого 'mould'!='mold'
SPELLING_ALIASES = {
    'mould': 'mold', 'colour': 'color', 'favourite': 'favorite',
    'centre': 'center', 'tyre': 'tire', 'jewellery': 'jewelry',
    'fb': 'facebook', 'insta': 'instagram', 'ig': 'instagram',
    'snap': 'snapchat', 'yt': 'youtube',
}

BRAND_WORDS = {
    'facebook','instagram','snapchat','tiktok','twitter','gmail','google',
    'whatsapp','telegram','youtube','linkedin','pinterest','reddit',
    'amazon','netflix','spotify','discord','outlook','yahoo','icloud',
}

# Слова, которые если встречаются НА РАЗНЫХ СТОРОНАХ группы — почти
# наверняка разные сущности/темы, даже при остальном словесном совпадении
CONFLICTING_PAIRS = [
    ('account', 'page'), ('account', 'group'), ('account', 'profile'),
    ('page', 'group'), ('page', 'profile'), ('account', 'post'),
]

def significant_words(kw):
    words = re.sub(r'[^\w\s]', ' ', kw.lower()).split()
    words = [SPELLING_ALIASES.get(w, w) for w in words]
    # грубое снятие множественного числа EN (caps->cap), не идеально,
    # но достаточно для целей этой проверки
    words = [w[:-1] if w.endswith('s') and len(w) > 3 else w for w in words]
    return {w for w in words if w not in GENERIC_WORDS and len(w) > 1}

def group_is_plausible(keywords_in_group):
    word_sets = [significant_words(kw) for kw in keywords_in_group]
    if not word_sets:
        return False, 'пустая группа'

    common = set.intersection(*word_sets)
    if not common:
        return False, 'нет ни одного общего значимого слова — разные темы'

    all_words = set.union(*word_sets)

    brands_per_kw = [s & BRAND_WORDS for s in word_sets if s & BRAND_WORDS]
    if len(brands_per_kw) >= 2:
        first = brands_per_kw[0]
        if not all(b == first for b in brands_per_kw):
            return False, f'разные бренды в группе ({all_words & BRAND_WORDS})'

    for w1, w2 in CONFLICTING_PAIRS:
        if w1 in all_words and w2 in all_words:
            return False, f'конфликтующие понятия в группе ("{w1}" vs "{w2}")'

    return True, ''

client = genai.Client(api_key=GEMINI_API_KEY)


def call_with_timeout(fn, timeout, *args, **kwargs):
    q = queue.Queue()
    def target():
        try:
            q.put(('ok', fn(*args, **kwargs)))
        except Exception as e:
            q.put(('err', e))
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError(f'Gemini не ответил за {timeout}с')
    status, val = q.get()
    if status == 'err':
        raise val
    return val


def fix_json(text):
    text = re.sub(r'^```json\s*', '', text.strip())
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def find_duplicate_groups(keywords, lang):
    """Возвращает список групп — каждая группа это список дублирующихся keyword-строк."""
    numbered = '\n'.join(f'{i+1}. {kw}' for i, kw in enumerate(keywords))

    prompt = f"""You are analyzing keywords behind ALREADY PUBLISHED articles
(language: {lang.upper()}) to find true duplicates — different phrasings that
represent the EXACT SAME article topic/intent (one article would fully satisfy
a search for any keyword in the group).

Be CONSERVATIVE: only group keywords that are genuinely the same topic with
different wording (e.g. "how to delete facebook account permanently" and
"how do you delete a facebook account" — same intent). Do NOT group keywords
that are merely related or share a topic area but differ in specific intent
(e.g. "how to clean dryer vent" and "how to install gutters" are NOT duplicates
even though both are home-maintenance).

Keywords that have no duplicate among this list should simply not appear in
any group — do not force singletons into groups.

Return ONLY valid JSON, no markdown:
{{"duplicate_groups": [["keyword a", "keyword b"], ["keyword c", "keyword d", "keyword e"]]}}

Keywords:
{numbered}"""

    response = call_with_timeout(
        client.models.generate_content,
        TIMEOUT_SEC,
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=512),
            http_options=types.HttpOptions(timeout=65000)
        )
    )
    return json.loads(fix_json(response.text)).get('duplicate_groups', [])


def main():
    apply_flag = '--apply' in sys.argv
    lang_args = [a for a in sys.argv[1:] if not a.startswith('--')]
    lang = lang_args[0].lower() if lang_args else None

    if not lang or lang not in SUPPORTED_LANGS:
        print('Укажи язык: py -3.11 find_published_duplicates.py en [--apply]')
        return

    if not META_FILE.exists():
        print('❌ articles-meta.json не найден — сначала запусти publish.py')
        return

    with open(META_FILE, encoding='utf-8') as f:
        meta = json.load(f)

    articles = meta.get(lang, [])
    if not articles:
        print(f'Нет опубликованных статей для {lang.upper()}')
        return

    # keyword -> (slug, title)
    kw_to_article = {a['keyword'].lower().strip(): a for a in articles if a.get('keyword')}
    keywords = list(kw_to_article.keys())

    if len(keywords) < 2:
        print(f'Слишком мало статей для анализа ({len(keywords)})')
        return

    print(f'🔍 Анализируем {len(keywords)} опубликованных статей [{lang.upper()}] на дубли...')

    total_batches = (len(keywords) - 1) // BATCH_SIZE + 1
    all_groups = []

    for i in range(0, len(keywords), BATCH_SIZE):
        batch = keywords[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f'   Батч {batch_num}/{total_batches} ({len(batch)} ключевиков)...')
        try:
            groups = find_duplicate_groups(batch, lang)
            all_groups.extend(groups)
            if groups:
                print(f'      → найдено групп дублей: {len(groups)}')
        except TimeoutError as e:
            print(f'      ⏱️  Таймаут: {e} — пропускаем батч')
        except Exception as e:
            print(f'      ⚠️  Ошибка: {e} — пропускаем батч')
        time.sleep(1)

    if not all_groups:
        print('\n✅ Дублей не найдено')
        return

    # Получаем avg_searches/cpc для решения "кого оставить"
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT keyword, avg_searches, cpc_high FROM keywords WHERE lang=?', (lang,))
    kw_stats = {row[0].lower().strip(): (row[1] or 0, row[2] or 0) for row in c.fetchall()}

    print(f'\n📋 Найдено {len(all_groups)} групп дублей:\n')

    # ВАЖНО: Gemini иногда выдаёт ОДИН И ТОТ ЖЕ ключевик в ДВУХ разных
    # группах за один прогон (например "how do you plant potatoes" был и
    # 'оставить' в одной группе, и 'удалить' в другой) — без защиты это
    # может привести к удалению ВСЕХ статей кластера или произвольному
    # исходу в зависимости от порядка обработки. Та же проблема, что
    # transitive-clustering снежный ком в dedupe_keywords.py — фикс тот
    # же: первая группа, которая упомянула ключевик, "застолбила" его,
    # последующие группы это слово больше не трогают.
    claimed = set()
    to_remove = []

    for group in all_groups:
        group_lower = [g.lower().strip() for g in group if g.lower().strip() in kw_to_article]
        group_lower = [g for g in group_lower if g not in claimed]
        if len(group_lower) < 2:
            continue

        # Страховочная проверка на здравый смысл — см. комментарий в начале файла
        plausible, reason = group_is_plausible(group_lower)
        if not plausible:
            titles = [kw_to_article[g]['title'] for g in group_lower]
            print(f'  ⚠️  ПРОПУЩЕНА группа ({reason}):')
            for t in titles:
                print(f'       - {t}')
            print()
            continue

        # Сортируем по объёму поиска, при равенстве — по CPC (та же логика
        # ценности темы, что используется во всём остальном пайплайне)
        group_sorted = sorted(
            group_lower,
            key=lambda k: (kw_stats.get(k, (0,0))[0], kw_stats.get(k, (0,0))[1]),
            reverse=True
        )
        keep = group_sorted[0]
        losers = group_sorted[1:]
        claimed.add(keep)
        for l in losers:
            claimed.add(l)

        keep_article = kw_to_article[keep]
        searches_keep = kw_stats.get(keep, (0,0))[0]
        print(f'  ✅ ОСТАВИТЬ: "{keep_article["title"]}" ({searches_keep:,} поисков)')
        print(f'     slug: {keep_article["slug"]}')
        for loser in losers:
            la = kw_to_article[loser]
            searches_l = kw_stats.get(loser, (0,0))[0]
            print(f'  🗑️  УДАЛИТЬ: "{la["title"]}" ({searches_l:,} поисков)')
            print(f'     slug: {la["slug"]}')
            to_remove.append((la['slug'], loser, la['title']))
        print()

    print(f'Итого к удалению: {len(to_remove)} статей')

    if apply_flag:
        removed_files = 0
        for slug, keyword, title in to_remove:
            filepath = CONTENT_DIR / lang / f'{slug}.mdx'
            if filepath.exists():
                filepath.unlink()
                removed_files += 1
            c.execute(
                'UPDATE keywords SET status="duplicate" WHERE keyword=? AND lang=? AND status="done"',
                (keyword, lang)
            )
        conn.commit()
        print(f'\n✅ Удалено файлов: {removed_files}')
        print(f'   Статус в БД обновлён: done → duplicate для {len(to_remove)} ключевиков')
        print('\n📌 Дальше: py -3.11 scripts/publish.py  (пересоберёт индекс и sitemap)')
        print('\n⚠️  ВАЖНО: батчи по 40 не видят друг друга — дубли, чьи формулировки')
        print('   разошлись по разным батчам (например 5 статей про "delete facebook')
        print('   page" могли разбиться на 2 группы), могли быть найдены НЕ ПОЛНОСТЬЮ.')
        print(f'   После publish.py запусти ЭТОТ скрипт ещё раз на {lang} —')
        print('   с уменьшившимся списком статей шанс попасть в один батч выше.')
        print(f'   Повторяй пока не увидишь "Дублей не найдено".')
    else:
        print('\n👀 DRY-RUN — ничего не удалено.')
        print(f'   Проверь список выше, затем: py -3.11 find_published_duplicates.py {lang} --apply')

    conn.close()


if __name__ == '__main__':
    main()
