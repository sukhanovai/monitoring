"""
/extensions/extension_manager.py
Server Monitoring System v4.20.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Extension Manager for Monitoring
Система мониторинга серверов
Версия: 4.20.1
Автор: Александр Суханов (c)
Лицензия: MIT
Менеджер расширений для мониторинга
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from config.settings import DATA_DIR

# Путь к каталогу конфигурации расширений
EXTENSIONS_CONFIG_DIR = Path(DATA_DIR) / "extensions"

# Путь к файлу конфигурации расширений
EXTENSIONS_CONFIG_FILE = EXTENSIONS_CONFIG_DIR / "extensions_config.json"
LEGACY_EXTENSIONS_CONFIG_FILE = Path(DATA_DIR) / "extensions_config.json"

# Список всех доступных расширений
AVAILABLE_EXTENSIONS = {
    'backup_monitor': {
        'name': '📊 Мониторинг бэкапов Proxmox',
        'description': 'Отслеживание статуса бэкапов Proxmox из почтовых уведомлений',
        'commands': ['/backup', '/backup_search', '/backup_help'],
        'handlers': ['backup_'],
        'enabled_by_default': True,
        'package': 'extensions.backup_monitor'
    },
    'database_backup_monitor': {
        'name': '🗃️ Мониторинг бэкапов БД',
        'description': 'Отслеживание статуса бэкапов баз данных',
        'commands': ['/db_backups'],
        'handlers': ['db_backups_'],
        'enabled_by_default': True,
        'package': 'extensions.server_checks'
    },
    'resource_monitor': {
        'name': '💻 Мониторинг ресурсов',
        'description': 'Проверка загрузки CPU, RAM и дискового пространства',
        'commands': ['check_resources', 'check_cpu', 'check_ram', 'check_disk'],
        'handlers': ['check_'],
        'enabled_by_default': True,
        'package': 'extensions.web_interface'
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
        self.config_dir = EXTENSIONS_CONFIG_DIR
        self.config_file = EXTENSIONS_CONFIG_FILE
        self.extensions_config: Dict[str, Dict[str, Any]] = self.load_config()

    def _ensure_config_dir(self) -> None:
        """Создает каталог для конфигов расширений при необходимости"""
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

    def _build_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Формирует конфигурацию по умолчанию для всех доступных расширений"""
        return {
            ext_id: {
                'enabled': ext_info.get('enabled_by_default', False),
                'last_modified': datetime.now().isoformat()
            }
            for ext_id, ext_info in AVAILABLE_EXTENSIONS.items()
        }
    
    def load_config(self) -> Dict[str, Dict[str, Any]]:
        """Загружает конфигурацию расширений из файла"""
        self._ensure_config_dir()

        try:
            config: Dict[str, Dict[str, Any]] = {}
            loaded_from_legacy = False

            if self.config_file.exists():
                config = json.loads(self.config_file.read_text(encoding="utf-8"))
            elif LEGACY_EXTENSIONS_CONFIG_FILE.exists():
                config = json.loads(LEGACY_EXTENSIONS_CONFIG_FILE.read_text(encoding="utf-8"))
                loaded_from_legacy = True

            changed = loaded_from_legacy

            if not config:
                config = self._build_default_config()
                changed = True
            else:
                for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
                    if ext_id not in config:
                        config[ext_id] = {
                            'enabled': ext_info.get('enabled_by_default', False),
                            'last_modified': datetime.now().isoformat()
                        }
                        changed = True

                unknown = [ext_id for ext_id in config if ext_id not in AVAILABLE_EXTENSIONS]
                for ext_id in unknown:
                    config.pop(ext_id, None)
                    changed = True

            if changed:
                self.save_config(config)

            return config
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации расширений: {e}")
            return {}
    
    def save_config(self, config: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Сохраняет конфигурацию расширений в файл"""
        try:
            if config is None:
                config = self.extensions_config
            
            self._ensure_config_dir()
            self.config_file.write_text(
                json.dumps(config, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации расширений: {e}")
            return False
    
    def get_extension_config_path(self, extension_id: str) -> Path:
        """Возвращает путь к файлу конфига конкретного расширения"""
        return Path(self.config_dir) / f"{extension_id}.json"

    def load_extension_config(self, extension_id: str) -> Dict[str, Any]:
        """Загружает конфиг конкретного расширения из его файла"""
        default_config = AVAILABLE_EXTENSIONS.get(extension_id, {}).get('default_config', {})
        path = self.get_extension_config_path(extension_id)

        try:
            if not path.exists():
                return default_config

            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Ошибка загрузки конфига для {extension_id}: {e}")
            return default_config

    def save_extension_config(self, extension_id: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Сохраняет конфиг конкретного расширения в его файл"""
        path = self.get_extension_config_path(extension_id)
        try:
            self._ensure_config_dir()
            path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True, f"✅ Конфиг {extension_id} сохранен"
        except Exception as e:
            return False, f"❌ Ошибка сохранения конфига {extension_id}: {e}"
    
    def is_extension_enabled(self, extension_id: str) -> bool:
        """Проверяет, включено ли расширение"""
        if extension_id not in self.extensions_config:
            # Если расширения нет в конфиге, используем значение по умолчанию
            return AVAILABLE_EXTENSIONS.get(extension_id, {}).get('enabled_by_default', False)
        
        return self.extensions_config[extension_id].get('enabled', False)
    
    def enable_extension(self, extension_id: str) -> Tuple[bool, str]:
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
    
    def disable_extension(self, extension_id: str) -> Tuple[bool, str]:
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
    
    def toggle_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Переключает состояние расширения"""
        if self.is_extension_enabled(extension_id):
            return self.disable_extension(extension_id)
        else:
            return self.enable_extension(extension_id)
    
    def get_extensions_status(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статус всех расширений"""
        status = {}
        for ext_id in AVAILABLE_EXTENSIONS:
            status[ext_id] = {
                'enabled': self.is_extension_enabled(ext_id),
                'info': AVAILABLE_EXTENSIONS[ext_id]
            }
        return status
    
    def get_enabled_extensions(self) -> List[str]:
        """Возвращает список включенных расширений"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if self.is_extension_enabled(ext_id)]
    
    def get_disabled_extensions(self) -> List[str]:
        """Возвращает список отключенных расширений"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if not self.is_extension_enabled(ext_id)]

    def is_command_available(self, command: str) -> bool:
        """Проверяет, доступна ли команда с учетом включенных расширений"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            if command in ext_info.get('commands', []) and not self.is_extension_enabled(ext_id):
                return False
        return True

    def is_handler_available(self, handler_pattern: str) -> bool:
        """Проверяет, доступен ли обработчик с учетом включенных расширений"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            for pattern in ext_info.get('handlers', []):
                if handler_pattern.startswith(pattern) and not self.is_extension_enabled(ext_id):
                    return False
        return True

    def filter_available_commands(self, commands_list: List[str]) -> List[str]:
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

def get_enabled_extensions() -> List[str]:
    return extension_manager.get_enabled_extensions()

def register_enabled_extensions(dispatcher: Any) -> None:
    """
    Регистрирует обработчики всех включенных расширений.
    dispatcher — это application.dispatcher / updater.dispatcher (в зависимости от PTB версии).
    """
    enabled = extension_manager.get_enabled_extensions()

    for ext_id in enabled:
        try:
            if ext_id == "backup_monitor":
                from extensions.backup_monitor.bot_handler import register_handlers as reg
                reg(dispatcher)

            # На будущее:
            # elif ext_id == "web_interface":
            #     from extensions.web_interface.bot_handler import register_handlers as reg
            #     reg(dispatcher)

        except Exception as e:
            # не валим весь бот из-за одного расширения
            from lib.logging import debug_log
            debug_log(f"❌ Ошибка регистрации расширения {ext_id}: {e}")
