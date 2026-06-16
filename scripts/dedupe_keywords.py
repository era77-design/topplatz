"""
dedupe_keywords.py — находит near-duplicate ключевики в keywords.db.
Вместо того, чтобы их просто выбросить, КОНСОЛИДИРУЕТ их: похожие
формулировки сохраняются в колонке related_phrases у "главного"
(наибольший объём поиска) ключевика группы — generator.py использует
их как материал для FAQ-секции, чтобы ОДНА статья ранжировалась по
нескольким вариантам запроса. Остальные ключевики группы помечаются
статусом 'duplicate', чтобы не генерировать по ним отдельные
почти-дублирующие статьи (риск "scaled content abuse" в глазах
Google — много тонких похожих страниц вредит сайту целиком).

АЛГОРИТМ — 'star'-кластеризация, НЕ транзитивное Union-Find:
каждый кандидат сравнивается НАПРЯМУЮ с центром группы (самым
высокочастотным ключевиком), а не через цепочку промежуточных
совпадений. Это специально, чтобы избежать эффекта 'снежного кома'
(A похож на B, B похож на C, ...по цепочке Z тоже попадает в группу
с A, хотя A и Z вообще не связаны напрямую). Плюс есть жёсткий
потолок размера группы (MAX_CLUSTER_SIZE) как защита от аномалий.

Данные НЕ удаляются — статус обратим (--rollback откатывает всё,
включая очистку related_phrases).

ИСПОЛЬЗОВАНИЕ:
  py -3.11 scripts/dedupe_keywords.py              # dry-run — только отчёт
  py -3.11 scripts/dedupe_keywords.py --apply       # применить
  py -3.11 scripts/dedupe_keywords.py --rollback    # откатить ВСЕ
                                                       предыдущие --apply

Полный отчёт пишется в dedup_report.txt (корень проекта).
"""

import sqlite3
import re
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'keywords.db'
REPORT_PATH = ROOT / 'dedup_report.txt'

SIMILARITY_THRESHOLD = 0.6
MAX_CLUSTER_SIZE = 20  # защита от аномальных 'снежного кома' групп

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


def ensure_related_phrases_column(conn):
    """Добавляет колонку related_phrases, если её ещё нет (идемпотентно)."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(keywords)")
    cols = [row[1] for row in c.fetchall()]
    if 'related_phrases' not in cols:
        c.execute("ALTER TABLE keywords ADD COLUMN related_phrases TEXT")
        conn.commit()


def find_duplicate_groups(rows):
    """
    rows: список (keyword, lang, status, avg_searches, cpc_high)
    Возвращает список групп (списков индексов в rows). group[0] —
    всегда центр группы (наибольший объём поиска).

    'Star'-кластеризация: кандидат добавляется в группу ТОЛЬКО если
    похож НАПРЯМУЮ на центр — без транзитивных цепочек через других
    членов группы. Это специально устраняет эффект 'снежного кома'.
    """
    signatures = {}
    token_index = defaultdict(list)
    for idx, row in enumerate(rows):
        sig = normalize(row[0])
        signatures[idx] = sig
        for token in sig:
            token_index[token].append(idx)

    # центрами становятся сначала самые высокочастотные — это гарантирует,
    # что group[0] всегда остаётся keyword с наибольшим объёмом в группе
    order = sorted(range(len(rows)), key=lambda i: rows[i][3] or 0, reverse=True)
    claimed = [False] * len(rows)
    groups = []

    for idx in order:
        if claimed[idx]:
            continue
        center_sig = signatures[idx]
        if not center_sig:
            claimed[idx] = True
            continue

        lang = rows[idx][1]
        candidates = set()
        for token in center_sig:
            candidates.update(token_index[token])
        candidates.discard(idx)
        cand_sorted = sorted(candidates, key=lambda i: rows[i][3] or 0, reverse=True)

        group = [idx]
        claimed[idx] = True

        for cand in cand_sorted:
            if claimed[cand] or rows[cand][1] != lang:
                continue
            if len(group) >= MAX_CLUSTER_SIZE:
                break
            # сравнение ТОЛЬКО с центром — не с другими членами группы
            if jaccard(center_sig, signatures[cand]) >= SIMILARITY_THRESHOLD:
                group.append(cand)
                claimed[cand] = True

        if len(group) > 1:
            groups.append(group)

    return groups


def rollback():
    """Откатывает ВСЕ предыдущие --apply: status duplicate -> pending,
    очищает related_phrases у всех ключевиков."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('UPDATE keywords SET status="pending" WHERE status="duplicate"')
    affected = c.rowcount

    c.execute("PRAGMA table_info(keywords)")
    has_related = any(row[1] == 'related_phrases' for row in c.fetchall())
    if has_related:
        c.execute('UPDATE keywords SET related_phrases=NULL')

    conn.commit()
    conn.close()
    print(f'↩️  Откат выполнен: {affected} ключевиков возвращены в status="pending"')
    if has_related:
        print('   related_phrases очищены у всех ключевиков')


def main():
    if '--rollback' in sys.argv:
        rollback()
        return

    apply_changes = '--apply' in sys.argv

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    if apply_changes:
        ensure_related_phrases_column(conn)

    c.execute('SELECT keyword, lang, status, avg_searches, cpc_high FROM keywords WHERE status="pending"')
    rows = c.fetchall()

    print(f'📊 Анализируем {len(rows)} ключевиков со статусом pending...')

    groups = find_duplicate_groups(rows)
    total_marked = sum(len(g) - 1 for g in groups)
    by_lang = defaultdict(lambda: [0, 0])
    largest_group_size = max((len(g) for g in groups), default=0)

    report_lines = [
        f'Отчёт о консолидации ключевиков — {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'Порог схожести: {SIMILARITY_THRESHOLD} | Потолок группы: {MAX_CLUSTER_SIZE}',
        f'Всего pending ключевиков: {len(rows)}',
        f'Найдено групп: {len(groups)}',
        f'Формулировок будет консолидировано (войдут в FAQ главной статьи): {total_marked}',
        f'Самая большая группа: {largest_group_size} ключевиков',
        '=' * 70,
        '',
    ]

    groups.sort(key=lambda g: rows[g[0]][3] or 0, reverse=True)

    for group in groups:
        group_rows = [rows[i] for i in group]
        keep = group_rows[0]          # уже центр — наибольший объём, по построению
        duplicates = group_rows[1:]
        lang = keep[1]
        by_lang[lang][0] += 1
        by_lang[lang][1] += len(duplicates)
        cluster_volume = sum(r[3] or 0 for r in group_rows)

        report_lines.append(f'[{lang.upper()}] ГЛАВНАЯ СТАТЬЯ: "{keep[0]}"  ({keep[3]:,} поисков, ${keep[4]:.2f} CPC)')
        report_lines.append(f'         суммарный охват кластера: {cluster_volume:,} поисков/мес, {len(group_rows)} формулировок')
        for dup in duplicates:
            report_lines.append(f'         + войдёт в FAQ:  "{dup[0]}"  ({dup[3]:,} поисков)')
        report_lines.append('')

        if apply_changes:
            new_phrases = [d[0] for d in duplicates]
            c.execute('SELECT related_phrases FROM keywords WHERE keyword=? AND lang=?', (keep[0], keep[1]))
            existing_row = c.fetchone()
            existing = json.loads(existing_row[0]) if existing_row and existing_row[0] else []
            merged = existing + [p for p in new_phrases if p not in existing]

            c.execute(
                'UPDATE keywords SET related_phrases=? WHERE keyword=? AND lang=?',
                (json.dumps(merged, ensure_ascii=False), keep[0], keep[1])
            )
            for dup in duplicates:
                c.execute(
                    'UPDATE keywords SET status="duplicate" WHERE keyword=? AND lang=?',
                    (dup[0], dup[1])
                )

    REPORT_PATH.write_text('\n'.join(report_lines), encoding='utf-8')

    print(f'\n📋 Групп: {len(groups)} | Самая большая группа: {largest_group_size} ключевиков')
    for lang, (n_groups, n_phrases) in sorted(by_lang.items()):
        print(f'   {lang.upper()}: {n_groups} групп, {n_phrases} формулировок будут консолидированы в FAQ')

    print(f'\n📄 Полный отчёт: {REPORT_PATH.relative_to(ROOT)}')

    if apply_changes:
        conn.commit()
        print(f'\n✅ Применено: {total_marked} формулировок сохранены как related_phrases')
        print('   и помечены "duplicate" (не будут генерироваться отдельно)')
    else:
        print(f'\n👀 DRY-RUN — изменения в БД НЕ применены.')
        print(f'   Открой {REPORT_PATH.name} и проверь группы.')
        print(f'   Если всё ок — запусти: py -3.11 scripts/dedupe_keywords.py --apply')

    conn.close()


if __name__ == '__main__':
    main()
