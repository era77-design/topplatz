"""
sync_db.py — синхронизирует keywords.db с реальными файлами на диске.
Читает keyword из frontmatter каждого .mdx файла и помечает его в БД
как status='done', если он был в другом статусе (не duplicate/fragment).

Запуск: py -3.11 sync_db.py
"""
import sqlite3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = sqlite3.connect(str(ROOT / 'keywords.db'))
c = DB.cursor()
fixed = 0

for lang in ('en', 'de', 'nl', 'sv'):
    content_dir = ROOT / 'content' / lang
    if not content_dir.exists():
        continue
    for mdx in content_dir.glob('*.mdx'):
        text = mdx.read_text(encoding='utf-8')
        m = re.search(r'^keyword:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
        if not m:
            continue
        kw = m.group(1).strip().strip('"\'')
        c.execute(
            'UPDATE keywords SET status="done" WHERE keyword=? AND lang=? '
            'AND status NOT IN ("done","duplicate","fragment")',
            (kw, lang)
        )
        if c.rowcount:
            fixed += 1
            print(f'  [{lang}] done: {kw}')

DB.commit()
DB.close()
print(f'\nСинхронизировано: {fixed} ключевиков помечены done')
