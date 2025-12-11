#!/bin/bash
# /opt/monitoring/migrate_core_utils.sh
# Скрипт миграции core_utils.py

set -e  # Выход при ошибке

echo "🔄 Начинаем миграцию core_utils.py..."

# 1. Создаем резервную копию оригинала
BACKUP_DIR="/opt/monitoring/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp core_utils.py "$BACKUP_DIR/"
echo "✅ Создана резервная копия в $BACKUP_DIR"

# 2. Тестируем новую структуру
echo "🧪 Тестируем новую структуру..."
python3 test_new_structure.py

if [ $? -ne 0 ]; then
    echo "❌ Тест провален. Отмена миграции."
    exit 1
fi

# 3. Создаем симлинк для обратной совместимости (ОПЦИОНАЛЬНО)
echo "🔗 Создаем симлинк для совместимости..."
ln -sf /opt/monitoring/app/core/checker.py /opt/monitoring/core_checker_new.py
ln -sf /opt/monitoring/app/utils/common.py /opt/monitoring/utils_common_new.py

# 4. Тестовый запуск бота с новой структурой
echo "🤖 Тестовый запуск бота..."
if systemctl is-active --quiet monitoring; then
    echo "⚠️  Сервис мониторинга запущен. Тестируем без перезапуска."
    
    # Создаем тестовый скрипт для проверки импортов
    cat > /tmp/test_imports.py << 'EOF'
import sys
sys.path.insert(0, '/opt/monitoring/app')
try:
    from app import server_checker, logger
    print("✅ Новые импорты работают")
    
    # Тест функций
    from app.utils.common import progress_bar
    print(f"✅ Функция progress_bar: {progress_bar(50)}")
    
    print("🎉 Все тесты пройдены!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
    
    python3 /tmp/test_imports.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Бот совместим с новой структурой"
    else
        echo "❌ Проблемы с совместимостью"
    fi
    
    rm /tmp/test_imports.py
fi

echo ""
echo "=========================================="
echo "МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!"
echo "=========================================="
echo ""
echo "Что было сделано:"
echo "1. ✅ Создана новая структура в /opt/monitoring/app/"
echo "2. ✅ core_utils.py разбит на модули:"
echo "   - /opt/monitoring/app/core/checker.py"
echo "   - /opt/monitoring/app/utils/common.py"
echo "3. ✅ Созданы файлы совместимости"
echo "4. ✅ Проведено тестирование"
echo ""
echo "Следующие шаги:"
echo "1. Запустите бота в тестовом режиме:"
echo "   python3 /opt/monitoring/main_new.py"
echo "2. Проверьте логи:"
echo "   tail -f /opt/monitoring/bot_debug.log"
echo "3. Если всё работает, можно обновлять импорты"
echo "   в других файлах (monitor_core.py и т.д.)"
echo ""
echo "Резервная копия оригинала: $BACKUP_DIR"
