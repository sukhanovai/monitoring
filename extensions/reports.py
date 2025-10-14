def diagnose_ssh_command(update, context):
    if not context.args:
        update.message.reply_text("❌ Укажите IP или имя сервера: /diagnose_ssh <ip>")
        return
    update.message.reply_text(f"🔧 Диагностика для {context.args[0]} будет доступна после полной настройки")

def diagnose_menu_handler(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔧 Меню диагностики будет доступно после полной настройки")
