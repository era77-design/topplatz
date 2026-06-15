import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv('.env')
DB_PATH = os.getenv('DB_PATH', 'keywords.db')

CSV_FILES = {
    'en': 'Keyword Stats 2026-06-12 at 07_41_27.csv',
    'de': 'Keyword Stats 2026-06-12 at 07_43_09.csv',
    'nl': 'Keyword Stats 2026-06-12 at 07_44_47.csv',
    'sv': 'Keyword Stats 2026-06-12 at 07_45_55.csv',
}

STOP_WORDS = [
    'weapon', 'gun', 'bomb', 'explosive', 'shoot', 'kill',
    'drug', 'weed', 'cocaine', 'meth', 'heroin',
    'overdose', 'suicide', 'self harm', 'self-harm',
    'hack', 'crack', 'steal', 'fraud', 'scam',
    'porn', 'sex', 'nude', 'adult', 'xxx',
    'gambling', 'casino', 'poker cheat', 'extremist', 'terrorist',
    'waffe', 'bombe', 'drogen', 'selbstmord',
    'wapen', 'bom', 'zelfmoord', 'vapen', 'droger', 'självmord',
]

def is_safe(keyword):
    kw_lower = str(keyword).lower()
    return not any(stop.lower() in kw_lower for stop in STOP_WORDS)

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
            source TEXT DEFAULT 'keyword_planner',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(keyword, lang)
        )
    ''')
    conn.commit()
    conn.close()
    print('✅ База данных инициализирована')

def parse_cpc(value):
    if pd.isna(value):
        return 0.0
    try:
        return float(str(value).replace(',', '.').replace(' ', ''))
    except:
        return 0.0

def import_csv(lang, filepath):
    if not os.path.exists(filepath):
        print(f'  ⚠️  Файл не найден: {filepath}')
        return 0, 0
    df = pd.read_csv(filepath, sep='\t', encoding='utf-16', skiprows=2)
    df.columns = [c.strip() for c in df.columns]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = skipped = 0
    for _, row in df.iterrows():
        keyword = str(row.get('Keyword', '')).strip()
        if not keyword or keyword == 'nan':
            continue
        if not is_safe(keyword):
            skipped += 1
            continue
        try:
            avg_searches = 0
            try:
                avg_searches = int(float(str(row.get('Avg. monthly searches', 0)).replace(',', '.').replace(' ', '')))
            except:
                avg_searches = 0
            competition = str(row.get('Competition', 'Unknown'))
            cpc_low  = parse_cpc(row.get('Top of page bid (low range)', 0))
            cpc_high = parse_cpc(row.get('Top of page bid (high range)', 0))
            c.execute('''
                INSERT OR IGNORE INTO keywords
                (keyword, lang, avg_searches, competition, cpc_low, cpc_high)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (keyword, lang, avg_searches, competition, cpc_low, cpc_high))
            if c.rowcount > 0:
                saved += 1
        except Exception as e:
            print(f'  ⚠️  Ошибка: {e}')
    conn.commit()
    conn.close()
    return saved, skipped

def show_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print('\n📊 Статистика:')
    for lang in ['en', 'de', 'nl', 'sv']:
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND avg_searches > 0', (lang,))
        total = c.fetchone()[0]
        c.execute('SELECT AVG(cpc_high) FROM keywords WHERE lang=? AND cpc_high > 0', (lang,))
        avg_cpc = c.fetchone()[0] or 0
        print(f'  {lang.upper()}: {total} ключевиков | avg CPC: ${avg_cpc:.2f}')
    print('\n💰 Топ 5 по CPC (EN):')
    c.execute('''SELECT keyword, avg_searches, cpc_high FROM keywords
                 WHERE lang="en" AND cpc_high > 0
                 ORDER BY cpc_high DESC LIMIT 5''')
    for kw, s, cpc in c.fetchall():
        print(f'  ${cpc:>8.2f} | {s:>8,} | {kw}')
    conn.close()

if __name__ == '__main__':
    print('🚀 TopPlatz — Импорт ключевиков из Google Keyword Planner')
    print('=' * 55)
    init_db()
    total_saved = total_skipped = 0
    for lang, filename in CSV_FILES.items():
        print(f'\n📥 Импорт {lang.upper()}: {filename}')
        saved, skipped = import_csv(lang, filename)
        total_saved += saved
        total_skipped += skipped
        print(f'   ✅ Сохранено: {saved} | 🚫 Отфильтровано: {skipped}')
    print(f'\n🎉 Итого: {total_saved} сохранено, {total_skipped} отфильтровано')
    show_stats()
