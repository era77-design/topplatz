import shutil
import os
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env')

SCRIPTS_DIR = Path(os.getenv('SCRIPTS_DIR', 'C:/Users/DDR/topplatz-scripts'))
NEXTJS_DIR  = Path(os.getenv('NEXTJS_DIR',  'C:/Users/DDR/topplatz'))
CONTENT_SRC = SCRIPTS_DIR / 'content'
CONTENT_DST = NEXTJS_DIR  / 'content'
META_FILE   = NEXTJS_DIR  / 'data' / 'articles-meta.json'
DB_PATH     = SCRIPTS_DIR / os.getenv('DB_PATH', 'keywords.db')

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
    except:
        pass
    return data

def publish():
    if not CONTENT_SRC.exists():
        print(f'❌ Папка не найдена: {CONTENT_SRC}')
        return 0

    copied = skipped = 0
    articles_by_lang = {'en': [], 'de': [], 'nl': [], 'sv': []}

    for lang_dir in sorted(CONTENT_SRC.iterdir()):
        if not lang_dir.is_dir():
            continue
        lang = lang_dir.name
        if lang not in articles_by_lang:
            continue

        dst_dir = CONTENT_DST / lang
        dst_dir.mkdir(parents=True, exist_ok=True)
        mdx_files = sorted(lang_dir.glob('*.mdx'), key=lambda f: f.stat().st_mtime, reverse=True)
        print(f'\n📂 [{lang.upper()}] {len(mdx_files)} файлов')

        for mdx_file in mdx_files:
            dst_file = dst_dir / mdx_file.name

            if not dst_file.exists() or mdx_file.stat().st_mtime > dst_file.stat().st_mtime:
                shutil.copy2(mdx_file, dst_file)
                print(f'   ✅ {mdx_file.name}')
                copied += 1
            else:
                skipped += 1

            fm = parse_frontmatter(mdx_file)
            slug = mdx_file.stem
            if fm:
                category = fm.get('category') or detect_category(fm.get('keyword', ''), slug)
                articles_by_lang[lang].append({
                    'slug':        slug,
                    'title':       fm.get('title', slug),
                    'description': fm.get('description', ''),
                    'photoUrl':    fm.get('photoUrl', ''),
                    'photoAlt':    fm.get('photoAlt', ''),
                    'photoAuthor': fm.get('photoAuthor', ''),
                    'photoUnsplash': fm.get('photoUnsplash', ''),
                    'category':    category,
                    'timeMinutes': int(fm.get('timeMinutes', 15) or 15),
                    'difficulty':  fm.get('difficulty', 'Easy'),
                    'createdAt':   fm.get('createdAt', ''),
                    'keyword':     fm.get('keyword', ''),
                })

    print(f'\n📊 Скопировано: {copied} | Без изменений: {skipped}')

    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles_by_lang, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in articles_by_lang.values())
    print(f'📋 JSON индекс: {total} статей → {META_FILE}')
    return copied

def git_push(copied):
    print(f'\n🚀 Пушим изменения...')
    os.chdir(NEXTJS_DIR)
    os.system('git add content/ data/articles-meta.json')
    os.system(f'git commit -m "add {copied} new articles, update index"')
    os.system('git push')
    print('✅ Готово! Cloudflare деплоит автоматически')

def show_stats():
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print('\n📊 Статус:')
    for lang in ['en', 'de', 'nl', 'sv']:
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="done"', (lang,))
        done = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="pending"', (lang,))
        pending = c.fetchone()[0]
        print(f'   {lang.upper()}: ✅ {done} опубликовано | ⏳ {pending} в очереди')
    conn.close()

if __name__ == '__main__':
    print('📤 TopPlatz — Публикация статей')
    print('=' * 35)
    copied = publish()
    git_push(copied)
    show_stats()
