import os
import json
import sqlite3
from pathlib import Path

# ==========================================
# ПУТИ — всё относительно корня topplatz/
# (скрипт лежит в topplatz/scripts/, поэтому .parent.parent)
# ==========================================

ROOT        = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / 'content'
META_FILE   = ROOT / 'data' / 'articles-meta.json'
DB_PATH     = ROOT / 'keywords.db'

LANGS = ['en', 'de', 'nl', 'sv']

# ==========================================
# КАТЕГОРИЗАЦИЯ
# ==========================================

def detect_category(keyword='', slug=''):
    text = f'{keyword} {slug}'.lower()
    if any(w in text for w in ['clean','fix','repair','build','grow','garden','home','house','door','pipe','leak','wobbly','wood','paint','bed bug','pest','lawn','plant']):
        return 'home-garden'
    if any(w in text for w in ['cook','recipe','food','kitchen','bake','meal','dish','ingredient','eat','drink','coffee','tea','sauce']):
        return 'kitchen-food'
    if any(w in text for w in ['install','tech','computer','phone','wifi','software','app','delete','account','facebook','instagram','chrome','node','windows','mac','android','ios','internet']):
        return 'tech-devices'
    if any(w in text for w in ['craft','diy','sew','knit','crochet','origami','candle','jewelry','decor']):
        return 'diy-crafts'
    return 'general'

# ==========================================
# ПАРСЕР FRONTMATTER
# ==========================================

def parse_frontmatter(filepath):
    data = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.startswith('---'):
            return data
        end = content.find('---', 3)
        if end == -1:
            return data
        fm = content[3:end]
        for line in fm.strip().split('\n'):
            if ':' in line:
                key, _, val = line.partition(':')
                data[key.strip()] = val.strip().strip('"').strip("'")
    except Exception:
        pass
    return data

# ==========================================
# СБОРКА data/articles-meta.json
# ==========================================

def build_index():
    articles_by_lang = {lang: [] for lang in LANGS}

    for lang in LANGS:
        lang_dir = CONTENT_DIR / lang
        if not lang_dir.exists():
            continue

        mdx_files = sorted(lang_dir.glob('*.mdx'), key=lambda f: f.stat().st_mtime, reverse=True)
        for mdx_file in mdx_files:
            fm = parse_frontmatter(mdx_file)
            if not fm:
                continue
            slug = mdx_file.stem
            category = fm.get('category') or detect_category(fm.get('keyword', ''), slug)
            articles_by_lang[lang].append({
                'slug':          slug,
                'title':         fm.get('title', slug),
                'description':   fm.get('description', ''),
                'photoUrl':      fm.get('photoUrl', ''),
                'photoAlt':      fm.get('photoAlt', ''),
                'photoAuthor':   fm.get('photoAuthor', ''),
                'photoUnsplash': fm.get('photoUnsplash', ''),
                'category':      category,
                'timeMinutes':   int(fm.get('timeMinutes', 15) or 15),
                'difficulty':    fm.get('difficulty', 'Easy'),
                'createdAt':     fm.get('createdAt', ''),
                'keyword':       fm.get('keyword', ''),
            })

        print(f'   [{lang.upper()}] {len(articles_by_lang[lang])} статей')

    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles_by_lang, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in articles_by_lang.values())
    print(f'\n📋 Индекс обновлён: {total} статей → data/articles-meta.json')
    return total

# ==========================================
# GIT PUSH
# ==========================================

def git_push(total):
    print('\n🚀 Пушим изменения...')
    os.chdir(ROOT)
    os.system('git add content/ data/articles-meta.json')
    os.system(f'git commit -m "publish: {total} articles in index"')
    os.system('git push')
    print('✅ Готово! Cloudflare деплоит автоматически')

# ==========================================
# СТАТИСТИКА ПО КЛЮЧЕВИКАМ
# ==========================================

def show_stats():
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    print('\n📊 Статус по ключевикам:')
    for lang in LANGS:
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="done"', (lang,))
        done = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="pending"', (lang,))
        pending = c.fetchone()[0]
        print(f'   {lang.upper()}: ✅ {done} опубликовано | ⏳ {pending} в очереди')
    conn.close()

# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == '__main__':
    print('📤 TopPlatz — Публикация')
    print('=' * 35)
    print(f'ROOT: {ROOT}\n')
    total = build_index()
    git_push(total)
    show_stats()
