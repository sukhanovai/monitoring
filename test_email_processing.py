#!/usr/bin/env python3
"""
Тестирование обработки конкретного письма
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

def test_specific_email():
    """Тестирует обработку конкретного письма"""
    
    # Вставьте сюда содержимое письма которое вы переслали
    test_email = """
Return-Path: <>
X-Original-To: backup-monitor@help.sr-goods.geltd.local
Delivered-To: backup-monitor@help.sr-goods.geltd.local
Received: from mail.202020.ru (sr-mail.geltd.local [192.168.20.49])
        by help.sr-goods.geltd.local (Postfix) with ESMTP id ABC123
        for <backup-monitor@help.sr-goods.geltd.local>; Tue, 29 Jul 2025 20:31:11 +0700 (+07)
Content-Type: multipart/alternative;
        boundary="----_=_NextPart_002_1753795870"
MIME-Version: 1.0
Subject: vzdump backup status (pve13.geltd.local): backup successful
From: vzdump backup tool <root@pve13.localdomain>
To: katok@202020.ru
Date: Tue, 29 Jul 2025 20:31:10 +0700

This is a multi-part message in MIME format.

------_=_NextPart_002_1753795870
Content-Type: text/plain;
        charset="UTF-8"
Content-Transfer-Encoding: quoted-printable

Backup completed successfully.
Duration: 01:23:45
Total size: 156.7GB
All VMs backed up without errors.
"""
    
    from extensions.email_processor.core import EmailProcessorCore
    
    print("🧪 Тестирование обработки письма...")
    print("=" * 50)
    
    processor = EmailProcessorCore()
    success = processor.process_email(test_email)
    
    if success:
        print("✅ Письмо успешно обработано!")
        print("📊 Проверьте базу данных:")
        print("   sqlite3 /opt/monitoring/data/backups.db \"SELECT * FROM proxmox_backups ORDER BY received_at DESC LIMIT 1;\"")
    else:
        print("❌ Ошибка обработки письма")
        print("📋 Проверьте логи:")
        print("   tail -f /opt/monitoring/logs/email_processor.log")

if __name__ == "__main__":
    test_specific_email()
    