from types import SimpleNamespace
from unittest.mock import Mock


def test_server_list_paginates_all_actions(monkeypatch):
    from bot.handlers.settings_handlers import _legacy, callback_dispatcher

    servers = [
        {"ip": f"192.0.2.{i + 1}", "name": f"server-{i:02d}", "type": "ssh", "enabled": True}
        for i in range(49)
    ]
    servers[35]["enabled"] = False
    servers[45]["enabled"] = False
    get_servers = Mock(return_value=servers)
    monkeypatch.setattr(_legacy.settings_manager, "get_all_servers", get_servers)
    monkeypatch.setattr(_legacy, "InlineKeyboardButton", lambda text, callback_data: (text, callback_data))
    monkeypatch.setattr(_legacy, "InlineKeyboardMarkup", lambda rows: rows)

    query = Mock(data="settings_servers_list")
    update = SimpleNamespace(callback_query=query)
    context = SimpleNamespace(user_data={})
    seen = []
    for page in range(5):
        callback_dispatcher.settings_callback_handler(update, context)
        args, kwargs = query.edit_message_text.call_args
        assert f"Страница {page + 1} из 5" in args[0]
        buttons = {callback: text for row in kwargs["reply_markup"] for text, callback in row}
        assert len(buttons) <= 35
        for server in servers[page * 10 : (page + 1) * 10]:
            ip = server["ip"]
            assert server["name"] in args[0]
            assert f"settings_edit_server_{ip}" in buttons
            assert f"settings_delete_server_{ip}" in buttons
            assert buttons[f"settings_toggle_server_{ip}"] == (
                "⏸️ Пауза" if server["enabled"] else "▶️ Возобновить"
            )
            seen.append(ip)
        if page:
            assert f"settings_servers_page_{page - 1}" in buttons
        next_callback = f"settings_servers_page_{page + 1}"
        assert (next_callback in buttons) == (page < 4)
        query.data = next_callback

    assert seen == [server["ip"] for server in servers]
    get_servers.assert_called_with(include_disabled=True)
