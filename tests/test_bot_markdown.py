"""
Тесты безопасного рендера Markdown в Telegram-меню (`bot/handlers/base.py`).

Регрессия: имя пользователя из Telegram (например логин `ivan_petrov`)
подставлялось в меню как есть, Telegram отвечал «Can't parse entities:
can't find end of the entity starting at byte offset …», и меню вообще не
доходило до пользователя.
"""

from __future__ import annotations

import pytest

from bot.handlers.base import escape_md, render_markdown


class _Query:
    """Заглушка callback_query: считает попытки и режимы разметки."""

    def __init__(self, fail_markdown: bool = False):
        self.fail_markdown = fail_markdown
        self.calls: list[tuple[str, str | None]] = []

    def edit_message_text(self, text, parse_mode=None, reply_markup=None):
        self.calls.append((text, parse_mode))
        if parse_mode == "Markdown" and self.fail_markdown:
            raise RuntimeError(
                "Can't parse entities: can't find end of the entity starting at byte offset 557"
            )


class _Update:
    def __init__(self, query):
        self.callback_query = query
        self.message = None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ivan_petrov", r"ivan\_petrov"),
        ("*bold*", r"\*bold\*"),
        ("code`inject", r"code\`inject"),
        ("[link]", r"\[link]"),
        ("обычное имя", "обычное имя"),
        (None, ""),
        (-1001234567890, "-1001234567890"),
    ],
)
def test_escape_md_escapes_markdown_specials(raw, expected):
    assert escape_md(raw) == expected


def test_render_markdown_sends_with_markup():
    query = _Query()
    render_markdown(_Update(query), "🔔 *Меню*")

    assert query.calls == [("🔔 *Меню*", "Markdown")]


def test_render_markdown_falls_back_to_plain_text():
    """Неразобранная разметка не должна проглатывать всё меню."""
    query = _Query(fail_markdown=True)
    render_markdown(_Update(query), "👥 *Пользователи* ivan_petrov")

    assert [parse_mode for _, parse_mode in query.calls] == ["Markdown", None]
    assert query.calls[-1][0] == "👥 *Пользователи* ivan_petrov"


def test_render_markdown_reraises_other_errors():
    """Остальные ошибки Telegram глушить нельзя — они не про разметку."""

    class _BrokenQuery(_Query):
        def edit_message_text(self, text, parse_mode=None, reply_markup=None):
            raise RuntimeError("Chat not found")

    with pytest.raises(RuntimeError, match="Chat not found"):
        render_markdown(_Update(_BrokenQuery()), "текст")
