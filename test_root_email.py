#!/usr/bin/env python3
"""
Тестирование получения почты на root@help.geltd.local
"""

import subprocess
import sys
import os

sys.path.insert(0, '/opt/monitoring')

def test_email_delivery():
    """Тестирует доставку почты на root"""
    
    print("🧪 Тестирование доставки почты на root@help.geltd.local\n")
    
    # Тестовое письмо от Proxmox
    test_email = """Subject: vzdump backup status (sr-pve4.geltd.local): backup successful
From: root@sr-pve4.localdomain
To: root@help.geltd.local
Date: Tue, 21 Oct 2025 18:35:53 +0700

Backup completed successfully
Duration: 02:15:30
Total size: 145.8GB
VMs: 12 successful, 0 failed
"""
    
    try:
        # Отправляем письмо через обработчик
        result = subprocess.run(
            ['/opt/monitoring/email_processor.py'],
            input=test_email,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ Обработчик успешно обработал тестовое письмо")
            
            # Проверяем логи
            if os.path.exists('/opt/monitoring/logs/email_processor.log'):
                with open('/opt/monitoring/logs/email_processor.log', 'r') as f:
                    logs = f.read()
                    if 'sr-pve4' in logs:
                        print("✅ Письмо от sr-pve4 обнаружено в логах")
                    else:
                        print("❌ Письмо не найдено в логах")
        else:
            print(f"❌ Обработчик завершился с ошибкой: {result.returncode}")
            print(f"STDERR: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"💥 Ошибка тестирования: {e}")
        return False

def check_mail_system():
    """Проверяет почтовую систему"""
    print("\n🔍 Проверка почтовой системы...")
    
    # Проверяем Postfix
    try:
        result = subprocess.run(['systemctl', 'status', 'postfix'], capture_output=True, text=True)
        if 'active (running)' in result.stdout:
            print("✅ Postfix работает")
        else:
            print("❌ Postfix не запущен")
            print(result.stdout)
    except Exception as e:
        print(f"❌ Ошибка проверки Postfix: {e}")
    
    # Проверяем .forward файл
    if os.path.exists('/root/.forward'):
        with open('/root/.forward', 'r') as f:
            content = f.read().strip()
            print(f"✅ .forward файл существует: {content}")
    else:
        print("❌ .forward файл не существует")

def simulate_incoming_email():
    """Имитирует входящее письмо через sendmail"""
    print("\n📨 Имитация входящего письма через sendmail...")
    
    test_email = """Subject: Test backup from pve4
From: root@pve4.localdomain  
To: root@help.geltd.local

This is a test backup email.
Backup status: successful
"""
    
    try:
        # Используем sendmail для отправки тестового письма
        result = subprocess.run(
            ['sendmail', 'root'],
            input=test_email,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ Тестовое письмо отправлено через sendmail")
            
            # Ждем немного для обработки
            import time
            time.sleep(2)
            
            # Проверяем логи
            if os.path.exists('/opt/monitoring/logs/email_processor.log'):
                with open('/opt/monitoring/logs/email_processor.log', 'r') as f:
                    logs = f.read()
                    if 'Test backup' in logs:
                        print("✅ Тестовое письмо обработано")
                    else:
                        print("❌ Тестовое письмо не обработано")
        else:
            print(f"❌ Ошибка отправки: {result.stderr}")
            
    except Exception as e:
        print(f"💥 Ошибка имитации: {e}")

if __name__ == "__main__":
    print("📧 Тестирование почтовой системы для root@help.geltd.local\n")
    
    check_mail_system()
    test_email_delivery() 
    simulate_incoming_email()
    
    print("\n🎯 Инструкция для настройки Proxmox серверов:")
    print("1. На каждом Proxmox сервере выполните:")
    print("   nano /etc/vzdump.conf")
    print("2. Измените строку mailto на:")
    print("   mailto: root@help.geltd.local")
    print("3. Или через веб-интерфейс:")
    print("   Storage → Backup → Mail to: root@help.geltd.local")