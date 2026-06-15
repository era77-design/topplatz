from google import genai
from google.genai import types
import sqlite3
import json
import time
import re
import requests
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
ARTICLES_PER_RUN = int(os.getenv('ARTICLES_PER_RUN', 5))

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
# UNSPLASH — подбор фото
# ==========================================

def get_photo(query):
    try:
        resp = requests.get(
            'https://api.unsplash.com/search/photos',
            params={'query': query, 'per_page': 1, 'orientation': 'landscape', 'content_filter': 'high'},
            headers={'Authorization': f'Client-ID {UNSPLASH_KEY}'},
            timeout=10
        )
        results = resp.json().get('results', [])
        if not results:
            return None
        photo = results[0]
        return {
            'url':          photo['urls']['regular'],
            'url_small':    photo['urls']['small'],
            'alt':          photo.get('alt_description') or query,
            'author_name':  photo['user']['name'],
            'author_url':   photo['user']['links']['html'],
            'unsplash_url': photo['links']['html'],
        }
    except Exception as e:
        print(f'  ⚠️  Unsplash: {e}')
        return None

# ==========================================
# ПРОМПТ
# ==========================================

def build_prompt(keyword, lang):
    lang_names = {'en': 'English', 'de': 'German', 'nl': 'Dutch', 'sv': 'Swedish'}
    lang_name = lang_names.get(lang, 'English')
    return f"""You are an expert how-to content writer.

Keyword: "{keyword}"
Language: {lang_name}

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

def generate_article(keyword, lang):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=build_prompt(keyword, lang),
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)
        )
        return json.loads(fix_json(response.text.strip()))
    except json.JSONDecodeError as e:
        print(f'  ⚠️  JSON ошибка: {e}')
        return None
    except Exception as e:
        print(f'  ⚠️  API ошибка: {e}')
        return None

# ==========================================
# СОХРАНЕНИЕ В MDX — теперь прямо в topplatz/content/
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
    if lang:
        c.execute('SELECT keyword, lang, avg_searches, cpc_high FROM keywords WHERE status="pending" AND lang=? ORDER BY avg_searches DESC LIMIT ?', (lang, limit))
    else:
        c.execute('SELECT keyword, lang, avg_searches, cpc_high FROM keywords WHERE status="pending" ORDER BY avg_searches DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
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
    print(f'\n🚀 Генерируем {len(keywords)} статей...\n')
    success = errors = 0
    for keyword, kw_lang, searches, cpc in keywords:
        print(f'📝 [{kw_lang.upper()}] "{keyword}"')
        print(f'   Поисков: {searches:,} | CPC: ${cpc:.2f}')
        article = generate_article(keyword, kw_lang)
        if article:
            photo_query = article.get('photo_query', keyword)
            print(f'   🖼️  Фото: "{photo_query}"')
            photo = get_photo(photo_query)
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
        time.sleep(2)
    print(f'\n🎉 Успешно: {success} | Ошибки: {errors}')

# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == '__main__':
    print('🤖 TopPlatz — Генератор контента (Gemini + Unsplash)')
    print('=' * 52)
    check_config()
    init_client()
    run_generator(lang='en', limit=ARTICLES_PER_RUN)
