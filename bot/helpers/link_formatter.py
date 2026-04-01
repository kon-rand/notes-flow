"""Utilities for formatting links in Telegram messages."""

import re

# Pattern for existing Yandex ticket links in markdown format
YANDEX_TICKET_PATTERN = r'\[([A-Z]+[A-Z0-9-]*[0-9]+)\]\(https://st\.yandex-team\.ru/([A-Z]+[A-Z0-9-]*[0-9]+)\)'

# Pattern for plain ticket numbers (without links)
PLAIN_TICKET_PATTERN = r'\b([A-Z]+[A-Z0-9-]*[0-9]+)\b'


def format_ticket_links(text: str) -> str:
    """
    Add Markdown links to ticket numbers that don't already have links.
    
    Looks for ticket numbers in format like TICKET-123, LAVKAINCIDENTS-1575
    and converts them to Markdown links: [TICKET-123](https://st.yandex-team.ru/TICKET-123)
    
    Args:
        text: Input text with potential ticket numbers.
        
    Returns:
        Text with ticket numbers converted to Markdown links.
    """
    # Find all already-linked tickets
    linked_tickets = set()
    for match in re.finditer(YANDEX_TICKET_PATTERN, text):
        linked_tickets.add(match.group(1).upper())
    
    def replace_ticket(match: re.Match[str]) -> str:
        ticket: str = match.group(1).upper()
        if ticket in linked_tickets:
            return match.group(0)
        return f"[{ticket}](https://st.yandex-team.ru/{ticket})"
    
    result = re.sub(PLAIN_TICKET_PATTERN, replace_ticket, text)
    return result


def format_mentions(text: str) -> str:
    """
    Preserve @username mentions (Telegram auto-links them).
    
    Telegram automatically converts @username to clickable links,
    so no additional formatting is needed.
    
    Args:
        text: Input text with potential @mentions.
        
    Returns:
        Text with @mentions unchanged.
    """
    return text


def escape_markdown(text: str) -> str:
    """
    Escape special Markdown characters for Telegram parse_mode.
    
    Escapes: _ * [ ] ( ) ~ ` > # + - = | { } . !
    
    Args:
        text: Input text to escape.
        
    Returns:
        Text with special Markdown characters escaped.
    """
    # Escape order matters - escape backslash first to avoid double-escaping
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    result = text
    for char in special_chars:
        result = result.replace(char, f'\\{char}')
    return result


if __name__ == "__main__":
    # Examples of usage
    
    # Example 1: Format ticket links
    text1 = "Тикет LAVKAINCIDENTS-1575 требует внимания"
    print("Input:", text1)
    print("Output:", format_ticket_links(text1))
    print()
    
    # Example 2: Already has link - should not duplicate
    text2 = "Ссылка на [LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)"
    print("Input:", text2)
    print("Output:", format_ticket_links(text2))
    print()
    
    # Example 3: Multiple tickets
    text3 = "Задачи TICKET-123 и PROJ-456 нужно решить"
    print("Input:", text3)
    print("Output:", format_ticket_links(text3))
    print()
    
    # Example 4: Mentions - should stay unchanged
    text4 = "Напиши @username по этому вопросу"
    print("Input:", text4)
    print("Output:", format_mentions(text4))
    print()
    
    # Example 5: Escape Markdown
    text5 = "Текст с _underscore_ и *asterisks*"
    print("Input:", text5)
    print("Output:", escape_markdown(text5))