"""
fix_missing_images.py — находит статьи без фото и добавляет их.

Читает все MDX-файлы, ищет те у которых нет photoUrl в frontmatter
(Unsplash не нашёл фото во время генерации — например "BlueBrixx instructions PDF"
не даёт результатов). Для каждой такой статьи пробует несколько запросов подряд,
пока не найдёт подходящее фото.

Запуск: py -3.11 fix_missing_images.py             # dry-run (показать список)
        py -3.11 fix_missing_images.py --apply       # применить
"""

import re
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

UNSPLASH_KEY     = os.getenv('UNSPLASH_KEY')
CONTENT_DIR      = ROOT / 'content'
USED_PHOTOS_FILE = ROOT / 'data' / 'used-photos.json'
APPLY            = '--apply' in sys.argv


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


def search_unsplash(query, used_ids, per_page=3):
    """Ищет фото на Unsplash. Возвращает первое неиспользованное или None."""
    try:
        resp = requests.get(
            'https://api.unsplash.com/search/photos',
            params={'query': query, 'per_page': per_page,
                    'orientation': 'landscape', 'content_filter': 'high'},
            headers={'Authorization': f'Client-ID {UNSPLASH_KEY}'},
            timeout=10
        )
        results = resp.json().get('results', [])
        for photo in results:
            if photo['id'] not in used_ids:
                return {
                    'id':           photo['id'],
                    'url':          photo['urls']['regular'],
                    'url_small':    photo['urls']['small'],
                    'alt':          photo.get('alt_description') or query,
                    'author_name':  photo['user']['name'],
                    'author_url':   photo['user']['links']['html'],
                    'unsplash_url': photo['links']['html'],
                }
        # Все использованы — берём первое попавшееся
        if results:
            p = results[0]
            return {
                'id':           p['id'],
                'url':          p['urls']['regular'],
                'url_small':    p['urls']['small'],
                'alt':          p.get('alt_description') or query,
                'author_name':  p['user']['name'],
                'author_url':   p['user']['links']['html'],
                'unsplash_url': p['links']['html'],
            }
    except Exception as e:
        print(f'      Unsplash error: {e}')
    return None


def make_fallback_queries(keyword, title, lang):
    """Генерирует несколько запросов от специфичного к общему."""
    # Базовый запрос = первые 3 слова ключевика без вопросительных слов
    stop = {'how','to','what','when','where','why','do','can','i','you',
            'wie','was','wo','wann','warum','hoe','wat','wanneer','varför',
            'hur','man','je','jij'}
    words = [w for w in keyword.lower().split() if w not in stop]
    short_kw = ' '.join(words[:3])

    # Извлекаем существительные из title (слова длиннее 4 букв, не стоп-слова)
    title_words = [w for w in re.sub(r'[^\w\s]','',title.lower()).split()
                   if len(w) > 4 and w not in stop]
    title_noun = ' '.join(title_words[:2]) if title_words else short_kw

    return [
        short_kw,
        title_noun,
        ' '.join(words[:2]) if len(words) >= 2 else short_kw,
        words[0] if words else 'guide',
    ]


def inject_photo_into_mdx(filepath, photo):
    """Вставляет/обновляет поля photo в frontmatter MDX-файла."""
    text = filepath.read_text(encoding='utf-8')

    # Проверяем что frontmatter есть
    if not text.startswith('---'):
        return False

    # Удаляем старые photo-поля если есть
    text = re.sub(r'\nphotoUrl:.*', '', text)
    text = re.sub(r'\nphotoAlt:.*', '', text)
    text = re.sub(r'\nphotoAuthor:.*', '', text)
    text = re.sub(r'\nphotoUnsplash:.*', '', text)
    # Удаляем старый image-блок после первого ---
    text = re.sub(r'\n!\[.*?\]\(.*?\)\n\*Photo by.*?\*\n', '\n', text)

    # Вставляем новые поля перед закрывающим ---
    photo_meta = (
        f'\nphotoUrl: "{photo["url"]}"'
        f'\nphotoAlt: "{photo["alt"]}"'
        f'\nphotoAuthor: "{photo["author_name"]}"'
        f'\nphotoUnsplash: "{photo["unsplash_url"]}"'
    )
    # Находим закрывающий --- frontmatter
    second_dash = text.index('---', 3)
    text = text[:second_dash] + photo_meta + '\n' + text[second_dash:]

    # Вставляем image-блок после первого ---\n
    image_block = (
        f'\n![{photo["alt"]}]({photo["url"]})\n'
        f'*Photo by [{photo["author_name"]}]({photo["author_url"]}) '
        f'on [Unsplash]({photo["unsplash_url"]})*\n'
    )
    # Находим конец frontmatter (второй ---)
    end_fm = text.index('---', 3) + 3
    text = text[:end_fm] + '\n' + image_block + text[end_fm:]

    filepath.write_text(text, encoding='utf-8')
    return True


def main():
    if not UNSPLASH_KEY:
        print('❌ UNSPLASH_KEY не задан в .env')
        return

    used_ids = load_used_photos()
    missing = []

    for lang in ('en', 'de', 'nl', 'sv'):
        lang_dir = CONTENT_DIR / lang
        if not lang_dir.exists():
            continue
        for mdx in sorted(lang_dir.glob('*.mdx')):
            text = mdx.read_text(encoding='utf-8')
            if 'photoUrl:' not in text:
                # Извлекаем keyword и title для fallback-запросов
                kw_m = re.search(r'^keyword:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
                ti_m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
                kw = kw_m.group(1).strip().strip('"\'') if kw_m else mdx.stem
                title = ti_m.group(1).strip().strip('"\'') if ti_m else kw
                missing.append((lang, mdx, kw, title))

    if not missing:
        print('✅ Все статьи имеют фото — ничего делать не нужно')
        return

    print(f'🔍 Найдено {len(missing)} статей без фото:\n')
    for lang, mdx, kw, title in missing:
        print(f'  [{lang}] {mdx.name}')
        print(f'         keyword: {kw}')

    if not APPLY:
        print(f'\n👀 DRY-RUN. Запусти с --apply чтобы добавить фото.')
        return

    print(f'\n🖼️  Добавляем фото...\n')
    fixed = 0
    failed = []

    for lang, mdx, kw, title in missing:
        queries = make_fallback_queries(kw, title, lang)
        photo = None
        for q in queries:
            if not q.strip():
                continue
            photo = search_unsplash(q, used_ids)
            if photo:
                print(f'  [{lang}] {mdx.name}')
                print(f'         query: "{q}" → {photo["author_name"]}')
                break
            time.sleep(0.3)

        if photo:
            inject_photo_into_mdx(mdx, photo)
            used_ids.add(photo['id'])
            fixed += 1
        else:
            print(f'  [{lang}] ❌ Не удалось найти фото: {mdx.name}')
            failed.append(mdx.name)

        time.sleep(0.5)  # rate limit

    save_used_photos(used_ids)
    print(f'\n✅ Добавлено фото: {fixed} | Не найдено: {len(failed)}')
    if failed:
        print('Не нашлось фото для:')
        for f in failed:
            print(f'  - {f}')
    print('\nДальше: py -3.11 scripts/publish.py')


if __name__ == '__main__':
    main()
