#!/usr/bin/env python3
"""
Тестирование обработки реального письма от sr-pve4
"""

import sys
import os
import subprocess

sys.path.insert(0, '/opt/monitoring')

def test_sr_pve4_email():
    """Тестирует обработку реального письма от sr-pve4"""
    
    print("🧪 Тестирование обработки реального письма от sr-pve4\n")
    
    # Реальное письмо которое вы получили
    real_email = """Return-Path: <root@sr-pve4.localdomain>
Received: from mail.202020.ru (LHLO mail.202020.ru) (192.168.20.49) by
 mail.202020.ru with LMTP; Tue, 21 Oct 2025 18:35:54 +0700 (NOVT)
Received: from localhost (localhost [127.0.0.1])
	by mail.202020.ru (Postfix) with ESMTP id C7B7A655E4E
	for <katok@202020.ru>; Tue, 21 Oct 2025 18:35:53 +0700 (+07)
Received: from mail.202020.ru ([127.0.0.1])
	by localhost (mail.202020.ru [127.0.0.1]) (amavisd-new, port 10032)
	with ESMTP id NCF4DTo9-ANp for <katok@202020.ru>;
	Tue, 21 Oct 2025 18:35:53 +0700 (+07)
Received: from localhost (localhost [127.0.0.1])
	by mail.202020.ru (Postfix) with ESMTP id 9CF72655DEF
	for <katok@202020.ru>; Tue, 21 Oct 2025 18:35:53 +0700 (+07)
X-Virus-Scanned: amavisd-new at 202020.ru
Received: from mail.202020.ru ([127.0.0.1])
	by localhost (mail.202020.ru [127.0.0.1]) (amavisd-new, port 10026)
	with ESMTP id BzkhpSeJm-ic for <katok@202020.ru>;
	Tue, 21 Oct 2025 18:35:53 +0700 (+07)
Received: from sr-pve4.localdomain (pve4.geltd.local [192.168.30.104])
	by mail.202020.ru (Postfix) with ESMTP id 59ED1657FFF
	for <katok@202020.ru>; Tue, 21 Oct 2025 18:35:53 +0700 (+07)
Received: by sr-pve4.localdomain (Postfix, from userid 0)
	id 50BF81040C02; Tue, 21 Oct 2025 18:35:53 +0700 (+07)
Content-Type: multipart/alternative;
	boundary="----_=_NextPart_002_1761046553"
MIME-Version: 1.0
Subject: vzdump backup status (sr-pve4.geltd.local): backup successful
From: vzdump backup tool <root@sr-pve4.localdomain>
To: katok@202020.ru
Date: Tue, 21 Oct 2025 18:35:53 +0700
Auto-Submitted: auto-generated;
Message-Id: <20251021113553.50BF81040C02@sr-pve4.localdomain>

This is a multi-part message in MIME format.

------_=_NextPart_002_1761046553
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Backup completed successfully
Duration: 02:15:30
Total size: 145.8GB
VMs: 12 successful, 0 failed

------_=_NextPart_002_1761046553
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html>
<body>
<h1>Backup Report</h1>
<p>Backup completed successfully</p>
<p>Duration: 02:15:30</p>
<p>Total size: 145.8GB</p>
<p>VMs: 12 successful, 0 failed</p>
</body>
</html>

------_=_NextPart_002_1761046553--
"""
    
    try:
        # Отправляем письмо через обработчик
        result = subprocess.run(
            ['/opt/monitoring/email_processor.py'],
            input=real_email,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        
        print(f"📧 Результат обработки: код {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Письмо успешно обработано")
            
            # Проверяем логи
            if os.path.exists('/opt/monitoring/logs/email_processor.log'):
                with open('/opt/monitoring/logs/email_processor.log', 'r', encoding='utf-8') as f:
                    logs = f.read()
                    if 'sr-pve4' in logs:
                        print("✅ Письмо от sr-pve4 обнаружено в логах")
                    else:
                        print("❌ Письмо от sr-pve4 не найдено в логах")
                        
            # Проверяем базу данных
            check_database()
            
        else:
            print(f"❌ Ошибка обработки: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"💥 Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """Проверяет базу данных"""
    print("\n🔍 Проверка базы данных...")
    
    try:
        from extensions.backup_monitor.bot_handler import BackupMonitorBot
        
        bot = BackupMonitorBot()
        
        # Проверяем различные методы
        today = bot.get_today_status()
        hosts = bot.get_all_hosts()
        recent = bot.get_recent_backups(24)
        
        print(f"📊 Данные за сегодня: {len(today)} записей")
        print(f"🏠 Всего хостов: {len(hosts)}")
        print(f"📅 Последние бэкапы: {len(recent)} записей")
        
        if today:
            print("\n📋 Детали по хостам:")
            for host, status, count, last_report in today:
                print(f"  • {host}: {status} (отчетов: {count})")
                
        # Проверяем конкретно sr-pve4
        sr_pve4_data = [item for item in today if item[0] == 'sr-pve4']
        if sr_pve4_data:
            print(f"\n🎯 sr-pve4 найден в базе: {sr_pve4_data}")
        else:
            print(f"\n❌ sr-pve4 не найден в базе данных")
                
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы: {e}")
        return False

def test_bot_command():
    """Тестирует команду бота"""
    print("\n🤖 Тестирование команды /backup...")
    
    try:
        from extensions.backup_monitor.bot_handler import format_backup_summary, BackupMonitorBot
        
        bot = BackupMonitorBot()
        message = format_backup_summary(bot)
        
        print("📊 Результат команды /backup:")
        print("-" * 50)
        print(message)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка команды бота: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Тестирование обработки реального письма от sr-pve4\n")
    
    # Тестируем обработку письма
    email_processed = test_sr_pve4_email()
    
    # Тестируем команду бота
    if email_processed:
        test_bot_command()
    
    print("\n📝 Следующие шаги:")
    print("1. Настройте Proxmox серверы на отправку напрямую на root@help.geltd.local")
    print("2. Или настройте пересылку с katok@202020.ru на root@help.geltd.local")
    print("3. Проверьте работу команды /backup в боте Telegram")