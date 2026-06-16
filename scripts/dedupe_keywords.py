"""
dedupe_keywords.py — находит near-duplicate ключевики в keywords.db и
помечает статусом 'duplicate' все варианты кроме одного (с наибольшим
объёмом поиска) в каждой группе. Данные НЕ удаляются — статус обратим.

Примеры того, что попадает в одну группу:
  "how to delete facebook" / "how do you delete facebook" / "how do i delete facebook"
  "how can i get taller" / "how do i get taller" / "how can you get taller"

ЧТО НЕ ЛОВИТ (осознанное ограничение):
  Синонимы без общих корневых слов: "false nails" vs "artificial nails",
  "sticker residue" vs "sticker glue" — для этого нужна семантическая
  (LLM) проверка, а не просто пересечение слов. Можно добавить отдельным
  шагом позже, если понадобится более глубокая чистка.

ИСПОЛЬЗОВАНИЕ:
  py -3.11 scripts/dedupe_keywords.py            # dry-run — только отчёт,
                                                    БД не трогает
  py -3.11 scripts/dedupe_keywords.py --apply     # применить изменения

Полный отчёт всегда пишется в dedup_report.txt (корень проекта) —
удобно открыть в VS Code и пролистать все группы перед --apply.
"""

import sqlite3
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'keywords.db'
REPORT_PATH = ROOT / 'dedup_report.txt'

SIMILARITY_THRESHOLD = 0.6  # доля общих значимых слов, чтобы считать дублем

# Вопросительные префиксы, не меняющие суть запроса — убираются перед сравнением
QUESTION_PREFIXES = [
    'how do i', 'how do you', 'how can i', 'how can you',
    'how does one', 'how should i', 'how can one',
    'what is the best way to', 'best way to', 'ways to',
    'tips for', 'tips to', 'guide to', 'how to',
    # DE
    'wie kann ich', 'wie kann man', 'wie macht man', 'wie',
    # NL
    'hoe kan ik', 'hoe',
    # SV
    'hur kan jag', 'hur gör man', 'hur',
]

# Слова без значимого веса для определения дублей (язык-независимый общий набор + EN)
STOPWORDS = {
    'a', 'an', 'the', 'my', 'your', 'his', 'her', 'their', 'our',
    'to', 'of', 'in', 'on', 'at', 'for', 'with', 'from', 'out',
    'off', 'up', 'is', 'are', 'do', 'does', 'i', 'you', 'it',
    'and', 'or', 'be',
    'permanently', 'easily', 'quickly', 'safely', 'fast', 'naturally',
    'completely', 'properly', 'correctly', 'effectively',
}


def normalize(keyword):
    """Возвращает frozenset значимых слов после очистки от вопросительных
    префиксов, стоп-слов и пунктуации — используется как 'отпечаток' темы."""
    text = keyword.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)

    for prefix in sorted(QUESTION_PREFIXES, key=len, reverse=True):
        if text.startswith(prefix + ' '):
            text = text[len(prefix):].strip()
            break

    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    return frozenset(words)


def jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def find_duplicate_groups(rows):
    """
    rows: список (keyword, lang, status, avg_searches, cpc_high)
    Возвращает список групп — каждая группа — список индексов в rows,
    которые считаются дублями друг друга (объём > 1).
    """
    token_index = defaultdict(list)
    signatures = {}

    for idx, row in enumerate(rows):
        sig = normalize(row[0])
        signatures[idx] = sig
        for token in sig:
            token_index[token].append(idx)

    parent = list(range(len(rows)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    compared = set()
    for idx, row in enumerate(rows):
        lang = row[1]
        sig = signatures[idx]
        if not sig:
            continue

        candidates = set()
        for token in sig:
            candidates.update(token_index[token])
        candidates.discard(idx)

        for cand in candidates:
            if rows[cand][1] != lang:
                continue
            pair = (min(idx, cand), max(idx, cand))
            if pair in compared:
                continue
            compared.add(pair)
            if jaccard(sig, signatures[cand]) >= SIMILARITY_THRESHOLD:
                union(idx, cand)

    groups = defaultdict(list)
    for idx in range(len(rows)):
        groups[find(idx)].append(idx)

    return [g for g in groups.values() if len(g) > 1]


def main():
    apply_changes = '--apply' in sys.argv

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT keyword, lang, status, avg_searches, cpc_high FROM keywords WHERE status="pending"')
    rows = c.fetchall()

    print(f'📊 Анализируем {len(rows)} ключевиков со статусом pending...')

    groups = find_duplicate_groups(rows)
    total_marked = sum(len(g) - 1 for g in groups)
    by_lang = defaultdict(lambda: [0, 0])  # lang -> [групп, дублей]

    report_lines = [
        f'Отчёт о дедупликации — {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'Порог схожести: {SIMILARITY_THRESHOLD}',
        f'Всего pending ключевиков: {len(rows)}',
        f'Найдено групп дублей: {len(groups)}',
        f'Будет помечено дублями: {total_marked}',
        '=' * 70,
        '',
    ]

    groups.sort(key=lambda g: max(rows[i][3] or 0 for i in g), reverse=True)

    for group in groups:
        group_rows = [rows[i] for i in group]
        group_rows.sort(key=lambda r: (r[3] or 0, r[4] or 0), reverse=True)
        keep = group_rows[0]
        duplicates = group_rows[1:]
        lang = keep[1]
        by_lang[lang][0] += 1
        by_lang[lang][1] += len(duplicates)

        report_lines.append(f'[{lang.upper()}] ОСТАВЛЯЕМ: "{keep[0]}"  ({keep[3]:,} поисков, ${keep[4]:.2f} CPC)')
        for dup in duplicates:
            report_lines.append(f'         дубль:    "{dup[0]}"  ({dup[3]:,} поисков)')
        report_lines.append('')

        if apply_changes:
            for dup in duplicates:
                c.execute(
                    'UPDATE keywords SET status="duplicate" WHERE keyword=? AND lang=?',
                    (dup[0], dup[1])
                )

    REPORT_PATH.write_text('\n'.join(report_lines), encoding='utf-8')

    print(f'\n📋 Групп дублей: {len(groups)}')
    for lang, (n_groups, n_dupes) in sorted(by_lang.items()):
        print(f'   {lang.upper()}: {n_groups} групп, {n_dupes} ключевиков будут помечены дублями')

    print(f'\n📄 Полный отчёт: {REPORT_PATH.relative_to(ROOT)}')

    if apply_changes:
        conn.commit()
        print(f'\n✅ Применено: {total_marked} ключевиков помечены как "duplicate"')
        print('   Они больше не будут попадать в generator.py (фильтр status="pending")')
    else:
        print(f'\n👀 DRY-RUN — изменения в БД НЕ применены.')
        print(f'   Открой {REPORT_PATH.name} и проверь группы.')
        print(f'   Если всё ок — запусти: py -3.11 scripts/dedupe_keywords.py --apply')

    conn.close()


if __name__ == '__main__':
    main()
