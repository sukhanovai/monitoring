"""
/extensions/extension_manager.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Extension Manager for Monitoring
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРµРЅРµРґР¶РµСЂ СЂР°СЃС€РёСЂРµРЅРёР№ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from config.settings import DATA_DIR

# РџСѓС‚СЊ Рє РєР°С‚Р°Р»РѕРіСѓ РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЂР°СЃС€РёСЂРµРЅРёР№
EXTENSIONS_CONFIG_DIR = Path(DATA_DIR) / "extensions"

# РџСѓС‚СЊ Рє С„Р°Р№Р»Сѓ РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЂР°СЃС€РёСЂРµРЅРёР№
EXTENSIONS_CONFIG_FILE = EXTENSIONS_CONFIG_DIR / "extensions_config.json"
LEGACY_EXTENSIONS_CONFIG_FILE = Path(DATA_DIR) / "extensions_config.json"

# РЎРїРёСЃРѕРє РІСЃРµС… РґРѕСЃС‚СѓРїРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№
AVAILABLE_EXTENSIONS = {
    'backup_monitor': {
        'name': 'рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox',
        'description': 'РћС‚СЃР»РµР¶РёРІР°РЅРёРµ СЃС‚Р°С‚СѓСЃР° Р±СЌРєР°РїРѕРІ Proxmox РёР· РїРѕС‡С‚РѕРІС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№',
        'commands': ['/backup', '/backup_search', '/backup_help'],
        'handlers': ['backup_'],
        'enabled_by_default': True,
        'package': 'extensions.backup_monitor'
    },
    'database_backup_monitor': {
        'name': 'рџ—ѓпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Р‘Р”',
        'description': 'РћС‚СЃР»РµР¶РёРІР°РЅРёРµ СЃС‚Р°С‚СѓСЃР° Р±СЌРєР°РїРѕРІ Р±Р°Р· РґР°РЅРЅС‹С…',
        'commands': ['/db_backups'],
        'handlers': ['db_backups_'],
        'enabled_by_default': True,
        'package': 'extensions.server_checks'
    },
    'zfs_monitor': {
        'name': 'рџ§Љ РњРѕРЅРёС‚РѕСЂРёРЅРі ZFS',
        'description': 'РћС‚СЃР»РµР¶РёРІР°РЅРёРµ СЃС‚Р°С‚СѓСЃР° ZFS РјР°СЃСЃРёРІРѕРІ РїРѕ РїРѕС‡С‚РѕРІС‹Рј СѓРІРµРґРѕРјР»РµРЅРёСЏРј',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'mail_backup_monitor': {
        'name': 'рџ“¬ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°',
        'description': 'РћС‚СЃР»РµР¶РёРІР°РЅРёРµ СЂРµР·СѓР»СЊС‚Р°С‚Р° Р±СЌРєР°РїРѕРІ Zimbra РїРѕ РїРѕС‡С‚РѕРІС‹Рј СѓРІРµРґРѕРјР»РµРЅРёСЏРј',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'stock_load_monitor': {
        'name': 'рџ“¦ РњРѕРЅРёС‚РѕСЂРёРЅРі Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ 1РЎ',
        'description': 'Р Р°Р·Р±РѕСЂ Р»РѕРіРѕРІ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ С‚РѕРІР°СЂРѕРІ РёР· РїРѕС‡С‚РѕРІС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'supplier_stock_files': {
        'name': 'рџ“¦ РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ',
        'description': 'РџРѕР»СѓС‡РµРЅРёРµ С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ Рё С„РѕСЂРјРёСЂРѕРІР°РЅРёРµ РѕС‚С‡РµС‚РѕРІ',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'resource_monitor': {
        'name': 'рџ’» РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ',
        'description': 'РџСЂРѕРІРµСЂРєР° Р·Р°РіСЂСѓР·РєРё CPU, RAM Рё РґРёСЃРєРѕРІРѕРіРѕ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР°',
        'commands': ['check_resources', 'check_cpu', 'check_ram', 'check_disk'],
        'handlers': ['check_'],
        'enabled_by_default': True,
        'package': 'extensions.web_interface'
    },
    'web_interface': {
        'name': 'рџЊђ Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ',
        'description': 'Р’РµР±-РїР°РЅРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕ Р°РґСЂРµСЃСѓ http://192.168.20.2:5000',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    },
    'email_processor': {
        'name': 'рџ“§ РћР±СЂР°Р±РѕС‚РєР° РїРѕС‡С‚С‹',
        'description': 'РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РѕР±СЂР°Р±РѕС‚РєР° РїРёСЃРµРј СЃ РѕС‚С‡РµС‚Р°РјРё Рѕ Р±СЌРєР°РїР°С…',
        'commands': [],
        'handlers': [],
        'enabled_by_default': True
    }
}

class ExtensionManager:
    def __init__(self):
        self.config_dir = EXTENSIONS_CONFIG_DIR
        self.config_file = EXTENSIONS_CONFIG_FILE
        self.extensions_config: Dict[str, Dict[str, Any]] = self.load_config()

    def _ensure_config_dir(self) -> None:
        """РЎРѕР·РґР°РµС‚ РєР°С‚Р°Р»РѕРі РґР»СЏ РєРѕРЅС„РёРіРѕРІ СЂР°СЃС€РёСЂРµРЅРёР№ РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё"""
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

    def _build_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Р¤РѕСЂРјРёСЂСѓРµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РґР»СЏ РІСЃРµС… РґРѕСЃС‚СѓРїРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№"""
        return {
            ext_id: {
                'enabled': ext_info.get('enabled_by_default', False),
                'last_modified': datetime.now().isoformat()
            }
            for ext_id, ext_info in AVAILABLE_EXTENSIONS.items()
        }
    
    def load_config(self) -> Dict[str, Dict[str, Any]]:
        """Р—Р°РіСЂСѓР¶Р°РµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ СЂР°СЃС€РёСЂРµРЅРёР№ РёР· С„Р°Р№Р»Р°"""
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
            print(f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЂР°СЃС€РёСЂРµРЅРёР№: {e}")
            return {}
    
    def save_config(self, config: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """РЎРѕС…СЂР°РЅСЏРµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ СЂР°СЃС€РёСЂРµРЅРёР№ РІ С„Р°Р№Р»"""
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
            print(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЂР°СЃС€РёСЂРµРЅРёР№: {e}")
            return False
    
    def get_extension_config_path(self, extension_id: str) -> Path:
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РїСѓС‚СЊ Рє С„Р°Р№Р»Сѓ РєРѕРЅС„РёРіР° РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ"""
        return Path(self.config_dir) / f"{extension_id}.json"

    def load_extension_config(self, extension_id: str) -> Dict[str, Any]:
        """Р—Р°РіСЂСѓР¶Р°РµС‚ РєРѕРЅС„РёРі РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ РёР· РµРіРѕ С„Р°Р№Р»Р°"""
        default_config = AVAILABLE_EXTENSIONS.get(extension_id, {}).get('default_config', {})
        path = self.get_extension_config_path(extension_id)

        try:
            if not path.exists():
                return default_config

            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РєРѕРЅС„РёРіР° РґР»СЏ {extension_id}: {e}")
            return default_config

    def save_extension_config(self, extension_id: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """РЎРѕС…СЂР°РЅСЏРµС‚ РєРѕРЅС„РёРі РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ РІ РµРіРѕ С„Р°Р№Р»"""
        path = self.get_extension_config_path(extension_id)
        try:
            self._ensure_config_dir()
            path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True, f"вњ… РљРѕРЅС„РёРі {extension_id} СЃРѕС…СЂР°РЅРµРЅ"
        except Exception as e:
            return False, f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РєРѕРЅС„РёРіР° {extension_id}: {e}"
    
    def is_extension_enabled(self, extension_id: str) -> bool:
        """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅРѕ Р»Рё СЂР°СЃС€РёСЂРµРЅРёРµ"""
        if extension_id not in self.extensions_config:
            # Р•СЃР»Рё СЂР°СЃС€РёСЂРµРЅРёСЏ РЅРµС‚ РІ РєРѕРЅС„РёРіРµ, РёСЃРїРѕР»СЊР·СѓРµРј Р·РЅР°С‡РµРЅРёРµ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
            return AVAILABLE_EXTENSIONS.get(extension_id, {}).get('enabled_by_default', False)
        
        return self.extensions_config[extension_id].get('enabled', False)
    
    def enable_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Р’РєР»СЋС‡Р°РµС‚ СЂР°СЃС€РёСЂРµРЅРёРµ"""
        if extension_id not in AVAILABLE_EXTENSIONS:
            return False, f"вќЊ Р Р°СЃС€РёСЂРµРЅРёРµ '{extension_id}' РЅРµ РЅР°Р№РґРµРЅРѕ"
        
        if extension_id not in self.extensions_config:
            self.extensions_config[extension_id] = {}
        
        self.extensions_config[extension_id]['enabled'] = True
        self.extensions_config[extension_id]['last_modified'] = datetime.now().isoformat()
        
        if self.save_config():
            return True, f"вњ… Р Р°СЃС€РёСЂРµРЅРёРµ '{AVAILABLE_EXTENSIONS[extension_id]['name']}' РІРєР»СЋС‡РµРЅРѕ"
        else:
            return False, f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РєРѕРЅС„РёРіСѓСЂР°С†РёРё"
    
    def disable_extension(self, extension_id: str) -> Tuple[bool, str]:
        """РћС‚РєР»СЋС‡Р°РµС‚ СЂР°СЃС€РёСЂРµРЅРёРµ"""
        if extension_id not in AVAILABLE_EXTENSIONS:
            return False, f"вќЊ Р Р°СЃС€РёСЂРµРЅРёРµ '{extension_id}' РЅРµ РЅР°Р№РґРµРЅРѕ"
        
        if extension_id not in self.extensions_config:
            self.extensions_config[extension_id] = {}
        
        self.extensions_config[extension_id]['enabled'] = False
        self.extensions_config[extension_id]['last_modified'] = datetime.now().isoformat()
        
        if self.save_config():
            return True, f"вњ… Р Р°СЃС€РёСЂРµРЅРёРµ '{AVAILABLE_EXTENSIONS[extension_id]['name']}' РѕС‚РєР»СЋС‡РµРЅРѕ"
        else:
            return False, f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РєРѕРЅС„РёРіСѓСЂР°С†РёРё"
    
    def toggle_extension(self, extension_id: str) -> Tuple[bool, str]:
        """РџРµСЂРµРєР»СЋС‡Р°РµС‚ СЃРѕСЃС‚РѕСЏРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏ"""
        if self.is_extension_enabled(extension_id):
            return self.disable_extension(extension_id)
        else:
            return self.enable_extension(extension_id)
    
    def get_extensions_status(self) -> Dict[str, Dict[str, Any]]:
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃС‚Р°С‚СѓСЃ РІСЃРµС… СЂР°СЃС€РёСЂРµРЅРёР№"""
        status = {}
        for ext_id in AVAILABLE_EXTENSIONS:
            status[ext_id] = {
                'enabled': self.is_extension_enabled(ext_id),
                'info': AVAILABLE_EXTENSIONS[ext_id]
            }
        return status
    
    def get_enabled_extensions(self) -> List[str]:
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє РІРєР»СЋС‡РµРЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if self.is_extension_enabled(ext_id)]
    
    def get_disabled_extensions(self) -> List[str]:
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє РѕС‚РєР»СЋС‡РµРЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№"""
        return [ext_id for ext_id in AVAILABLE_EXTENSIONS if not self.is_extension_enabled(ext_id)]

    def is_command_available(self, command: str) -> bool:
        """РџСЂРѕРІРµСЂСЏРµС‚, РґРѕСЃС‚СѓРїРЅР° Р»Рё РєРѕРјР°РЅРґР° СЃ СѓС‡РµС‚РѕРј РІРєР»СЋС‡РµРЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            if command in ext_info.get('commands', []) and not self.is_extension_enabled(ext_id):
                return False
        return True

    def is_handler_available(self, handler_pattern: str) -> bool:
        """РџСЂРѕРІРµСЂСЏРµС‚, РґРѕСЃС‚СѓРїРµРЅ Р»Рё РѕР±СЂР°Р±РѕС‚С‡РёРє СЃ СѓС‡РµС‚РѕРј РІРєР»СЋС‡РµРЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№"""
        for ext_id, ext_info in AVAILABLE_EXTENSIONS.items():
            for pattern in ext_info.get('handlers', []):
                if handler_pattern.startswith(pattern) and not self.is_extension_enabled(ext_id):
                    return False
        return True

    def filter_available_commands(self, commands_list: List[str]) -> List[str]:
        """Р¤РёР»СЊС‚СЂСѓРµС‚ СЃРїРёСЃРѕРє РєРѕРјР°РЅРґ, РѕСЃС‚Р°РІР»СЏСЏ С‚РѕР»СЊРєРѕ РґРѕСЃС‚СѓРїРЅС‹Рµ"""
        return [cmd for cmd in commands_list if self.is_command_available(cmd)]

    def should_include_backup_data(self):
        """РџСЂРѕРІРµСЂСЏРµС‚, РЅСѓР¶РЅРѕ Р»Рё РІРєР»СЋС‡Р°С‚СЊ РґР°РЅРЅС‹Рµ Рѕ Р±СЌРєР°РїР°С… РІ РѕС‚С‡РµС‚С‹"""
        return self.is_extension_enabled('backup_monitor')

    def is_web_interface_enabled(self):
        """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃ"""
        return self.is_extension_enabled('web_interface')

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРµРЅРµРґР¶РµСЂР° СЂР°СЃС€РёСЂРµРЅРёР№
extension_manager = ExtensionManager()

def get_enabled_extensions() -> List[str]:
    return extension_manager.get_enabled_extensions()

def register_enabled_extensions(dispatcher: Any) -> None:
    """
    Р РµРіРёСЃС‚СЂРёСЂСѓРµС‚ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РІСЃРµС… РІРєР»СЋС‡РµРЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёР№.
    dispatcher вЂ” СЌС‚Рѕ application.dispatcher / updater.dispatcher (РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ PTB РІРµСЂСЃРёРё).
    """
    enabled = extension_manager.get_enabled_extensions()

    for ext_id in enabled:
        try:
            if ext_id == "backup_monitor":
                from extensions.backup_monitor.bot_handler import register_handlers as reg
                reg(dispatcher)

            # РќР° Р±СѓРґСѓС‰РµРµ:
            # elif ext_id == "web_interface":
            #     from extensions.web_interface.bot_handler import register_handlers as reg
            #     reg(dispatcher)

        except Exception as e:
            # РЅРµ РІР°Р»РёРј РІРµСЃСЊ Р±РѕС‚ РёР·-Р·Р° РѕРґРЅРѕРіРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ
            from lib.logging import debug_log
            debug_log(f"вќЊ РћС€РёР±РєР° СЂРµРіРёСЃС‚СЂР°С†РёРё СЂР°СЃС€РёСЂРµРЅРёСЏ {ext_id}: {e}")
