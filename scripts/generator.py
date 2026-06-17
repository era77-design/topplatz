from google import genai
from google.genai import types
import sqlite3
import json
import time
import re
import sys
import requests
import threading
import queue
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# ==========================================
# ПУТИ — всё относительно корня topplatz/
# (скрипт лежит в topplatz/scripts/, поэтому .parent.parent)
# ==========================================

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

GEMINI_API_KEY   = os.getenv('GEMINI_API_KEY')
UNSPLASH_KEY     = os.getenv('UNSPLASH_KEY')
DB_PATH          = ROOT / 'keywords.db'
CONTENT_DIR      = ROOT / 'content'
USED_PHOTOS_FILE = ROOT / 'data' / 'used-photos.json'
ARTICLES_PER_RUN = int(os.getenv('ARTICLES_PER_RUN', 5))
PHOTO_CANDIDATES = int(os.getenv('PHOTO_CANDIDATES', 5))

# ==========================================
# ЗАЩИТА ОТ ЗАВИСАНИЯ GEMINI API
# ==========================================
# Известный баг SDK google-genai: без явного таймаута запрос может
# зависнуть НАВСЕГДА при сетевом сбое (timeout=None передаётся внутрь
# httpx). HttpOptions(timeout=...) помогает, но не всегда срабатывает
# надёжно — поэтому здесь ещё и свой watchdog на отдельном потоке: если
# вызов не вернулся за N секунд, скрипт считает его проваленным и идёт
# дальше, вместо того чтобы зависнуть на час.

def call_with_timeout(fn, timeout_sec, *args, **kwargs):
    result_queue = queue.Queue()

    def target():
        try:
            result_queue.put(('ok', fn(*args, **kwargs)))
        except Exception as e:
            result_queue.put(('error', e))

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        raise TimeoutError(f'не вернулся за {timeout_sec} сек')

    status, value = result_queue.get()
    if status == 'error':
        raise value
    return value

# ==========================================
# ПРОВЕРКА КЛЮЧЕЙ
# ==========================================

def check_config():
    errors = []
    if not GEMINI_API_KEY or 'КЛЮЧ' in GEMINI_API_KEY:
        errors.append('❌ GEMINI_API_KEY не задан в .env')
    if not UNSPLASH_KEY or 'КЛЮЧ' in UNSPLASH_KEY:
        errors.append('❌ UNSPLASH_KEY не задан в .env')
    if errors:
        [print(e) for e in errors]
        exit(1)
    print(f'✅ Конфигурация загружена (ROOT: {ROOT})')

client = None
def init_client():
    global client
    client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# ТРЕКИНГ УЖЕ ИСПОЛЬЗОВАННЫХ ФОТО
# (переживает между запусками — data/used-photos.json)
# ==========================================

def load_used_photos():
    if USED_PHOTOS_FILE.exists():
        try:
            return set(json.loads(USED_PHOTOS_FILE.read_text(encoding='utf-8')))
        except Exception:
            return set()
    return set()

def save_used_photos(used_ids):
    USED_PHOTOS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USED_PHOTOS_FILE.write_text(
        json.dumps(sorted(used_ids), ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

# ==========================================
# GEMINI VISION — оценка релевантности фото
# ==========================================

def score_photo_relevance(image_bytes, keyword):
    """Просит Gemini оценить 1-10, насколько фото подходит к теме статьи."""
    try:
        response = call_with_timeout(
            client.models.generate_content,
            25,  # сек — это быстрый вызов, 25 сек более чем достаточно
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                f'You are picking a header photo for a how-to article about '
                f'"{keyword}". On a scale of 1-10, rate how SUITABLE this image '
                f'is as that header photo. A generic but topically-related stock '
                f'photo (showing the right object, setting, or activity) should '
                f'score 6-8. Reserve 9-10 for an excellent, specific match. '
                f'Only score below 4 if the image is about something clearly '
                f'unrelated to the topic. '
                f'Reply with ONLY a single integer from 1 to 10, nothing else.'
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=50,
                thinking_config=types.ThinkingConfig(thinking_budget=256),
                http_options=types.HttpOptions(timeout=20000)
            )
        )
        text = response.text
        if not text:
            return 5
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 5
    except TimeoutError as e:
        print(f'      ⏱️  Vision таймаут ({e}) — нейтральный балл')
        return 5
    except Exception as e:
        print(f'      ⚠️  Vision: {e}')
        return 5  # нейтральный балл при ошибке — не блокирует выбор

# ==========================================
# UNSPLASH — подбор фото с проверкой релевантности
# ==========================================

def get_photo(query, keyword, used_photo_ids):
    try:
        resp = requests.get(
            'https://api.unsplash.com/search/photos',
            params={'query': query, 'per_page': PHOTO_CANDIDATES, 'orientation': 'landscape', 'content_filter': 'high'},
            headers={'Authorization': f'Client-ID {UNSPLASH_KEY}'},
            timeout=10
        )
        results = resp.json().get('results', [])
        if not results:
            return None

        if len(results) == 1:
            best = results[0]
        else:
            scored = []
            for photo in results:
                try:
                    img_bytes = requests.get(photo['urls']['small'], timeout=10).content
                    score = score_photo_relevance(img_bytes, keyword)
                except Exception:
                    score = 5
                scored.append((score, photo))
                time.sleep(0.5)

            scored.sort(key=lambda x: -x[0])

            # Предпочитаем фото, которые ещё не использовались в других статьях,
            # даже если их оценка релевантности немного ниже
            unused = [s for s in scored if s[1]['id'] not in used_photo_ids]
            chosen = unused if unused else scored

            best_score, best = chosen[0]
            scores_str = ', '.join(str(s) for s, _ in scored)
            note = '' if unused else ' (все уже использованы — берём лучший повтор)'
            print(f'      🎯 Релевантность: [{scores_str}] → выбрано {best_score}/10{note}')

        used_photo_ids.add(best['id'])

        return {
            'url':          best['urls']['regular'],
            'url_small':    best['urls']['small'],
            'alt':          best.get('alt_description') or query,
            'author_name':  best['user']['name'],
            'author_url':   best['user']['links']['html'],
            'unsplash_url': best['links']['html'],
        }
    except Exception as e:
        print(f'  ⚠️  Unsplash: {e}')
        return None

# ==========================================
# ПРОМПТ
# ==========================================

def build_prompt(keyword, lang, related_phrases=None):
    lang_names = {'en': 'English', 'de': 'German', 'nl': 'Dutch', 'sv': 'Swedish'}
    lang_name = lang_names.get(lang, 'English')

    related_section = ''
    if related_phrases:
        phrases_list = '\n'.join(f'- "{p}"' for p in related_phrases[:8])
        related_section = f"""
People also search for this same topic using these phrasings:
{phrases_list}

Naturally work 2-4 of these (verbatim or near-verbatim) in as FAQ questions,
so the article matches multiple ways people ask this. Don't force all of them —
only the ones that make sense as genuine, distinct questions.
"""

    return f"""You are an expert how-to content writer.

Keyword: "{keyword}"
Language: {lang_name}
{related_section}
RULES:
- Write ONLY in {lang_name}
- Be practical and safe
- NO dangerous, harmful or illegal content
- NO specific medical dosages or diagnoses
- NO financial advice

Return ONLY valid JSON, no markdown, no backticks:

{{
  "title": "SEO title with keyword max 60 chars",
  "description": "Meta description 120-155 chars",
  "slug": "url-slug-with-hyphens",
  "photo_query": "2-3 word English search query for relevant photo",
  "intro": "2-3 sentence answer for featured snippet",
  "difficulty": "Easy",
  "time_minutes": 15,
  "what_you_need": ["item1", "item2"],
  "steps": [{{"title": "Step title", "text": "3-5 sentence explanation", "tip": "optional tip"}}],
  "tips": ["tip1", "tip2", "tip3"],
  "warnings": ["warning if relevant"],
  "faq": [{{"q": "Question?", "a": "Answer 2-3 sentences."}}]
}}

Write 5-7 steps and 5-7 FAQ questions."""

# ==========================================
# ПОЧИНКА JSON
# ==========================================

def fix_json(text):
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    if not text.endswith('}'):
        for i in range(len(text)-1, 0, -1):
            if text[i] in ('}', ']'):
                text = text[:i+1]
                break
        text += ']' * max(0, text.count('[') - text.count(']'))
        text += '}' * max(0, text.count('{') - text.count('}'))
    return text

# ==========================================
# ГЕНЕРАЦИЯ СТАТЬИ
# ==========================================

def generate_article(keyword, lang, related_phrases=None):
    try:
        response = call_with_timeout(
            client.models.generate_content,
            90,  # сек — этот вызов сложнее и дольше, даём больше запаса
            model='gemini-2.5-flash',
            contents=build_prompt(keyword, lang, related_phrases),
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,
                http_options=types.HttpOptions(timeout=60000)
            )
        )
        return json.loads(fix_json(response.text.strip()))
    except TimeoutError as e:
        print(f'  ⏱️  Таймаут генерации ({e})')
        return None
    except json.JSONDecodeError as e:
        print(f'  ⚠️  JSON ошибка: {e}')
        return None
    except Exception as e:
        print(f'  ⚠️  API ошибка: {e}')
        return None

# ==========================================
# СОХРАНЕНИЕ В MDX — прямо в topplatz/content/
# ==========================================

def save_as_mdx(article, keyword, lang, slug, photo):
    lang_dir = CONTENT_DIR / lang
    lang_dir.mkdir(parents=True, exist_ok=True)
    filepath = lang_dir / f'{slug}.mdx'

    photo_md = ''
    if photo:
        photo_md = f"\n![{photo['alt']}]({photo['url']})\n*Photo by [{photo['author_name']}]({photo['author_url']}) on [Unsplash]({photo['unsplash_url']})*\n"

    steps_md = ''
    for i, step in enumerate(article.get('steps', []), 1):
        steps_md += f'\n### Step {i}: {step["title"]}\n\n{step["text"]}\n'
        if step.get('tip'):
            steps_md += f'\n> 💡 **Tip:** {step["tip"]}\n'

    faq_md = ''.join([f'\n**{item["q"]}**\n\n{item["a"]}\n' for item in article.get('faq', [])])
    tips_md     = '\n'.join([f'- {t}' for t in article.get('tips', [])])
    warnings_md = '\n'.join([f'- ⚠️ {w}' for w in article.get('warnings', [])])
    needs_md    = '\n'.join([f'- {n}' for n in article.get('what_you_need', [])])

    photo_meta = ''
    if photo:
        photo_meta = f'photoUrl: "{photo["url_small"]}"\nphotoAlt: "{photo["alt"]}"\nphotoAuthor: "{photo["author_name"]}"\nphotoUnsplash: "{photo["unsplash_url"]}"'

    content = f"""---
title: "{article['title']}"
description: "{article['description']}"
keyword: "{keyword}"
lang: "{lang}"
slug: "{slug}"
difficulty: "{article.get('difficulty', 'Easy')}"
timeMinutes: {article.get('time_minutes', 15)}
createdAt: "{datetime.now().strftime('%Y-%m-%d')}"
{photo_meta}
---

{photo_md}

{article['intro']}

## What You Need

{needs_md}

## Steps
{steps_md}

## Tips & Tricks

{tips_md}

{'## Warnings' + chr(10) + chr(10) + warnings_md if warnings_md.strip() else ''}

## Frequently Asked Questions
{faq_md}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return str(filepath.relative_to(ROOT))

# ==========================================
# БД ФУНКЦИИ
# ==========================================

def update_status(keyword, lang, status):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('UPDATE keywords SET status=? WHERE keyword=? AND lang=?', (status, keyword, lang))
    conn.commit()
    conn.close()

def get_pending_keywords(lang=None, limit=5):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("PRAGMA table_info(keywords)")
    has_related = any(row[1] == 'related_phrases' for row in c.fetchall())
    cols = 'keyword, lang, avg_searches, cpc_high' + (', related_phrases' if has_related else '')

    if lang:
        c.execute(f'SELECT {cols} FROM keywords WHERE status="pending" AND lang=? ORDER BY avg_searches DESC LIMIT ?', (lang, limit))
    else:
        c.execute(f'SELECT {cols} FROM keywords WHERE status="pending" ORDER BY avg_searches DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()

    if not has_related:
        rows = [r + (None,) for r in rows]
    return rows

# ==========================================
# ОСНОВНОЙ ЗАПУСК
# ==========================================

def run_generator(lang=None, limit=None):
    limit = limit or ARTICLES_PER_RUN
    keywords = get_pending_keywords(lang=lang, limit=limit)
    if not keywords:
        print('✅ Нет ключевиков для генерации')
        return

    used_photo_ids = load_used_photos()
    print(f'\n🚀 Генерируем {len(keywords)} статей... (известно {len(used_photo_ids)} использованных фото)\n')

    success = errors = 0
    for keyword, kw_lang, searches, cpc, related_json in keywords:
        print(f'📝 [{kw_lang.upper()}] "{keyword}"')
        print(f'   Поисков: {searches:,} | CPC: ${cpc:.2f}')
        related_phrases = json.loads(related_json) if related_json else []
        if related_phrases:
            print(f'   🔗 +{len(related_phrases)} похожих формулировок → войдут в FAQ')
        article = generate_article(keyword, kw_lang, related_phrases)
        if article:
            photo_query = article.get('photo_query', keyword)
            print(f'   🖼️  Фото: "{photo_query}"')
            photo = get_photo(photo_query, keyword, used_photo_ids)
            print(f'   📸 {photo["author_name"] if photo else "не найдено"}')
            slug = re.sub(r'[^a-z0-9\-]', '', article.get('slug', keyword.lower().replace(' ', '-')))[:60]
            filepath = save_as_mdx(article, keyword, kw_lang, slug, photo)
            update_status(keyword, kw_lang, 'done')
            print(f'   ✅ {filepath}')
            success += 1
        else:
            update_status(keyword, kw_lang, 'error')
            print(f'   ❌ Ошибка')
            errors += 1
        save_used_photos(used_photo_ids)
        time.sleep(2)
    print(f'\n🎉 Успешно: {success} | Ошибки: {errors}')

# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == '__main__':
    SUPPORTED_LANGS = ('en', 'de', 'nl', 'sv')
    lang_arg = sys.argv[1].lower() if len(sys.argv) > 1 else 'en'
    if lang_arg not in SUPPORTED_LANGS:
        print(f'⚠️  Неизвестный язык "{lang_arg}", поддерживаются: {", ".join(SUPPORTED_LANGS)}. Использую en.')
        lang_arg = 'en'

    print('🤖 TopPlatz — Генератор контента (Gemini + Unsplash + Vision)')
    print(f'   Язык: {lang_arg.upper()}')
    print('=' * 60)
    check_config()
    init_client()
    run_generator(lang=lang_arg, limit=ARTICLES_PER_RUN)
