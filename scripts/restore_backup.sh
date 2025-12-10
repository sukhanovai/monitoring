#!/bin/bash
# Скрипт восстановления из резервной копии

if [ -z "$1" ]; then
    echo "Использование: $0 <путь_к_резервной_копии>"
    echo "Пример: $0 /opt/monitoring/backup_20241208_210100"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Резервная копия не найдена: $BACKUP_DIR"
    exit 1
fi

echo "🔙 Восстановление из резервной копии: $BACKUP_DIR"
echo "Это восстановит старую структуру. Продолжить? (y/N)"
read -r answer

if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "Восстановление отменено"
    exit 0
fi

# Останавливаем службы если они запущены
echo "🛑 Остановка служб..."
systemctl stop monitoring-bot 2>/dev/null || true
systemctl stop mail-monitor 2>/dev/null || true

# Восстанавливаем файлы
echo "📦 Восстановление файлов..."

# Основные файлы
for file in bot_menu.py config.py core_utils.py debug_config.py improved_mail_monitor.py main.py monitor_core.py settings_handlers.py settings_manager.py; do
    if [ -f "$BACKUP_DIR/$file" ]; then
        cp "$BACKUP_DIR/$file" "/opt/monitoring/$file"
        echo "  ✅ $file"
    fi
done

# Директории
for dir in extensions data logs; do
    if [ -d "$BACKUP_DIR/$dir" ]; then
        rm -rf "/opt/monitoring/$dir"
        cp -r "$BACKUP_DIR/$dir" "/opt/monitoring/"
        echo "  ✅ $dir/"
    fi
done

# Удаляем новую структуру если она есть
echo "🧹 Очистка новой структуры..."
rm -rf /opt/monitoring/app 2>/dev/null || true
rm -rf /opt/monitoring/scripts 2>/dev/null || true

echo "✅ Восстановление завершено!"
echo "Запустите систему: systemctl start monitoring-bot"
