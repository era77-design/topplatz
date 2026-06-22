"""
migrate_db.py — РАЗОВЫЙ скрипт.
Добавляет новые таблицы для семантического ядра в существующую keywords.db.
Существующие данные НЕ трогает, полностью безопасно запускать на живой БД.

Запуск: py -3.11 migrate_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path('keywords.db')

if not DB_PATH.exists():
    print('❌ keywords.db не найдена — запусти из корня проекта')
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

# Проверяем существующие колонки keywords
c.execute('PRAGMA table_info(keywords)')
existing_cols = {row[1] for row in c.fetchall()}

# Добавляем topic_id к существующей таблице keywords (если ещё нет)
if 'topic_id' not in existing_cols:
    c.execute('ALTER TABLE keywords ADD COLUMN topic_id TEXT')
    print('✅ keywords.topic_id добавлена')
else:
    print('ℹ️  keywords.topic_id уже существует')

# Таблица семантических кластеров / тем
c.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id             TEXT NOT NULL,   -- "delete-facebook-account"
        lang           TEXT NOT NULL,   -- "en"
        primary_kw     TEXT NOT NULL,   -- лучший ключевик для H1/title
        category       TEXT,            -- "tech-devices"
        total_searches INTEGER DEFAULT 0,
        total_value    REAL DEFAULT 0,  -- Σ(searches × cpc) — реальная ценность
        tier           TEXT DEFAULT 'C', -- A/B/C по ценности
        status         TEXT DEFAULT 'pending', -- pending/done
        article_slug   TEXT,            -- slug опубликованной статьи
        created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id, lang)
    )
''')
print('✅ topics таблица создана (или уже существовала)')

# Таблица ролей ключевиков внутри кластера
c.execute('''
    CREATE TABLE IF NOT EXISTS keyword_roles (
        keyword_id  INTEGER NOT NULL,
        topic_id    TEXT NOT NULL,
        lang        TEXT NOT NULL,
        role        TEXT NOT NULL, -- primary/secondary/faq/longtail/invalid
        priority    INTEGER DEFAULT 0,
        PRIMARY KEY (keyword_id, topic_id, lang),
        FOREIGN KEY (keyword_id) REFERENCES keywords(id)
    )
''')
print('✅ keyword_roles таблица создана (или уже существовала)')

# Индекс для быстрого поиска по topic_id
c.execute('CREATE INDEX IF NOT EXISTS idx_keywords_topic ON keywords(topic_id)')
c.execute('CREATE INDEX IF NOT EXISTS idx_topics_lang ON topics(lang)')
c.execute('CREATE INDEX IF NOT EXISTS idx_topics_tier ON topics(tier, lang)')
print('✅ Индексы созданы')

conn.commit()
conn.close()

print('\n🎉 Миграция завершена — существующие данные не тронуты')
print('   Следующий шаг: py -3.11 scripts/smart_cluster.py en --preview')
