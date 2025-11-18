# restore_patterns.py
import sqlite3
import json

BACKUP_PATTERNS = {
    "proxmox_subject": [
        r"vzdump backup status \((.+?)\): backup (successful|failed)",
        r"Proxmox Backup (?:Server )?report for (.+?): (success|error)"
    ],
    "hostname_extraction": [
        r"\(([^)]+)\)",
        r"for ([^:]+):"
    ],
    "database": {
        "company": [
            r"sr-bup (.+?) dump complete",
            r"database dump (.+?) completed"
        ],
        "barnaul": [
            r"brn-backup (.+?) backup.*errors: (\d+)",
            r"barnaul backup (.+?).*errors: (\d+)"
        ],
        "client": [
            r"kc-1c (.+?) dump complete", 
            r"client database (.+?) backup"
        ],
        "yandex": [
            r"yandex (.+?) backup",
            r"yandex (.+?) completed"
        ]
    }
}

def restore_patterns():
    conn = sqlite3.connect('/opt/monitoring/data/settings.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) 
        VALUES ('BACKUP_PATTERNS', ?)
    ''', (json.dumps(BACKUP_PATTERNS, ensure_ascii=False),))
    
    conn.commit()
    conn.close()
    print("✅ BACKUP_PATTERNS восстановлены")

if __name__ == "__main__":
    restore_patterns()
    