"""
keyword_quality_check.py — использует Gemini, чтобы определить, является
ли ключевик полноценной конкретной фразой (которую реально могли бы
искать) или обрывком/слишком общим словом без темы — например "anleitung"
(просто "инструкция", без объекта) или "wie kann ich" (обрывок вопроса
без продолжения).

Зачем: при импорте ключевиков иногда попадают такие артефакты — Google
Keyword Planner иногда выдаёт "seed"-термины с агрегированным объёмом
поиска (сумма по всем запросам, содержащим это слово), который не
относится буквально к этой короткой фразе. Генерация по таким
ключевикам создаёт статьи на ПРИДУМАННУЮ Gemini тему, не привязанную к
реальному поисковому запросу — впустую тратит API-вызовы.

Невалидные ключевики помечаются status='fragment' — не удаляются,
обратимо (--rollback).

ИСПОЛЬЗОВАНИЕ:
  py -3.11 scripts/keyword_quality_check.py de             # dry-run, отчёт
  py -3.11 scripts/keyword_quality_check.py de --apply      # применить
  py -3.11 scripts/keyword_quality_check.py --rollback      # откатить всё
"""

import sqlite3
import json
import re
import sys
import time
import threading
import queue
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = ROOT / 'keywords.db'
REPORT_PATH = ROOT / 'keyword_quality_report.txt'

BATCH_SIZE = 50  # сколько ключевиков отправляем за один запрос к Gemini

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# ЗАЩИТА ОТ ЗАВИСАНИЯ GEMINI API
# (тот же известный баг SDK, что в generator.py)
# ==========================================

def call_with_timeout(fn, timeout_sec, *args, **kwargs):
    result_queue = queue.Queue()

    def target():
        try:
            result_queue.put(('ok', fn(*args, **kwargs)))
        except Exception as e:
            result_queue.put(('error', e))

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        raise TimeoutError(f'не вернулся за {timeout_sec} сек')

    status, value = result_queue.get()
    if status == 'error':
        raise value
    return value


def fix_json(text):
    text = re.sub(r'^```json\s*', '', text.strip())
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


# ==========================================
# ПРОВЕРКА БАТЧА КЛЮЧЕВИКОВ
# ==========================================

def check_batch(keywords, lang):
    numbered = '\n'.join(f'{i+1}. {kw}' for i, kw in enumerate(keywords))

    prompt = f"""You are reviewing search keywords (language: {lang}) that will
each become the topic of a how-to article. For EACH numbered keyword below,
decide if it is a COMPLETE, SPECIFIC phrase representing genuine search intent
— something with a clear subject/topic a real person would type — or if it's
a FRAGMENT or too generic to be a standalone article topic.

Examples of FRAGMENT/too generic (false): a bare question stem with no object
("how can i", "wie kann ich"), a single generic word with no subject
("guide", "anleitung", "instructions" alone), an incomplete clause.

Examples of VALID (true): any phrase with a clear, specific subject — even
short ones like "lego anleitung" (lego instructions) or "tv reparieren"
(repair tv) are valid, since they name a specific topic.

Keywords:
{numbered}

Return ONLY a JSON array of {len(keywords)} booleans, one per keyword in
order, nothing else: [true, false, true, ...]"""

    response = call_with_timeout(
        client.models.generate_content,
        60,
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_budget=512),
            http_options=types.HttpOptions(timeout=50000)
        )
    )
    return json.loads(fix_json(response.text))


# ==========================================
# ROLLBACK
# ==========================================

def rollback():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('UPDATE keywords SET status="pending" WHERE status="fragment"')
    affected = c.rowcount
    conn.commit()
    conn.close()
    print(f'↩️  Откат: {affected} ключевиков возвращены в status="pending"')


# ==========================================
# ОСНОВНОЙ ЗАПУСК
# ==========================================

def main():
    if '--rollback' in sys.argv:
        rollback()
        return

    apply_changes = '--apply' in sys.argv
    lang_args = [a for a in sys.argv[1:] if a != '--apply']
    lang = lang_args[0].lower() if lang_args else None

    if lang not in ('en', 'de', 'nl', 'sv'):
        print('Укажи язык: py -3.11 scripts/keyword_quality_check.py de [--apply]')
        print('Доступные: en, de, nl, sv')
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT keyword FROM keywords WHERE lang=? AND status="pending"', (lang,))
    keywords = [row[0] for row in c.fetchall()]

    if not keywords:
        print(f'Нет pending ключевиков для {lang.upper()}')
        conn.close()
        return

    print(f'📊 Проверяем {len(keywords)} ключевиков [{lang.upper()}] через Gemini...')

    fragments = []
    valid_count = 0
    total_batches = (len(keywords) - 1) // BATCH_SIZE + 1

    for i in range(0, len(keywords), BATCH_SIZE):
        batch = keywords[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f'   Батч {batch_num}/{total_batches} ({len(batch)} ключевиков)...')

        try:
            results = check_batch(batch, lang)
            if len(results) != len(batch):
                print(f'      ⚠️  Несовпадение длины ответа ({len(results)} vs {len(batch)}) — пропускаем батч целиком')
                continue
            for kw, is_valid in zip(batch, results):
                if is_valid:
                    valid_count += 1
                else:
                    fragments.append(kw)
        except TimeoutError as e:
            print(f'      ⏱️  Таймаут ({e}) — пропускаем батч')
        except Exception as e:
            print(f'      ⚠️  Ошибка батча: {e}')

        time.sleep(1)

    report_lines = [
        f'Проверка качества ключевиков — {lang.upper()}',
        f'Всего проверено: {len(keywords)}',
        f'Валидных: {valid_count}',
        f'Фрагментов / слишком общих: {len(fragments)}',
        '=' * 50,
        '',
    ] + [f'  ❌ "{f}"' for f in fragments]

    REPORT_PATH.write_text('\n'.join(report_lines), encoding='utf-8')

    print(f'\n📋 Валидных: {valid_count} | Фрагментов: {len(fragments)}')
    print(f'📄 Полный отчёт: {REPORT_PATH.name}')

    if apply_changes:
        for kw in fragments:
            c.execute('UPDATE keywords SET status="fragment" WHERE keyword=? AND lang=?', (kw, lang))
        conn.commit()
        print(f'\n✅ Применено: {len(fragments)} ключевиков помечены status="fragment"')
        print('   Больше не будут попадать в generator.py')
    else:
        print(f'\n👀 DRY-RUN — изменения в БД НЕ применены.')
        print(f'   Открой {REPORT_PATH.name} и проверь список фрагментов.')
        print(f'   Если всё ок — запусти: py -3.11 scripts/keyword_quality_check.py {lang} --apply')

    conn.close()


if __name__ == '__main__':
    main()
