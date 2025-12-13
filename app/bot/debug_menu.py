"""
Server Monitoring System v4.4.11 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Меню управления отладкой

"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
import subprocess
import socket
from datetime import datetime

class DebugMenu:
    """Меню управления отладкой"""
    
    def __init__(self):
        try:
            from app.config.debug import DEBUG_MODE
            self.debug_mode = DEBUG_MODE
        except ImportError:
            self.debug_mode = False
    
    def __call__(self, update, context):
        """Основной обработчик - вызывает соответствующий метод по callback_data"""
        query = update.callback_query
        if not query:
            return
        
        data = query.data
        print(f"🔧 DebugMenu получил callback: {data}")
        
        if data == 'debug_menu':
            self.show_menu(update, context)
        elif data == 'debug_enable':
            self.enable_debug_mode(query)
        elif data == 'debug_disable':
            self.disable_debug_mode(query)
        elif data == 'debug_status':
            self.show_debug_status(query)
        elif data == 'debug_clear_logs':
            self.clear_debug_logs(query)
        elif data == 'debug_diagnose':
            self.run_diagnostic(query)
        elif data == 'debug_advanced':
            self.show_advanced_debug(query)
        else:
            print(f"❌ Неизвестный debug callback: {data}")
            query.answer(f"Неизвестная команда отладки: {data}")
    
    def show_menu(self, update, context):
        """Показать меню отладки"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        chat_id = query.message.chat_id if query else update.message.chat_id
        
        debug_status = "🟢 ВКЛЮЧЕНА" if self.debug_mode else "🔴 ВЫКЛЮЧЕНА"
        
        message = "🐛 *Управление отладкой*\n\n"
        message += f"*Текущий статус:* {debug_status}\n\n"
        
        toggle_text = "🔴 Выключить отладку" if self.debug_mode else "🟢 Включить отладку"
        toggle_data = 'debug_disable' if self.debug_mode else 'debug_enable'

        keyboard = [
            [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
            [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
            [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
            [InlineKeyboardButton("📋 Диагностика", callback_data='debug_diagnose')],
            [InlineKeyboardButton("🔧 Расширенная отладка", callback_data='debug_advanced')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    def enable_debug_mode(self, query):
        """Включить режим отладки"""
        try:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            
            self.debug_mode = True
            # Обновляем глобальную переменную DEBUG_MODE
            try:
                from app.config import debug as debug_module
                debug_module.DEBUG_MODE = True
                debug_module.save_debug_config()
            except:
                pass
            
            query.answer("🟢 Отладка включена")
            query.edit_message_text(
                "🟢 *Отладка включена*\n\n"
                "Теперь все операции будут детально логироваться.",
                parse_mode='Markdown',
                reply_markup=self._get_back_to_debug_keyboard()
            )
        except Exception as e:
            query.answer(f"❌ Ошибка включения отладки: {e}")
    
    def disable_debug_mode(self, query):
        """Выключить режим отладки"""
        try:
            import logging
            logging.getLogger().setLevel(logging.INFO)
            
            self.debug_mode = False
            # Обновляем глобальную переменную DEBUG_MODE
            try:
                from app.config import debug as debug_module
                debug_module.DEBUG_MODE = False
                debug_module.save_debug_config()
            except:
                pass
            
            query.answer("🔴 Отладка выключена")
            query.edit_message_text(
                "🔴 *Отладка выключена*\n\n"
                "Логирование переведено в стандартный режим.",
                parse_mode='Markdown',
                reply_markup=self._get_back_to_debug_keyboard()
            )
        except Exception as e:
            query.answer(f"❌ Ошибка выключения отладки: {e}")
    
    def show_debug_status(self, query):
        """Показать статус системы для отладки"""
        import platform
        import os
        import psutil
        from datetime import datetime
        
        # Собираем информацию о системе
        system_info = []
        system_info.append(f"🐍 Python: {platform.python_version()}")
        system_info.append(f"💻 OS: {platform.system()} {platform.release()}")
        system_info.append(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Использование ресурсов
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info.append(f"💻 CPU: {cpu_percent}%")
        system_info.append(f"🧠 RAM: {memory.percent}% ({memory.used//1024//1024}МБ/{memory.total//1024//1024}МБ)")
        system_info.append(f"💾 Disk: {disk.percent}% ({disk.used//1024//1024}МБ/{disk.total//1024//1024}МБ)")
        
        # Информация о мониторинге
        try:
            from app.core.monitoring import monitoring_core
            system_info.append(f"📊 Серверов в мониторинге: {len(monitoring_core.servers)}")
            system_info.append(f"🔄 Последняя проверка: {monitoring_core.last_check_time.strftime('%H:%M:%S')}")
        except:
            pass
        
        message = "📊 *Статус системы для отладки*\n\n"
        message += "\n".join([f"• {info}" for info in system_info])
        
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=self._get_back_to_debug_keyboard()
        )
    
    def clear_debug_logs(self, query):
        """Очистить логи отладки"""
        try:
            log_files = [
                '/opt/monitoring/logs/debug.log',
                '/opt/monitoring/bot_debug.log'
            ]
            
            cleared = 0
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'w') as f:
                        f.write('')
                    cleared += 1
            
            query.answer(f"✅ Очищено {cleared} файлов логов")
            query.edit_message_text(
                f"✅ *Логи очищены*\n\nОчищено {cleared} файлов логов.",
                parse_mode='Markdown',
                reply_markup=self._get_back_to_debug_keyboard()
            )
        except Exception as e:
            query.answer(f"❌ Ошибка очистки логов: {e}")
    
    def run_diagnostic(self, query):
        """Запустить диагностику"""
        query.answer("🔧 Запускается диагностика...")
        
        message = "🔧 *Диагностика системы*\n\n"
        
        # Проверяем доступность ключевых модулей
        modules_to_check = [
            ('app.config.settings', 'TELEGRAM_TOKEN'),
            ('app.core.monitoring', 'monitoring_core'),
            ('app.core.checker', 'server_checker'),
            ('extensions.extension_manager', 'extension_manager'),
            ('extensions.server_checks', 'initialize_servers'),
        ]
        
        for module_name, attr_name in modules_to_check:
            try:
                if attr_name:
                    exec(f"from {module_name} import {attr_name}")
                    message += f"✅ {module_name}.{attr_name}\n"
                else:
                    exec(f"import {module_name}")
                    message += f"✅ {module_name}\n"
            except Exception as e:
                message += f"❌ {module_name}: {str(e)[:50]}\n"
        
        message += f"\n🐛 Debug mode: {'🟢 ON' if self.debug_mode else '🔴 OFF'}"
        
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=self._get_back_to_debug_keyboard()
        )
    
    def show_advanced_debug(self, query):
        """Показать расширенное меню отладки"""
        message = "🔧 *Расширенная отладка*\n\n"
        message += "Доступные функции:\n"
        message += "• Проверка соединения с серверами\n"
        message += "• Тест базы данных бэкапов\n"
        message += "• Проверка конфигурации\n"
        message += "• Просмотр логов в реальном времени\n\n"
        message += "🔨 *В разработке*"
        
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=self._get_back_to_debug_keyboard()
        )
    
    def _get_back_to_debug_keyboard(self):
        """Получить клавиатуру для возврата в меню отладки"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад в отладку", callback_data='debug_menu')]
        ])

# Глобальный экземпляр
debug_menu = DebugMenu()

