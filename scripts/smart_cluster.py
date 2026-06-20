"""
smart_cluster.py — семантическая кластеризация ключевиков через Gemini.

Заменяет связку dedupe_keywords.py + keyword_quality_check.py одним умным
шагом: Gemini группирует ключевики по поисковому намерению (не по совпадению
слов), определяет роль каждого в будущей статье и сразу присваивает категорию.

РЕЗУЛЬТАТ в БД:
  topics        — одна запись на кластер (семантическое ядро)
  keyword_roles — роль каждого ключевика (primary/secondary/faq/longtail)
  keywords.topic_id — ссылка на кластер

ИСПОЛЬЗОВАНИЕ:
  py -3.11 scripts/smart_cluster.py en            # dry-run, показать кластеры
  py -3.11 scripts/smart_cluster.py en --apply    # применить к БД
  py -3.11 scripts/smart_cluster.py en --report   # сохранить отчёт в CSV

ПРИМЕЧАНИЕ: существующий пайплайн (generator.py, publish.py) НЕ изменяется.
"""

import sqlite3
import json
import re
import sys
import time
import threading
import queue
import csv
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

DB_PATH   = ROOT / 'keywords.db'
REPORT_PATH = ROOT / 'semantic_core.csv'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

BATCH_SIZE = 30        # меньше чем в fragment-check — ответ сложнее
TIMEOUT_SEC = 90
SUPPORTED_LANGS = ('en', 'de', 'nl', 'sv')

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# ЗАЩИТА ОТ ЗАВИСАНИЯ GEMINI API
# ==========================================

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


def tier_from_value(value):
    if value >= 3000:
        return 'A'
    if value >= 500:
        return 'B'
    return 'C'


# ==========================================
# GEMINI: КЛАСТЕРИЗАЦИЯ БАТЧА
# ==========================================

def cluster_batch(keywords_with_data, lang):
    """
    keywords_with_data: list of (keyword, avg_searches, cpc_high)
    Возвращает dict с ключами 'clusters' и 'invalid'.
    """
    numbered = '\n'.join(
        f'{i+1}. {kw} [~{searches:,} поисков, CPC ~${cpc:.2f}]'
        for i, (kw, searches, cpc) in enumerate(keywords_with_data)
    )

    prompt = f"""You are an expert SEO content strategist. Analyze these {len(keywords_with_data)} keywords (language: {lang.upper()}).

GROUP them into semantic clusters based on SEARCH INTENT — not word overlap.

SAME cluster = identical user need, different phrasing:
  "delete facebook account" + "remove facebook account" + "deactivate fb account permanently" → same cluster

DIFFERENT clusters = different user need, angle, or specificity:
  "delete facebook account" vs "delete facebook page" → different (account ≠ page)
  "boil egg" vs "fry egg" → different (cooking method differs)
  "pasta pesto" vs "pasta carbonara" → different (different dish)

INVALID = not a real how-to query:
  fragments ("wie", "how to"), single words ("facebook"), brand names without action,
  ISBN numbers, URLs, proper names, anything without clear actionable intent.

For each cluster:
- cluster_id: short kebab-case slug in ENGLISH always (e.g. "delete-facebook-account")
- primary_kw: best keyword for article title (highest search volume, most natural phrasing)
- secondary: keywords to naturally weave into article body (same intent, different phrasing), max 8
- faq: question-format keywords for FAQ section (specific long-tail variants with "how/what/when/can"), max 10
- longtail: very specific variants to briefly mention in text, max 6
- category: one of [tech-devices, kitchen-food, home-garden, diy-crafts, general]

Return ONLY valid JSON (no markdown, no explanation):
{{
  "clusters": [
    {{
      "cluster_id": "delete-facebook-account",
      "primary_kw": "how to delete facebook account permanently",
      "secondary": ["remove facebook account", "close facebook account forever"],
      "faq": ["how to delete facebook without knowing password", "what happens when you delete facebook"],
      "longtail": ["delete old facebook account i cant access"],
      "category": "tech-devices"
    }}
  ],
  "invalid": ["wie", "facebook 5", "isbn 978-3-19"]
}}

Keywords to analyze:
{numbered}"""

    response = call_with_timeout(
        client.models.generate_content,
        TIMEOUT_SEC,
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
            http_options=types.HttpOptions(timeout=80000)
        )
    )
    return json.loads(fix_json(response.text))


# ==========================================
# ПРИМЕНЕНИЕ К БД
# ==========================================

def apply_clusters(clusters, invalid_kws, lang, conn):
    c = conn.cursor()
    kw_lookup = {}  # keyword_text → (id, searches, cpc)
    c.execute('SELECT id, keyword, avg_searches, cpc_high FROM keywords WHERE lang=? AND status="pending"', (lang,))
    for row in c.fetchall():
        kw_lookup[row[1].lower().strip()] = (row[0], row[2], row[3])

    topics_created = 0
    roles_assigned = 0

    for cl in clusters:
        cid = cl.get('cluster_id', '').strip()
        if not cid:
            continue

        # Собираем все ключевики кластера с объёмом
        all_kws = (
            [(cl.get('primary_kw',''), 'primary', 0)] +
            [(kw, 'secondary', i) for i, kw in enumerate(cl.get('secondary', []))] +
            [(kw, 'faq', i) for i, kw in enumerate(cl.get('faq', []))] +
            [(kw, 'longtail', i) for i, kw in enumerate(cl.get('longtail', []))]
        )

        total_searches = 0
        total_value = 0.0
        primary_kw = cl.get('primary_kw', '')
        primary_searches = 0

        for kw_text, role, priority in all_kws:
            kw_lower = kw_text.lower().strip()
            if kw_lower in kw_lookup:
                kid, searches, cpc = kw_lookup[kw_lower]
                total_searches += searches or 0
                total_value += (searches or 0) * (cpc or 0)
                if role == 'primary':
                    primary_searches = searches or 0

                # Обновляем topic_id в keywords
                c.execute('UPDATE keywords SET topic_id=? WHERE id=?', (f'{cid}_{lang}', kid))

                # КРИТИЧНО: только primary остаётся 'pending' (подлежит
                # самостоятельной генерации). secondary/faq/longtail — это
                # формулировки, которые войдут в ТЕКСТ статьи primary-темы,
                # а не отдельные статьи — переводим их в 'duplicate', как и
                # обычные дубли (исключены из генерации, обратимо).
                # Без этого они наследуют total_value всей темы через JOIN
                # в generator.py и генератор делает по ним отдельные
                # статьи-дубли на ту же тему (баг, найденный 2026-06-18).
                if role != 'primary':
                    c.execute(
                        'UPDATE keywords SET status="duplicate" WHERE id=? AND status="pending"',
                        (kid,)
                    )

                # Записываем роль
                c.execute('''
                    INSERT OR REPLACE INTO keyword_roles (keyword_id, topic_id, lang, role, priority)
                    VALUES (?,?,?,?,?)
                ''', (kid, cid, lang, role, priority))
                roles_assigned += 1

        # Создаём/обновляем запись темы
        tier = tier_from_value(total_value)
        c.execute('''
            INSERT OR REPLACE INTO topics
            (id, lang, primary_kw, category, total_searches, total_value, tier)
            VALUES (?,?,?,?,?,?,?)
        ''', (cid, lang, primary_kw, cl.get('category','general'),
              total_searches, total_value, tier))
        topics_created += 1

    # Помечаем невалидные
    invalid_count = 0
    for kw_text in (invalid_kws or []):
        kw_lower = kw_text.lower().strip()
        if kw_lower in kw_lookup:
            kid = kw_lookup[kw_lower][0]
            c.execute('UPDATE keywords SET status="fragment", topic_id=NULL WHERE id=?', (kid,))
            invalid_count += 1

    return topics_created, roles_assigned, invalid_count


# ==========================================
# ОТЧЁТ — СЕМАНТИЧЕСКОЕ ЯДРО
# ==========================================

def save_semantic_core(conn):
    c = conn.cursor()
    c.execute('''
        SELECT t.id, t.lang, t.primary_kw, t.category, t.tier,
               t.total_searches, t.total_value, t.status, t.article_slug
        FROM topics t
        ORDER BY t.total_value DESC, t.lang
    ''')
    rows = c.fetchall()

    # Сводная таблица покрытия по языкам для каждого cluster_id
    coverage = {}
    for row in rows:
        cid, lang = row[0], row[1]
        if cid not in coverage:
            coverage[cid] = {
                'primary_kw': row[2], 'category': row[3], 'tier': row[4],
                'total_searches': 0, 'total_value': 0,
                'en':'❌','de':'❌','nl':'❌','sv':'❌'
            }
        coverage[cid]['total_searches'] = max(coverage[cid]['total_searches'], row[5] or 0)
        coverage[cid]['total_value'] += row[6] or 0
        status_icon = '✅' if row[7] == 'done' else '⏳'
        coverage[cid][lang] = status_icon

    with open(REPORT_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cluster_id','primary_kw','category','tier',
                         'searches','value_usd','EN','DE','NL','SV'])
        for cid, d in sorted(coverage.items(), key=lambda x: -x[1]['total_value']):
            writer.writerow([
                cid, d['primary_kw'], d['category'], d['tier'],
                d['total_searches'], f"${d['total_value']:,.0f}",
                d['en'], d['de'], d['nl'], d['sv']
            ])

    print(f'📊 Семантическое ядро сохранено: {REPORT_PATH.name} ({len(coverage)} тем)')


# ==========================================
# MAIN
# ==========================================

def main():
    apply_flag  = '--apply'  in sys.argv
    report_flag = '--report' in sys.argv
    lang_args   = [a for a in sys.argv[1:] if not a.startswith('--')]
    lang        = lang_args[0].lower() if lang_args else None

    if not lang or lang not in SUPPORTED_LANGS:
        print('Укажи язык: py -3.11 scripts/smart_cluster.py en [--apply] [--report]')
        print(f'Доступные: {", ".join(SUPPORTED_LANGS)}')
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Берём только некластеризованные pending-ключевики
    c.execute('''
        SELECT keyword, avg_searches, cpc_high
        FROM keywords
        WHERE lang=? AND status="pending" AND topic_id IS NULL
        ORDER BY (avg_searches * cpc_high) DESC
    ''', (lang,))
    rows = c.fetchall()

    if not rows:
        print(f'Нет некластеризованных pending-ключевиков для {lang.upper()}')
        if report_flag:
            save_semantic_core(conn)
        conn.close()
        return

    print(f'🔍 Кластеризуем {len(rows)} ключевиков [{lang.upper()}] через Gemini...')
    if not apply_flag:
        print('   (DRY-RUN — передай --apply чтобы сохранить в БД)')

    total_batches = (len(rows) - 1) // BATCH_SIZE + 1
    all_clusters = []
    all_invalid  = []

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f'   Батч {batch_num}/{total_batches} ({len(batch)} ключевиков)...')

        try:
            result = cluster_batch(batch, lang)
            clusters = result.get('clusters', [])
            invalid  = result.get('invalid', [])
            all_clusters.extend(clusters)
            all_invalid.extend(invalid)
            print(f'      → {len(clusters)} кластеров, {len(invalid)} невалидных')
        except TimeoutError as e:
            print(f'      ⏱️  Таймаут: {e} — пропускаем батч')
        except Exception as e:
            print(f'      ⚠️  Ошибка: {e} — пропускаем батч')

        time.sleep(1.5)

    # Итоги
    print(f'\n📋 Итого: {len(all_clusters)} кластеров | {len(all_invalid)} невалидных')

    # Превью топ-10 кластеров
    print('\nТоп-10 кластеров по ценности:')
    cluster_vals = []
    kw_map = {row[0].lower(): (row[1], row[2]) for row in rows}
    for cl in all_clusters:
        all_kws_in_cl = (
            [cl.get('primary_kw','')] +
            cl.get('secondary',[]) +
            cl.get('faq',[]) +
            cl.get('longtail',[])
        )
        val = sum((kw_map.get(kw.lower(),(0,0))[0] or 0) *
                  (kw_map.get(kw.lower(),(0,0))[1] or 0)
                  for kw in all_kws_in_cl)
        cluster_vals.append((cl['cluster_id'], cl.get('primary_kw',''), val,
                              len(all_kws_in_cl), cl.get('category','')))

    for cid, pkw, val, count, cat in sorted(cluster_vals, key=lambda x: -x[2])[:10]:
        tier = tier_from_value(val)
        print(f'  [{tier}] {cid:35} | ${val:>8,.0f} | {count:2} kw | {cat}')
        print(f'       primary: "{pkw}"')

    if apply_flag:
        topics_n, roles_n, inv_n = apply_clusters(all_clusters, all_invalid, lang, conn)
        conn.commit()
        print(f'\n✅ Применено: {topics_n} тем | {roles_n} ролей | {inv_n} невалидных помечено')
        if report_flag:
            save_semantic_core(conn)
    else:
        print(f'\n👀 DRY-RUN — запусти с --apply чтобы сохранить.')
        print(f'   py -3.11 scripts/smart_cluster.py {lang} --apply')
        if report_flag:
            print('   (--report работает только с --apply)')

    conn.close()


if __name__ == '__main__':
    main()
