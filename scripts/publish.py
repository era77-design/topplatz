import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# ==========================================
# ПУТИ — всё относительно корня topplatz/
# ==========================================

ROOT        = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / 'content'
META_FILE   = ROOT / 'data' / 'articles-meta.json'
DB_PATH     = ROOT / 'keywords.db'
SITEMAP     = ROOT / 'public' / 'sitemap.xml'

LANGS  = ['en', 'de', 'nl', 'sv']
DOMAIN = 'https://topplatz.com'

CATEGORIES = ['home-garden', 'kitchen-food', 'tech-devices', 'diy-crafts', 'general']

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
    return articles_by_lang, total

# ==========================================
# ГЕНЕРАЦИЯ sitemap.xml
# ==========================================

def build_sitemap(articles_by_lang):
    today = datetime.now().strftime('%Y-%m-%d')
    urls = []

    def add(loc, lastmod, changefreq, priority):
        urls.append(
            f'  <url>\n'
            f'    <loc>{DOMAIN}{loc}</loc>\n'
            f'    <lastmod>{lastmod}</lastmod>\n'
            f'    <changefreq>{changefreq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            f'  </url>'
        )

    for lang in LANGS:
        articles = articles_by_lang.get(lang, [])

        # Главная
        add(f'/{lang}', today, 'daily', '1.0')

        # Статические страницы
        for page, prio in [('about', '0.3'), ('contact', '0.3'), ('privacy', '0.2')]:
            add(f'/{lang}/{page}', today, 'monthly', prio)

        # Категории — только если есть статьи
        if articles:
            add(f'/{lang}/categories', today, 'weekly', '0.5')
            present_cats = {a['category'] for a in articles}
            for cat in CATEGORIES:
                if cat in present_cats:
                    add(f'/{lang}/category/{cat}', today, 'weekly', '0.6')

        # Статьи
        for a in articles:
            lastmod = a.get('createdAt') or today
            add(f'/{lang}/{a["slug"]}', lastmod, 'monthly', '0.8')

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>\n'
    )

    SITEMAP.parent.mkdir(parents=True, exist_ok=True)
    with open(SITEMAP, 'w', encoding='utf-8') as f:
        f.write(xml)

    print(f'🗺️  Sitemap: {len(urls)} URL → public/sitemap.xml')

# ==========================================
# GIT PUSH
# ==========================================

def git_push(total):
    print('\n🚀 Пушим изменения...')
    os.chdir(ROOT)
    os.system('git add content/ data/articles-meta.json data/used-photos.json public/sitemap.xml')
    os.system(f'git commit -m "publish: {total} articles, update sitemap"')
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
    articles_by_lang, total = build_index()
    build_sitemap(articles_by_lang)
    git_push(total)
    show_stats()
