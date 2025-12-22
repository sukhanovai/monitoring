"""
/app/config/debug.py
Server Monitoring System v4.14.46
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring system debug configuration
Система мониторинга серверов
Версия: 4.14.24
Автор: Александр Суханов (c)
Лицензия: MIT
Конфигурация отладки системы мониторинга
"""

import os
import json
from datetime import datetime

# Путь к файлу конфигурации отладки
DEBUG_CONFIG_FILE = '/opt/monitoring/data/debug_config.json'

class DebugConfig:
    """Класс для управления настройками отладки"""
    
    def __init__(self):
        self.config_file = DEBUG_CONFIG_FILE
        self.config = self.load_config()
        
    def load_config(self):
        """Загружает конфигурацию отладки"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
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
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config['last_modified'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
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
