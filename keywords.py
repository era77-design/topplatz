import requests
import sqlite3
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv('.env')
DB_PATH = os.getenv('DB_PATH', 'keywords.db')

SEED_KEYWORDS = {
    'en': [
        'how to fix', 'how to make', 'how to clean', 'how to grow',
        'how to remove', 'how to install', 'how to cook', 'how to repair',
        'how to build', 'how to save', 'how to stop', 'how to start',
    ],
    'de': [
        'wie man', 'wie kann ich', 'wie funktioniert', 'anleitung',
        'schritt für schritt', 'wie entfernt man', 'wie kocht man',
        'wie repariert man', 'wie baut man', 'wie reinigt man',
    ],
    'nl': [
        'hoe maak je', 'hoe verwijder je', 'hoe repareer je',
        'hoe kook je', 'hoe bouw je', 'hoe reinig je',
        'hoe installeer je', 'hoe groei je', 'hoe stop je',
    ],
    'sv': [
        'hur man', 'hur gör man', 'hur lagar man', 'hur tar man bort',
        'hur bygger man', 'hur rengör man', 'hur installerar man',
        'hur odlar man', 'hur sparar man',
    ],
}

STOP_WORDS = [
    'weapon', 'gun', 'bomb', 'explosive', 'shoot', 'kill',
    'drug', 'weed', 'cocaine', 'meth', 'heroin',
    'overdose', 'suicide', 'self harm', 'self-harm',
    'hack', 'crack', 'steal', 'fraud', 'scam',
    'porn', 'sex', 'nude', 'adult', 'xxx',
    'gambling', 'casino', 'poker cheat',
    'extremist', 'terrorist',
    'waffe', 'bombe', 'drogen', 'selbstmord',
    'wapen', 'bom', 'zelfmoord',
    'vapen', 'droger', 'självmord',
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            lang TEXT NOT NULL,
            avg_searches INTEGER DEFAULT 0,
            competition TEXT DEFAULT 'Unknown',
            cpc_low REAL DEFAULT 0,
            cpc_high REAL DEFAULT 0,
            source TEXT DEFAULT 'google_suggest',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(keyword, lang)
        )
    ''')
    conn.commit()
    conn.close()
    print('✅ База данных инициализирована')

def is_safe(keyword):
    kw_lower = keyword.lower()
    for stop in STOP_WORDS:
        if stop.lower() in kw_lower:
            return False
    return True

def get_suggestions(query, lang='en'):
    lang_map = {
        'en': ('en', 'US'), 'de': ('de', 'DE'),
        'nl': ('nl', 'NL'), 'sv': ('sv', 'SE'),
    }
    hl, gl = lang_map.get(lang, ('en', 'US'))
    try:
        resp = requests.get(
            'https://suggestqueries.google.com/complete/search',
            params={'client': 'firefox', 'q': query, 'hl': hl, 'gl': gl},
            headers={'User-Agent': 'Mozilla/5.0 Firefox/120.0'},
            timeout=10
        )
        data = json.loads(resp.text)
        return [s for s in (data[1] if len(data) > 1 else []) if isinstance(s, str)]
    except Exception as e:
        print(f'  ⚠️  Ошибка для "{query}": {e}')
        return []

def save_keywords(keywords, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = skipped = 0
    for kw in keywords:
        if not is_safe(kw):
            skipped += 1
            continue
        try:
            c.execute('INSERT OR IGNORE INTO keywords (keyword, lang) VALUES (?, ?)', (kw.strip(), lang))
            if c.rowcount > 0:
                saved += 1
        except:
            pass
    conn.commit()
    conn.close()
    return saved, skipped

def collect_keywords(langs=None, limit=None):
    if langs is None:
        langs = ['en', 'de', 'nl', 'sv']
    total_saved = 0
    for lang in langs:
        seeds = SEED_KEYWORDS.get(lang, [])
        if limit:
            seeds = seeds[:limit]
        print(f'\n🌐 Язык: {lang.upper()} ({len(seeds)} запросов)')
        for seed in seeds:
            print(f'  🔍 "{seed}"')
            suggestions = get_suggestions(seed, lang)
            saved, skipped = save_keywords(suggestions, lang)
            total_saved += saved
            print(f'     ✅ {saved} | 🚫 {skipped}')
            time.sleep(1)
    print(f'\n🎉 Итого сохранено: {total_saved}')
    return total_saved

def show_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print('\n📊 Статистика:')
    for lang in ['en', 'de', 'nl', 'sv']:
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=?', (lang,))
        total = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="pending"', (lang,))
        pending = c.fetchone()[0]
        print(f'  {lang.upper()}: {total} всего | {pending} pending')
    conn.close()

if __name__ == '__main__':
    print('🚀 TopPlatz — Сборщик ключевиков')
    init_db()
    collect_keywords(langs=['en'], limit=3)
    show_stats()
