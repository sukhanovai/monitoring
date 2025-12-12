"""
Server Monitoring System v4.1.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Менеджер расширений для мониторинга
Версия: 4.1.1
"""

import json
import os
from datetime import datetime

# Путь к файлу конфигурации расширений
EXTENSIONS_CONFIG_FILE = '/opt/monitoring/data/extensions_config.json'

# Список всех доступных расширений
AVAILABLE_EXTENSIONS = {
    'backup_monitor': {
        'name': '📊 Мониторинг бэкапов Proxmox',
        'description': 'Отслеживание статуса бэкапов Proxmox из почтовых уведомлений',
        'commands': ['/backup', '/backup_search', '/backup_help'],
        'handlers': ['backup_'],
        'enabled_by_default': True
    },
    'database_backup_monitor': {
        'name': '🗃️ Мониторинг бэкапов БД',
        'description': 'Отслеживание статуса бэкапов баз данных',
        'commands': ['/db_backups'],
        'handlers': ['db_backups_'],
        'enabled_by_default': True
    },
    'resource_monitor': {
        'name': '💻 Мониторинг ресурсов',
        'description': 'Проверка загрузки CPU, RAM и дискового пространства',
        'commands': ['check_resources', 'check_cpu', 'check_ram', 'check_disk'],
        'handlers': ['check_'],
        'enabled_by_default': True
    },
    'web_interface': {
        'name': '🌐 Веб-интерфейс',
        'description': 'Веб-панель управления по адресу http://192.168.20.2:5000',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'email_processor': {
        'name': '📧 Обработка почты',
        'description': 'Автоматическая обработка писем с отчетами о бэкапах',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'inventory_monitor': {
        'name': '📦 Инвентаризация',
        'description': 'Отслеживание аппаратного обеспечения серверов',
        'commands': [],
        'handlers': [],
        'enabled_by_default': False
    },
    'zfs_monitor': {
        'name': '💾 ZFS мониторинг',
        'description': 'Мониторинг ZFS файловых систем и пулов',
        'commands': [],
        'handlers': [],
        'enabled_by_default': False
    }
}

class ExtensionManager:
    def __init__(self):
        self.config_file = EXTENSIONS_CONFIG_FILE
        self.extensions_config = self.load_config()
    
    def load_config(self):
        """Загружает конфигурацию расширений из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Создаем конфиг по умолчанию
                default_config = {}
                for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
                    default_config[ext_id] = {
                        'enabled': ext_info['enabled_by_default'],
                        'last_modified': datetime.now().isoformat()
                    }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации расширений: {e}")
            return {}
    
    def save_config(self, config=None):
        """Сохраняет конфигурацию расширений в файл"""
        try:
            if config is None:
                config = self.extensions_config
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации расширений: {e}")
            return False
    
    def is_extension_enabled(self, extension_id):
        """Проверяет, включено ли расширение"""
        if extension_id not in self.extensions_config:
            # Если расширения нет в конфиге, используем значение по умолчанию
            return AVAILABLE_EXTENSIONS.get(extension_id, {}).get('enabled_by_default', False)
        
        return self.extensions_config[extension_id].get('enabled', False)
    
    def enable_extension(self, extension_id):
        """Включает расширение"""
        if extension_id not in AVAILABLE_EXTENSIONS:
            return False, f"❌ Расширение '{extension_id}' не найдено"
        
        if extension_id not in self.extensions_config:
            self.extensions_config[extension_id] = {}
        
        self.extensions_config[extension_id]['enabled'] = True
        self.extensions_config[extension_id]['last_modified'] = datetime.now().isoformat()
        
        if self.save_config():
            return True, f"✅ Расширение '{AVAILABLE_EXTENSIONS[extension_id]['name']}' включено"
        else:
            return False, f"❌ Ошибка сохранения конфигурации"
    
    def disable_extension(self, extension_id):
        """Отключает расширение"""
        if extension_id not in AVAILABLE_EXTENSIONS:
            return False, f"❌ Расширение '{extension_id}' не найдено"
        
        if extension_id not in self.extensions_config:
            self.extensions_config[extension_id] = {}
        
        self.extensions_config[extension_id]['enabled'] = False
        self.extensions_config[extension_id]['last_modified'] = datetime.now().isoformat()
        
        if self.save_config():
            return True, f"✅ Расширение '{AVAILABLE_EXTENSIONS[extension_id]['name']}' отключено"
        else:
            return False, f"❌ Ошибка сохранения конфигурации"
    
    def toggle_extension(self, extension_id):
        """Переключает состояние расширения"""
        if self.is_extension_enabled(extension_id):
            return self.disable_extension(extension_id)
        else:
            return self.enable_extension(extension_id)
    
    def get_extensions_status(self):
        """Возвращает статус всех расширений"""
        status = {}
        for ext_id in AVAILABLE_EXTENSIONS:
            status[ext_id] = {
                'enabled': self.is_extension_enabled(ext_id),
                'info': AVAILABLE_EXTENSIONS[ext_id]
            }
        return status
    
    def get_enabled_extensions(self):
        """Возвращает список включенных расширений"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if self.is_extension_enabled(ext_id)]
    
    def get_disabled_extensions(self):
        """Возвращает список отключенных расширений"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if not self.is_extension_enabled(ext_id)]

    def is_command_available(self, command):
        """Проверяет, доступна ли команда с учетом включенных расширений"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            if command in ext_info.get('commands', []) and not self.is_extension_enabled(ext_id):
                return False
        return True

    def is_handler_available(self, handler_pattern):
        """Проверяет, доступен ли обработчик с учетом включенных расширений"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            for pattern in ext_info.get('handlers', []):
                if handler_pattern.startswith(pattern) and not self.is_extension_enabled(ext_id):
                    return False
        return True

    def filter_available_commands(self, commands_list):
        """Фильтрует список команд, оставляя только доступные"""
        return [cmd for cmd in commands_list if self.is_command_available(cmd)]

    def should_include_backup_data(self):
        """Проверяет, нужно ли включать данные о бэкапах в отчеты"""
        return self.is_extension_enabled('backup_monitor')

    def is_web_interface_enabled(self):
        """Проверяет, включен ли веб-интерфейс"""
        return self.is_extension_enabled('web_interface')

# Глобальный экземпляр менеджера расширений
extension_manager = ExtensionManager()
