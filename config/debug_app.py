"""
/config/debug_app.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring system debug configuration
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕС‚Р»Р°РґРєРё СЃРёСЃС‚РµРјС‹ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
"""

import json
from datetime import datetime
from pathlib import Path

try:
    from config.settings import DATA_DIR, DEBUG_CONFIG_FILE
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"
    DEBUG_CONFIG_FILE = DATA_DIR / "debug_config.json"

# РџСѓС‚СЊ Рє С„Р°Р№Р»Сѓ РєРѕРЅС„РёРіСѓСЂР°С†РёРё РѕС‚Р»Р°РґРєРё
DEBUG_CONFIG_FILE = Path(DEBUG_CONFIG_FILE)

class DebugConfig:
    """РљР»Р°СЃСЃ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєР°РјРё РѕС‚Р»Р°РґРєРё"""
    
    def __init__(self):
        self.config_file = DEBUG_CONFIG_FILE
        self.config = self.load_config()
        
    def load_config(self):
        """Р—Р°РіСЂСѓР¶Р°РµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РѕС‚Р»Р°РґРєРё"""
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text(encoding="utf-8"))
            else:
                # РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
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
            print(f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РєРѕРЅС„РёРіСѓСЂР°С†РёРё РѕС‚Р»Р°РґРєРё: {e}")
            return self.get_default_config()
    
    def save_config(self, config=None):
        """РЎРѕС…СЂР°РЅСЏРµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РѕС‚Р»Р°РґРєРё"""
        try:
            if config is None:
                config = self.config
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            config['last_modified'] = datetime.now().isoformat()
            
            self.config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РєРѕРЅС„РёРіСѓСЂР°С†РёРё РѕС‚Р»Р°РґРєРё: {e}")
            return False
    
    def get_default_config(self):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ"""
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
        """Р РµР¶РёРј РѕС‚Р»Р°РґРєРё"""
        return self.config.get('debug_mode', False)
    
    @debug_mode.setter
    def debug_mode(self, value):
        """РЈСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ СЂРµР¶РёРј РѕС‚Р»Р°РґРєРё"""
        self.config['debug_mode'] = value
        self.save_config()
    
    def enable_debug(self):
        """Р’РєР»СЋС‡Р°РµС‚ РѕС‚Р»Р°РґРєСѓ"""
        self.debug_mode = True
        self.update_logging()
    
    def disable_debug(self):
        """Р’С‹РєР»СЋС‡Р°РµС‚ РѕС‚Р»Р°РґРєСѓ"""
        self.debug_mode = False
        self.update_logging()
    
    def update_logging(self):
        """РћР±РЅРѕРІР»СЏРµС‚ РЅР°СЃС‚СЂРѕР№РєРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ РЅР° РѕСЃРЅРѕРІРµ РєРѕРЅС„РёРіСѓСЂР°С†РёРё"""
        import logging
        
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
    
    def get_debug_info(self):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ РЅР°СЃС‚СЂРѕР№РєР°С… РѕС‚Р»Р°РґРєРё"""
        return {
            'debug_mode': self.debug_mode,
            'log_level': 'DEBUG' if self.debug_mode else 'INFO',
            'ssh_debug': self.config.get('enable_ssh_debug', False),
            'resource_debug': self.config.get('enable_resource_debug', False),
            'backup_debug': self.config.get('enable_backup_debug', True),
            'max_log_size': self.config.get('max_log_size_mb', 100),
            'last_modified': self.config.get('last_modified')
        }

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё РѕС‚Р»Р°РґРєРё
debug_config = DebugConfig()

# Р“Р»РѕР±Р°Р»СЊРЅР°СЏ РїРµСЂРµРјРµРЅРЅР°СЏ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РґРѕСЃС‚СѓРїР°
DEBUG_MODE = debug_config.debug_mode
