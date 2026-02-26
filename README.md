# рџ›°пёЏ Monitoring: Telegram/TamTam-Р±РѕС‚ Рё РїР»Р°С‚С„РѕСЂРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ

**Monitoring** вЂ” СЌС‚Рѕ РјРѕРґСѓР»СЊРЅР°СЏ СЃРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° РёРЅС„СЂР°СЃС‚СЂСѓРєС‚СѓСЂС‹ СЃ СѓРїСЂР°РІР»РµРЅРёРµРј С‡РµСЂРµР· Telegram/TamTam-Р±РѕС‚РѕРІ, CLI-РїСЂРѕРІРµСЂРєР°РјРё Рё РѕРїС†РёРѕРЅР°Р»СЊРЅС‹Рј РІРµР±вЂ‘РёРЅС‚РµСЂС„РµР№СЃРѕРј. РџСЂРѕРµРєС‚ СѓРјРµРµС‚ РѕС‚СЃР»РµР¶РёРІР°С‚СЊ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ, СЂРµСЃСѓСЂСЃС‹, Р±СЌРєР°РїС‹ Рё СЃРѕР±С‹С‚РёСЏ РёР· РїРѕС‡С‚РѕРІС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№, Р° С‚Р°РєР¶Рµ РѕС‚РїСЂР°РІР»СЏС‚СЊ Р°Р»РµСЂС‚С‹ РІ С‡Р°С‚.

## вњЁ РљР»СЋС‡РµРІС‹Рµ РІРѕР·РјРѕР¶РЅРѕСЃС‚Рё

- **РњРѕРЅРёС‚РѕСЂРёРЅРі РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё**: Ping, SSH, RDP, TCP-РїРѕСЂС‚С‹.  
- **РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ**: CPU, RAM, Disk, Load Average, Uptime (РїСЂРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё).  
- **РўРѕС‡РµС‡РЅС‹Рµ РїСЂРѕРІРµСЂРєРё**: РѕРґРёРЅРѕС‡РЅС‹Р№ СЃРµСЂРІРµСЂ, СЂРµР¶РёРјС‹ `availability` Рё `resources`.  
- **РђР»РµСЂС‚С‹ Рё С‚РёС…РёР№ СЂРµР¶РёРј**: РіРёР±РєРёРµ РїРѕСЂРѕРіРё, СЂР°СЃРїРёСЃР°РЅРёРµ С‚РёС€РёРЅС‹.  
- **РћС‚С‡С‘С‚С‹**: СѓС‚СЂРµРЅРЅРёРµ РѕС‚С‡С‘С‚С‹ Рё СЃС‚Р°С‚РёСЃС‚РёРєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°.  
- **Р‘СЌРєР°РїС‹**: Proxmox, Р‘Р”, ZFS (РїРѕ e-mail СѓРІРµРґРѕРјР»РµРЅРёСЏРј).  
- **РџРѕС‡С‚РѕРІС‹Рµ СЃРѕР±С‹С‚РёСЏ**: СЂР°Р·Р±РѕСЂ РїРѕС‡С‚С‹ Рё Р°РІС‚РѕРјР°С‚РёР·Р°С†РёСЏ РїРѕ С€Р°Р±Р»РѕРЅР°Рј.  
- **Р Р°СЃС€РёСЂРµРЅРёСЏ**: РІРєР»СЋС‡Р°РµРјС‹Рµ РјРѕРґСѓР»Рё Р±РµР· РёР·РјРµРЅРµРЅРёР№ РєРѕРґР°.  
- **CLIвЂ‘СЂРµР¶РёРј**: Р±С‹СЃС‚СЂС‹Рµ РїСЂРѕРІРµСЂРєРё Р±РµР· Р·Р°РїСѓСЃРєР° Р±РѕС‚Р°.  
- **Р’РµР±вЂ‘РїР°РЅРµР»СЊ**: Р·Р°РїСѓСЃРє РїСЂРѕРІРµСЂРѕРє Рё РѕС‚С‡С‘С‚РѕРІ РёР· Р±СЂР°СѓР·РµСЂР°.  

## рџ§± РђСЂС…РёС‚РµРєС‚СѓСЂР° РїСЂРѕРµРєС‚Р°

```
core/        вЂ” СЏРґСЂРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіР° Рё РјР°СЂС€СЂСѓС‚РёР·Р°С†РёСЏ Р·Р°РґР°С‡
bot/         вЂ” Telegram/TamTam-Р±РѕС‚С‹, РєРѕРјР°РЅРґС‹ Рё РјРµРЅСЋ
modules/     вЂ” С„РѕРЅРѕРІС‹Рµ РјРѕРґСѓР»Рё (СЂРµСЃСѓСЂСЃС‹, РѕС‚С‡С‘С‚С‹, РїРѕС‡С‚Р°)
extensions/ вЂ” СЂР°СЃС€РёСЂРµРЅРёСЏ (Р±СЌРєР°РїС‹, РІРµР±, РїСЂРѕРІРµСЂРєРё)
config/      вЂ” РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ Рё Р·РЅР°С‡РµРЅРёСЏ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
lib/         вЂ” СЃР»СѓР¶РµР±РЅС‹Рµ СѓС‚РёР»РёС‚С‹, Р»РѕРіРёСЂРѕРІР°РЅРёРµ, Р°Р»РµСЂС‚С‹
```

## вњ… РўСЂРµР±РѕРІР°РЅРёСЏ

- **Python 3.9+**
- Linux (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ Ubuntu/Debian)
- Telegram Bot Token
- TamTam Bot Token (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)

РћРїС†РёРѕРЅР°Р»СЊРЅРѕ:
- **Flask + WebSocket** вЂ” РґР»СЏ РІРµР±вЂ‘РїР°РЅРµР»Рё.
- **pywinrm / wmi** вЂ” РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° Windows.
- **xlrd** вЂ” РґР»СЏ С‡С‚РµРЅРёСЏ С„Р°Р№Р»РѕРІ `.xls` (РµСЃР»Рё РЅСѓР¶РЅС‹ РёРјРµРЅРЅРѕ СЃС‚Р°СЂС‹Рµ ExcelвЂ‘С„Р°Р№Р»С‹).
- **xlwt** вЂ” РґР»СЏ Р·Р°РїРёСЃРё С„Р°Р№Р»РѕРІ `.xls`.
- **openpyxl** вЂ” РґР»СЏ С‡С‚РµРЅРёСЏ С„Р°Р№Р»РѕРІ `.xlsx`.

## вљ™пёЏ Р‘С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚

### 1. РЈСЃС‚Р°РЅРѕРІРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 2. РљР»РѕРЅРёСЂРѕРІР°РЅРёРµ
```bash
git clone https://github.com/sukhanovai/monitoring.git
cd monitoring
```

### 3. Р’РёСЂС‚СѓР°Р»СЊРЅРѕРµ РѕРєСЂСѓР¶РµРЅРёРµ
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Р‘Р°Р·РѕРІР°СЏ РЅР°СЃС‚СЂРѕР№РєР°

РњРёРЅРёРјР°Р»СЊРЅС‹Р№ РЅР°Р±РѕСЂ РЅР°СЃС‚СЂРѕРµРє Р·Р°РґР°С‘С‚СЃСЏ РІ `config/settings.py`:

```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_IDS = ["123456789"]
TAMTAM_TOKEN = "YOUR_TAMTAM_BOT_TOKEN"
TAMTAM_CHAT_IDS = ["<chat_id>"]
```

> РџРѕСЃР»Рµ РїРµСЂРІРѕРіРѕ Р·Р°РїСѓСЃРєР° РЅР°СЃС‚СЂРѕР№РєРё Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ РІ `data/settings.db`.  
> РџСЂРё РЅР°Р»РёС‡РёРё Р·РЅР°С‡РµРЅРёР№ РІ Р‘Р” РѕРЅРё РёРјРµСЋС‚ РїСЂРёРѕСЂРёС‚РµС‚ РЅР°Рґ `config/settings.py`.

### 5. РџРѕР»СѓС‡РµРЅРёРµ Chat ID

РћС‚РїСЂР°РІСЊС‚Рµ Р»СЋР±РѕРµ СЃРѕРѕР±С‰РµРЅРёРµ Р±РѕС‚Сѓ Рё РІС‹РїРѕР»РЅРёС‚Рµ:
```bash
curl "https://api.telegram.org/bot<Р’РђРЁ_РўРћРљР•Рќ>/getUpdates"
```
РќР°Р№РґРёС‚Рµ:
```json
"chat": {"id": 123456789}
```


### 5.1 РџРѕР»СѓС‡РµРЅРёРµ TamTam Chat ID

1. РЎРѕР·РґР°Р№С‚Рµ Р±РѕС‚Р° С‡РµСЂРµР· [@BotFather РІ TamTam](https://tt.me/BotFather).
2. Р”РѕР±Р°РІСЊС‚Рµ Р±РѕС‚Р° РІ РЅСѓР¶РЅС‹Р№ С‡Р°С‚.
3. Р’С‹РїРѕР»РЅРёС‚Рµ Р·Р°РїСЂРѕСЃ Рє API:
```bash
curl "https://botapi.tamtam.chat/updates?access_token=<Р’РђРЁ_TAMTAM_РўРћРљР•Рќ>"
```
4. РќР°Р№РґРёС‚Рµ `recipient.chat_id` Рё РґРѕР±Р°РІСЊС‚Рµ РµРіРѕ РІ `TAMTAM_CHAT_IDS`.

### 6. Р—Р°РїСѓСЃРє

РћСЃРЅРѕРІРЅРѕР№ РјРѕРЅРёС‚РѕСЂРёРЅРі:
```bash
python main.py
```

РњРѕРЅРёС‚РѕСЂРёРЅРі РїРѕС‡С‚С‹ (РµСЃР»Рё РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ):
```bash
python -m modules.improved_mail_monitor
```

## рџ”§ РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ

- `MONITORING_BASE_DIR` вЂ” Р±Р°Р·РѕРІС‹Р№ РєР°С‚Р°Р»РѕРі РґР°РЅРЅС‹С…/Р»РѕРіРѕРІ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РєРѕСЂРµРЅСЊ РїСЂРѕРµРєС‚Р°).
- `MONITORING_MAILDIR_BASE` вЂ” РїСѓС‚СЊ Рє Maildir РґР»СЏ РїРѕС‡С‚РѕРІРѕРіРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіР° (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ `/root/Maildir`).

## рџ§Є CLIвЂ‘СЂРµР¶РёРј

РџСЂРѕРІРµСЂРєРё Р±РµР· Р·Р°РїСѓСЃРєР° Р±РѕС‚Р°:
```bash
python main.py --check availability
python main.py --check resources
python main.py --check targeted_checks --server 192.168.6.00 --mode resources
```

Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ:
- `--server` вЂ” IP/РёРјСЏ СЃРµСЂРІРµСЂР° РґР»СЏ С‚РѕС‡РµС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё.
- `--mode` вЂ” `availability` / `resources`.
- `--reload-servers` вЂ” РїРµСЂРµС‡РёС‚Р°С‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РїРµСЂРµРґ РїСЂРѕРІРµСЂРєРѕР№.
- `--dry-run` вЂ” Р·Р°РїСѓСЃРє Р±РµР· СЃРµС‚Рё Рё Telegram.

## рџ¤– РљРѕРјР°РЅРґС‹ Р±РѕС‚Р°

Р‘Р°Р·РѕРІС‹Рµ:
- `/start` вЂ” РіР»Р°РІРЅРѕРµ РјРµРЅСЋ.
- `/check` вЂ” Р±С‹СЃС‚СЂР°СЏ РїСЂРѕРІРµСЂРєР° СЃРµСЂРІРµСЂРѕРІ.
- `/status` вЂ” СЃС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°.
- `/servers` вЂ” СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ.
- `/report` вЂ” СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡С‘С‚.
- `/stats` вЂ” СЃС‚Р°С‚РёСЃС‚РёРєР°.
- `/control` вЂ” СѓРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј.
- `/silent` вЂ” С‚РёС…РёР№ СЂРµР¶РёРј.
- `/extensions` вЂ” СѓРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё.
- `/settings` вЂ” СѓРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё.
- `/check_server` вЂ” РїСЂРѕРІРµСЂРєР° РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°.
- `/check_res` вЂ” СЂРµСЃСѓСЂСЃС‹ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°.

TamTam (С‚РµРєСЃС‚РѕРІС‹Рµ РєРѕРјР°РЅРґС‹):
- `/help`, `/status`, `/check`, `/resources`.
- `/check_server <IP|РёРјСЏ>`.
- `/monitor_on`, `/monitor_off`.
- `/silent_on`, `/silent_off`.

РљРѕРјР°РЅРґС‹ Р±СЌРєР°РїРѕРІ (РїСЂРё Р°РєС‚РёРІРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёСЏС…):
- `/backup`, `/backup_search`, `/backup_help` вЂ” Proxmox.
- `/db_backups` вЂ” Р±СЌРєР°РїС‹ Р‘Р”.

## рџ§© Р Р°СЃС€РёСЂРµРЅРёСЏ

Р Р°СЃС€РёСЂРµРЅРёСЏ РІРєР»СЋС‡Р°СЋС‚СЃСЏ С‡РµСЂРµР· РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ Рё РјРµРЅСЋ Р±РѕС‚Р°. РџСЂРёРјРµСЂ СЃС‚СЂСѓРєС‚СѓСЂС‹:

```python
AVAILABLE_EXTENSIONS = {
    "backup_monitor": {"name": "рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox", "enabled_by_default": True},
    "database_backup_monitor": {"name": "рџ—ѓпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Р‘Р”", "enabled_by_default": True},
    "zfs_monitor": {"name": "рџ§Љ РњРѕРЅРёС‚РѕСЂРёРЅРі ZFS", "enabled_by_default": True},
    "resource_monitor": {"name": "рџ’» РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ", "enabled_by_default": True},
    "web_interface": {"name": "рџЊђ Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ", "enabled_by_default": True},
    "email_processor": {"name": "рџ“§ РћР±СЂР°Р±РѕС‚РєР° РїРѕС‡С‚С‹", "enabled_by_default": True}
}
```


## рџ“± Android-РєР»РёРµРЅС‚

Р’ СЂРµРїРѕР·РёС‚РѕСЂРёРё РґРѕР±Р°РІР»РµРЅ Android-РїСЂРѕРµРєС‚ `android-client/` (Kotlin + Compose), РєРѕС‚РѕСЂС‹Р№ СЂР°Р±РѕС‚Р°РµС‚ СЃ BFF API РїРѕ Р°РґСЂРµСЃСѓ `https://api.202020.ru:8443` Рё РЅРµ Р»РѕРјР°РµС‚ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ Telegram-РєР°РЅР°Р» СѓРїСЂР°РІР»РµРЅРёСЏ.

РџРѕРґСЂРѕР±РЅР°СЏ РїРѕС€Р°РіРѕРІР°СЏ РёРЅСЃС‚СЂСѓРєС†РёСЏ РґР»СЏ Р·Р°РїСѓСЃРєР° Рё РґРѕСЂР°Р±РѕС‚РєРё: `docs/android_mobile_app.md`.

## рџЊђ Р’РµР±вЂ‘РёРЅС‚РµСЂС„РµР№СЃ

Р•СЃР»Рё РІРєР»СЋС‡РµРЅРѕ СЂР°СЃС€РёСЂРµРЅРёРµ `web_interface`, РїР°РЅРµР»СЊ Р±СѓРґРµС‚ РґРѕСЃС‚СѓРїРЅР° РїРѕ Р°РґСЂРµСЃСѓ:

```
http://<YOUR_IP>:5000
```

Р’ РёРЅС‚РµСЂС„РµР№СЃРµ РјРѕР¶РЅРѕ Р·Р°РїСѓСЃРєР°С‚СЊ РїСЂРѕРІРµСЂРєСѓ СЂРµСЃСѓСЂСЃРѕРІ Рё С„РѕСЂРјРёСЂРѕРІР°С‚СЊ СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡С‘С‚.

## рџљЂ ProductionвЂ‘СЂР°Р·РІС‘СЂС‚С‹РІР°РЅРёРµ (systemd)

### 1. РћСЃРЅРѕРІРЅРѕР№ СЃРµСЂРІРёСЃ

РЎРѕР·РґР°Р№С‚Рµ unit:
```bash
sudo nano /etc/systemd/system/server-monitor.service
```

РџСЂРёРјРµСЂ (РїРѕРґ С‚РµРєСѓС‰РёР№ production-РїСЂРѕС„РёР»СЊ СЃ `proxychains4`):
```ini
[Unit]
Description=Server Monitoring Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
Environment=PYTHONUNBUFFERED=1
Environment="MOBILE_DEFAULT_TOKEN=CHANGE_ME_STRONG_BOOTSTRAP_TOKEN"
Environment="MOBILE_SESSION_TOKEN_TTL_SEC=0"

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/usr/bin/proxychains4 -q /opt/monitoring/venv/bin/python /opt/monitoring/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

РђР»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РІР°СЂРёР°РЅС‚ Р±РµР· `proxychains4`:
```ini
[Unit]
Description=Server Monitoring Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
Environment=PYTHONUNBUFFERED=1
Environment="MOBILE_DEFAULT_TOKEN=CHANGE_ME_STRONG_BOOTSTRAP_TOKEN"
Environment="MOBILE_SESSION_TOKEN_TTL_SEC=0"

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

РџРѕСЏСЃРЅРµРЅРёРµ РїРѕ Android-С‚РѕРєРµРЅР°Рј:
- `MOBILE_DEFAULT_TOKEN` вЂ” bootstrap-С‚РѕРєРµРЅ РґР»СЏ РїРµСЂРІРёС‡РЅРѕР№ Р°РІС‚РѕСЂРёР·Р°С†РёРё Android-РєР»РёРµРЅС‚Р°.
- `MOBILE_SESSION_TOKEN_TTL_SEC` вЂ” TTL СЂР°Р±РѕС‡РёС… С‚РѕРєРµРЅРѕРІ, РєРѕС‚РѕСЂС‹Рµ СЃРµСЂРІРµСЂ РІС‹РґР°РµС‚ РїСЂРёР»РѕР¶РµРЅРёСЋ РїРѕСЃР»Рµ bootstrap:
  - `0` = Р±РµСЃСЃСЂРѕС‡РЅРѕ,
  - `>0` = РІСЂРµРјСЏ Р¶РёР·РЅРё РІ СЃРµРєСѓРЅРґР°С….

РЎРіРµРЅРµСЂРёСЂРѕРІР°С‚СЊ `MOBILE_DEFAULT_TOKEN` РјРѕР¶РЅРѕ РєРѕРјР°РЅРґРѕР№:
```bash
python scripts/generate_mobile_default_token.py
```

Р РµРєРѕРјРµРЅРґСѓРµРјС‹Р№ РїРѕС‚РѕРє:
1. Р’ РїСЂРёР»РѕР¶РµРЅРёРё РІ РїРѕР»Рµ Bearer С‚РѕРєРµРЅР° РІСЃС‚Р°РІР»СЏРµС‚СЃСЏ `MOBILE_DEFAULT_TOKEN`.
2. РџСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё С‚РѕРєРµРЅР° Android РІС‹Р·С‹РІР°РµС‚ `POST /v1/auth/token`.
3. РЎРµСЂРІРµСЂ РІС‹РґР°РµС‚ РЅРѕРІС‹Р№ СЂР°Р±РѕС‡РёР№ С‚РѕРєРµРЅ, СЃРѕС…СЂР°РЅСЏРµС‚ РµРіРѕ РІ `settings.db` Рё РїСЂРёР»РѕР¶РµРЅРёРµ СЃРѕС…СЂР°РЅСЏРµС‚ РµРіРѕ Р»РѕРєР°Р»СЊРЅРѕ.
4. Р”Р°Р»РµРµ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ С‚РѕР»СЊРєРѕ СЂР°Р±РѕС‡РёР№ С‚РѕРєРµРЅ.

РџРµСЂРµРІС‹РїСѓСЃРє С‚РѕРєРµРЅР° (РЅР°РїСЂРёРјРµСЂ, РїРѕСЃР»Рµ РїРµСЂРµСѓСЃС‚Р°РЅРѕРІРєРё РїСЂРёР»РѕР¶РµРЅРёСЏ):
```bash
curl -k -X POST "https://<host>/v1/auth/token/reissue" \
  -H "Authorization: Bearer <MOBILE_DEFAULT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"android-device-1","subject":"android-client","reissue":true}'
```

РђРєС‚РёРІРёСЂСѓР№С‚Рµ:
```bash
sudo systemctl daemon-reload
sudo systemctl enable server-monitor
sudo systemctl start server-monitor
```

### 2. РџРѕС‡С‚РѕРІС‹Р№ РјРѕРЅРёС‚РѕСЂ (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)

Р•СЃР»Рё РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РїРѕС‡С‚РѕРІС‹Р№ РјРѕРґСѓР»СЊ:

```bash
sudo nano /etc/systemd/system/mail-monitor.service
```

```ini
[Unit]
Description=Proxmox Backup Mail Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/usr/bin/proxychains4 -q /opt/monitoring/venv/bin/python /opt/monitoring/modules/mail_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

РђР»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РІР°СЂРёР°РЅС‚ Р±РµР· `proxychains4`:
```ini
[Unit]
Description=Proxmox Backup Mail Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/modules/mail_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

РђРєС‚РёРІР°С†РёСЏ:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mail-monitor
sudo systemctl start mail-monitor
```

### 3. РџСЂРѕРІРµСЂРєР° СЃС‚Р°С‚СѓСЃР°
```bash
systemctl status server-monitor.service
systemctl status mail-monitor.service
```

## вњ… Р”РёР°РіРЅРѕСЃС‚РёРєР°

РџСЂРѕРІРµСЂРєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё:
```bash
python -c "import config; print('вњ… РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р·Р°РіСЂСѓР¶РµРЅР°')"
```

РџСЂРѕРІРµСЂРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№:
```bash
python -c "import flask, telegram, paramiko; print('вњ… Р—Р°РІРёСЃРёРјРѕСЃС‚Рё OK')"
```

## рџ“„ Р›РёС†РµРЅР·РёСЏ

MIT License вЂ” РїРѕРґСЂРѕР±РЅРµРµ РІ [LICENSE](LICENSE).

## Versioning

This project uses Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible API/behavior changes.
- `MINOR`: backward-compatible features.
- `PATCH`: backward-compatible fixes.

Release notes are tracked in `CHANGELOG.md`.
