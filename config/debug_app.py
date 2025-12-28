"""
/config/debug_app.py
Server Monitoring System v5.3.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring system debug configuration
Система мониторинга серверов
Версия: 5.3.7
Автор: Александр Суханов (c)
Лицензия: MIT
Конфигурация отладки системы мониторинга
"""

import json
from datetime import datetime
from pathlib import Path

try:
    from config.settings import DATA_DIR, DEBUG_CONFIG_FILE
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"
    DEBUG_CONFIG_FILE = DATA_DIR / "debug_config.json"

# Путь к файлу конфигурации отладки
DEBUG_CONFIG_FILE = Path(DEBUG_CONFIG_FILE)

class DebugConfig:
    """Класс для управления настройками отладки"""
    
    def __init__(self):
        self.config_file = DEBUG_CONFIG_FILE
        self.config = self.load_config()
        
    def load_config(self):
        """Загружает конфигурацию отладки"""
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text(encoding="utf-8"))
            else:
                # Конфигурация по умолчанию
                default_config = {
                    'debug_mode': False,
                    'log_level': 'INFO',
                    'enable_ssh_debug': False,
                    'enable_resource_debug': False,
                    'enable_backup_debug': True,
                    'max_log_size_mb': 100,
                    'last_modified': datetime.now().isoformat()
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации отладки: {e}")
            return self.get_default_config()
    
    def save_config(self, config=None):
        """Сохраняет конфигурацию отладки"""
        try:
            if config is None:
                config = self.config
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            config['last_modified'] = datetime.now().isoformat()
            
            self.config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации отладки: {e}")
            return False
    
    def get_default_config(self):
        """Возвращает конфигурацию по умолчанию"""
        return {
            'debug_mode': False,
            'log_level': 'INFO',
            'enable_ssh_debug': False,
            'enable_resource_debug': False,
            'enable_backup_debug': True,
            'max_log_size_mb': 100,
            'last_modified': datetime.now().isoformat()
        }
    
    @property
    def debug_mode(self):
        """Режим отладки"""
        return self.config.get('debug_mode', False)
    
    @debug_mode.setter
    def debug_mode(self, value):
        """Устанавливает режим отладки"""
        self.config['debug_mode'] = value
        self.save_config()
    
    def enable_debug(self):
        """Включает отладку"""
        self.debug_mode = True
        self.update_logging()
    
    def disable_debug(self):
        """Выключает отладку"""
        self.debug_mode = False
        self.update_logging()
    
    def update_logging(self):
        """Обновляет настройки логирования на основе конфигурации"""
        import logging
        
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
    
    def get_debug_info(self):
        """Возвращает информацию о настройках отладки"""
        return {
            'debug_mode': self.debug_mode,
            'log_level': 'DEBUG' if self.debug_mode else 'INFO',
            'ssh_debug': self.config.get('enable_ssh_debug', False),
            'resource_debug': self.config.get('enable_resource_debug', False),
            'backup_debug': self.config.get('enable_backup_debug', True),
            'max_log_size': self.config.get('max_log_size_mb', 100),
            'last_modified': self.config.get('last_modified')
        }

# Глобальный экземпляр конфигурации отладки
debug_config = DebugConfig()

# Глобальная переменная для быстрого доступа
DEBUG_MODE = debug_config.debug_mode
