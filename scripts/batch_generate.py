"""
Запускает generator.py несколько раундов подряд с паузой между ними
(чтобы не превысить лимит Unsplash API: 50 запросов/час на free-тарифе),
затем один раз publish.py в конце.

Использование:
  py -3.11 scripts/batch_generate.py          # 3 раунда (по умолчанию)
  py -3.11 scripts/batch_generate.py 5        # 5 раундов
  py -3.11 scripts/batch_generate.py 5 10     # 5 раундов, пауза 10 мин
"""

import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROUNDS        = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PAUSE_MINUTES = int(sys.argv[2]) if len(sys.argv) > 2 else 15

print(f'🤖 Batch-генерация: {ROUNDS} раундов, пауза {PAUSE_MINUTES} мин\n')

for i in range(1, ROUNDS + 1):
    print(f'\n{"="*52}')
    print(f'  РАУНД {i}/{ROUNDS}')
    print(f'{"="*52}\n')

    result = subprocess.run(
        ['py', '-3.11', str(ROOT / 'scripts' / 'generator.py')],
        cwd=ROOT
    )

    if result.returncode != 0:
        print(f'\n⚠️  Раунд {i} завершился с ошибкой (код {result.returncode})')

    if i < ROUNDS:
        print(f'\n⏸️  Пауза {PAUSE_MINUTES} мин (лимит Unsplash API)...')
        time.sleep(PAUSE_MINUTES * 60)

print(f'\n{"="*52}')
print('  ПУБЛИКАЦИЯ')
print(f'{"="*52}\n')
subprocess.run(['py', '-3.11', str(ROOT / 'scripts' / 'publish.py')], cwd=ROOT)

print('\n🎉 Batch-генерация завершена!')
