#!/bin/bash
cd /opt/monitoring

echo "🔍 Проверка структуры..."
echo "1. Проверка файлов:"
ls -la app/
echo ""
ls -la app/core/
echo ""
ls -la app/utils/

echo ""
echo "2. Тест импорта common.py:"
python3 -c "
import sys
sys.path.insert(0, '/opt/monitoring/app')
try:
    from utils.common import progress_bar, format_duration
    print('✅ common.py импортирован')
    print(f'   progress_bar(50): {progress_bar(50)}')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

echo ""
echo "3. Тест импорта checker.py:"
python3 -c "
import sys
sys.path.insert(0, '/opt/monitoring/app')
try:
    from core.checker import ServerChecker
    print('✅ checker.py импортирован')
    checker = ServerChecker()
    print(f'   ServerChecker создан: {checker}')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

echo ""
echo "✅ Проверка завершена"
