"""Tests for bot/helpers/link_formatter.py"""

import pytest
from bot.helpers.link_formatter import (
    format_ticket_links,
    format_mentions,
    escape_markdown
)


@pytest.fixture
def ticket_without_link():
    return "Тикет LAVKAINCIDENTS-1575 требует внимания"


@pytest.fixture
def ticket_with_link():
    return "Ссылка на [LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)"


@pytest.fixture
def multiple_tickets():
    return "Задачи TICKET-123 и PROJ-456 нужно решить"


@pytest.fixture
def mixed_tickets():
    return "Проблема в PROJ-789 и уже исправлено в [TICKET-100](https://st.yandex-team.ru/TICKET-100)"


@pytest.fixture
def text_with_mentions():
    return "Напиши @username по этому вопросу"


@pytest.fixture
def text_with_special_chars():
    return "Текст с _underscore_ и *asterisks* [brackets] (parentheses)"


def test_format_ticket_links_preserves_existing(ticket_with_link):
    result = format_ticket_links(ticket_with_link)
    assert result.count("st.yandex-team.ru/LAVKAINCIDENTS-1575") == 1
    assert "[LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)" in result


def test_format_ticket_links_adds_missing(ticket_without_link):
    result = format_ticket_links(ticket_without_link)
    assert "[LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)" in result


def test_format_ticket_links_multiple(multiple_tickets):
    result = format_ticket_links(multiple_tickets)
    assert "[TICKET-123](https://st.yandex-team.ru/TICKET-123)" in result
    assert "[PROJ-456](https://st.yandex-team.ru/PROJ-456)" in result


def test_format_ticket_links_mixed(mixed_tickets):
    result = format_ticket_links(mixed_tickets)
    assert "[PROJ-789](https://st.yandex-team.ru/PROJ-789)" in result
    assert "[TICKET-100](https://st.yandex-team.ru/TICKET-100)" in result


def test_format_ticket_links_empty():
    result = format_ticket_links("")
    assert result == ""


def test_format_ticket_links_no_tickets():
    text = "Просто обычный текст без тикетов"
    result = format_ticket_links(text)
    assert result == text


def test_format_ticket_links_uppercase():
    text = "TICKET-123 and TICKET-456"
    result = format_ticket_links(text)
    assert "[TICKET-123](https://st.yandex-team.ru/TICKET-123)" in result
    assert "[TICKET-456](https://st.yandex-team.ru/TICKET-456)" in result


def test_format_mentions_unchanged(text_with_mentions):
    result = format_mentions(text_with_mentions)
    assert result == text_with_mentions
    assert "@username" in result


def test_format_mentions_empty():
    result = format_mentions("")
    assert result == ""


def test_format_mentions_multiple():
    text = "Спроси @user1 или @user2 и @user3"
    result = format_mentions(text)
    assert result == text


def test_escape_markdown_underscore():
    text = "text_with_underscore"
    result = escape_markdown(text)
    assert r"\_" in result


def test_escape_markdown_asterisk():
    text = "bold *text*"
    result = escape_markdown(text)
    assert r"\*" in result


def test_escape_markdown_brackets():
    text = "[text](url)"
    result = escape_markdown(text)
    assert r"\[" in result
    assert r"\]" in result
    assert r"\(" in result
    assert r"\)" in result


def test_escape_markdown_special_chars(text_with_special_chars):
    result = escape_markdown(text_with_special_chars)
    assert r"\_" in result
    assert r"\*" in result
    assert r"\[" in result
    assert r"\]" in result
    assert r"\(" in result
    assert r"\)" in result


def test_escape_markdown_empty():
    result = escape_markdown("")
    assert result == ""


def test_escape_markdown_no_special():
    text = "Простой текст без специальных символов"
    result = escape_markdown(text)
    assert result == text


def test_escape_markdown_all_chars():
    text = "_ * [ ] ( ) ~ ` > # + - = | { } . !"
    result = escape_markdown(text)
    assert r"\_" in result
    assert r"\*" in result
    assert r"\[" in result
    assert r"\]" in result
    assert r"\(" in result
    assert r"\)" in result
    assert r"\~" in result
    assert r"\`" in result
    assert r"\>" in result
    assert r"\#" in result
    assert r"\+" in result
    assert r"\-" in result
    assert r"\=" in result
    assert r"\|" in result
    assert r"\{" in result
    assert r"\}" in result
    assert r"\." in result
    assert r"\!" in result


def test_format_ticket_links_ticket_at_start():
    text = "TASK-1 это важно"
    result = format_ticket_links(text)
    assert "[TASK-1](https://st.yandex-team.ru/TASK-1)" in result


def test_format_ticket_links_ticket_at_end():
    text = "Важно для TASK-999"
    result = format_ticket_links(text)
    assert "[TASK-999](https://st.yandex-team.ru/TASK-999)" in result


def test_format_ticket_links_hyphen_in_middle():
    text = "LAVKAINCIDENTS-1575 нужна помощь"
    result = format_ticket_links(text)
    assert "[LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)" in result