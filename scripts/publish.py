import os
import json
import re
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
# КАТЕГОРИЗАЦИЯ — EN/DE/NL/SV
# ==========================================
# ВАЖНО: сравнение по ЦЕЛЫМ СЛОВАМ (\b...\b), не по подстроке — иначе
# 'eat' находится внутри "create", 'mac' — внутри "machine", и т.п.
#
# Порядок проверки: сначала узкие/специфичные категории (tech, kitchen),
# потом home-garden — у неё самые общие слова ('fix','build'), и если
# проверять её первой, она "съедает" чужие темы.
#
# 'grow' и 'clean' (и их переводы) слишком неоднозначны сами по себе
# (рост человека vs растения; чистка чего угодно), поэтому для них
# требуется слово-напарник по теме рядом — иначе они не считаются.
#
# DE/NL/SV переводы — best-effort (не проверены носителем языка),
# покрывают основной словарь, но не претендуют на полноту. После первых
# сгенерированных статей стоит свериться глазами и подправить списки.
#
# Множественное число: для EN допускается окончание -s/-es (gnat/gnats).
# Для DE/NL/SV это НЕ включено — склонения там устроены сложнее простого
# суффикса (умляуты, классы склонения и т.п.), сравниваем только базовую
# форму слова. Известное ограничение v1.

def _has_word(text, word, lang='en'):
    if lang == 'en':
        # точное слово + опциональное -s/-es (gnat/gnats, pan/pans...)
        pattern = r'\b' + re.escape(word) + r'(e?s)?\b'
    else:
        # DE/NL/SV: сравниваем как ОСНОВУ (префикс) — компенсирует
        # спряжения/склонения (kochen->kocht, Kartoffel->Kartoffeln),
        # которые устроены сложнее простого английского -s. Левая \b
        # гарантирует совпадение только с НАЧАЛА слова (не подстрокой
        # внутри другого слова), а дальше разрешаем любое окончание.
        pattern = r'\b' + re.escape(word) + r'\w*'
    return re.search(pattern, text) is not None

def _has_any(text, words, lang='en'):
    return any(_has_word(text, w, lang) for w in words)

TECH_WORDS = {
    'en': ['install', 'tech', 'computer', 'phone', 'wifi', 'software', 'app',
           'delete', 'account', 'facebook', 'instagram', 'chrome', 'node',
           'windows', 'android', 'ios', 'internet', 'mac', 'gmail', 'email',
           'browser', 'password', 'tv', 'screen', 'laptop', 'tablet', 'router',
           'bluetooth', 'printer', 'telegram'],
    'de': ['konto', 'lösch', 'facebook', 'instagram', 'handy', 'computer',
           'telefon', 'wlan', 'software', 'app', 'chrome', 'windows', 'android',
           'internet', 'email', 'passwort', 'browser', 'drucker', 'gmail'],
    'nl': ['account', 'verwijder', 'facebook', 'instagram', 'telefoon',
           'computer', 'wifi', 'software', 'app', 'chrome', 'windows', 'android',
           'internet', 'email', 'wachtwoord', 'browser', 'printer', 'gmail'],
    'sv': ['konto', 'radera', 'facebook', 'instagram', 'telefon', 'dator',
           'wifi', 'programvara', 'app', 'chrome', 'windows', 'android',
           'internet', 'mejl', 'lösenord', 'webbläsare', 'skrivare', 'gmail'],
}

KITCHEN_WORDS = {
    'en': ['cook', 'recipe', 'food', 'kitchen', 'bake', 'meal', 'dish',
           'ingredient', 'eat', 'drink', 'coffee', 'tea', 'sauce',
           'dishwasher', 'microwave', 'oven', 'fridge', 'refrigerator',
           'pan', 'pot', 'stove', 'blender', 'toaster'],
    'de': ['koch', 'rezept', 'essen', 'küche', 'back', 'kaffee', 'tee',
           'geschirrspüler', 'mikrowelle', 'ofen', 'kühlschrank', 'pfanne', 'topf'],
    # 'koken'/'kook' и 'bakken'/'bak' нужны ОБА — нидерландское удвоение
    # гласной в открытом слоге (koken -> ik kook) ломает простое
    # префиксное совпадение в обе стороны
    'nl': ['koken', 'kook', 'recept', 'eten', 'keuken',
           'bakken', 'bak', 'koffie', 'thee',
           'vaatwasser', 'magnetron', 'oven', 'koelkast', 'pan'],
    'sv': ['laga', 'koka', 'recept', 'mat', 'kök', 'baka', 'kaffe', 'te',
           'diskmaskin', 'mikrovågsugn', 'ugn', 'kylskåp', 'panna'],
}

HOME_GARDEN_WORDS = {
    'en': ['garden', 'house', 'door', 'pipe', 'leak', 'wobbly', 'wood', 'paint',
           'bed bug', 'pest', 'lawn', 'plant', 'mold', 'mildew', 'flea', 'gnat',
           'tick', 'mosquito', 'mouse', 'mice', 'roach', 'cockroach', 'spider',
           'wasp', 'bee', 'rat', 'moth', 'termite', 'weed', 'gutter', 'roof',
           'fence', 'deck', 'patio', 'garage', 'fix', 'repair', 'build'],
    # 'reparier'/'bau' — основы глаголов (не полный инфинитив), чтобы
    # ловить и 'reparieren', и 'repariert'/'reparierst' одним совпадением
    'de': ['garten', 'haus', 'tür', 'rohr', 'leck', 'holz', 'farbe', 'mal',
           'schädling', 'rasen', 'pflanze', 'schimmel', 'floh', 'zecke',
           'maus', 'ratte', 'reparier', 'bau'],
    # 'repar'/'bouw' — то же самое для нидерландского
    'nl': ['tuin', 'huis', 'deur', 'lek', 'hout', 'verf', 'plaag', 'gazon',
           'plant', 'schimmel', 'vlo', 'teek', 'muis', 'repar', 'bouw'],
    # 'bygg' вместо 'bygga' — иначе не совпадает с 'bygger' (2-е спряжение
    # меняет окончание -a на -er, а не просто добавляет букву)
    'sv': ['trädgård', 'hus', 'dörr', 'läcka', 'trä', 'måla', 'färg',
           'skadedjur', 'gräsmatta', 'växt', 'mögel', 'loppa', 'fästing',
           'mus', 'reparera', 'bygg'],
}

GROW_COMPANIONS = {
    'en': ['seed', 'garden', 'vegetable', 'flower', 'tree', 'herb', 'potato',
           'avocado', 'tomato', 'grass', 'soil', 'indoor', 'outdoor'],
    'de': ['samen', 'garten', 'gemüse', 'blume', 'baum', 'kraut', 'kartoffel',
           'avocado', 'tomate', 'gras', 'erde'],
    'nl': ['zaad', 'tuin', 'groente', 'bloem', 'boom', 'kruid', 'aardappel',
           'avocado', 'tomaat', 'gras', 'grond'],
    'sv': ['frö', 'trädgård', 'grönsak', 'blomma', 'träd', 'ört', 'potatis',
           'avokado', 'tomat', 'gräs', 'jord'],
}

CLEAN_COMPANIONS = {
    'en': ['house', 'home', 'garage', 'gutter', 'window', 'carpet', 'floor',
           'wall', 'ceiling', 'yard', 'deck', 'patio'],
    'de': ['haus', 'garage', 'fenster', 'teppich', 'boden', 'wand', 'decke'],
    'nl': ['huis', 'garage', 'raam', 'tapijt', 'vloer', 'muur', 'plafond'],
    'sv': ['hus', 'garage', 'fönster', 'matta', 'golv', 'vägg', 'tak'],
}

DIY_WORDS = {
    'en': ['craft', 'diy', 'sew', 'knit', 'crochet', 'origami', 'candle',
           'jewelry', 'decor'],
    'de': ['bastel', 'näh', 'strick', 'kerze', 'schmuck', 'deko'],
    'nl': ['knutsel', 'naai', 'brei', 'kaars', 'sieraden', 'decoratie'],
    'sv': ['pyssel', 'sy', 'sticka', 'ljus', 'smycken', 'dekor'],
}

# 'grow'/'clean' и их переводы — отдельно от списков выше, т.к. требуют
# слова-напарника (см. комментарий в начале секции). Для DE/SV взяты
# основы глаголов короче инфинитива — 'wachsen'/'rengöra' не являются
# префиксами своих же спрягаемых форм ('wächst'/'rengör' короче или
# отличаются гласной), поэтому нужен именно общий корень.
GROW_WORD  = {'en': 'grow',  'de': 'wachs',   'nl': 'groei', 'sv': 'odla'}
CLEAN_WORD = {'en': 'clean', 'de': 'reinig',  'nl': 'schoonmaken', 'sv': 'rengör'}

def detect_category(keyword='', slug='', lang='en'):
    lang = lang if lang in TECH_WORDS else 'en'
    text = f'{keyword} {slug}'.lower()

    if _has_any(text, TECH_WORDS[lang], lang):
        return 'tech-devices'

    if _has_any(text, KITCHEN_WORDS[lang], lang):
        return 'kitchen-food'

    if _has_any(text, HOME_GARDEN_WORDS[lang], lang):
        return 'home-garden'

    if _has_word(text, GROW_WORD[lang], lang) and _has_any(text, GROW_COMPANIONS[lang], lang):
        return 'home-garden'

    if _has_word(text, CLEAN_WORD[lang], lang) and _has_any(text, CLEAN_COMPANIONS[lang], lang):
        return 'home-garden'

    if _has_any(text, DIY_WORDS[lang], lang):
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
            category = fm.get('category') or detect_category(fm.get('keyword', ''), slug, lang)
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
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="duplicate"', (lang,))
        duplicate = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM keywords WHERE lang=? AND status="fragment"', (lang,))
        fragment = c.fetchone()[0]
        extra = ''
        if duplicate:
            extra += f' | 🔗 {duplicate} дублей пропущено'
        if fragment:
            extra += f' | 🧩 {fragment} фрагментов отфильтровано'
        print(f'   {lang.upper()}: ✅ {done} опубликовано | ⏳ {pending} в очереди{extra}')
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
