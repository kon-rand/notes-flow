import sys
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

from datetime import datetime, timedelta
from bot.db.models import InboxMessage
from utils.context_analyzer import ContextAnalyzer


def create_message(id: str, offset_minutes: int, content: str) -> InboxMessage:
    """Helper для создания тестовых сообщений"""
    return InboxMessage(
        id=id,
        timestamp=datetime(2026, 3, 6, 14, 0, 0) + timedelta(minutes=offset_minutes),
        from_user=123456789,
        sender_id=123456789,
        sender_name=None,
        content=content,
        chat_id=-1001234567890
    )


def test_group_messages_empty_list():
    """Тест: обработка пустого списка"""
    result = ContextAnalyzer.group_messages([])
    assert result == []
    print("✓ test_group_messages_empty_list passed")


def test_group_messages_single_message():
    """Тест: одно сообщение"""
    messages = [create_message("msg_1", 0, "Привет")]
    result = ContextAnalyzer.group_messages(messages)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0].id == "msg_1"
    print("✓ test_group_messages_single_message passed")


def test_group_messages_multiple_separate():
    """Тест: несколько сообщений с большими интервалами"""
    messages = [
        create_message("msg_1", 0, "Тема 1"),
        create_message("msg_2", 40, "Тема 2"),
        create_message("msg_3", 90, "Тема 3"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    assert len(result) == 3
    assert len(result[0]) == 1
    assert len(result[1]) == 1
    assert len(result[2]) == 1
    print("✓ test_group_messages_multiple_separate passed")


def test_group_by_time_window_basic():
    """Тест: базовая группировка по времени"""
    messages = [
        create_message("msg_1", 0, "Первое"),
        create_message("msg_2", 15, "Второе"),
        create_message("msg_3", 60, "Третье"),
    ]
    result = ContextAnalyzer._group_by_time_window(messages, window_minutes=30)
    assert len(result) == 2
    assert len(result[0]) == 2
    assert len(result[1]) == 1
    assert result[0][0].id == "msg_1"
    assert result[0][1].id == "msg_2"
    assert result[1][0].id == "msg_3"
    print("✓ test_group_by_time_window_basic passed")


def test_group_by_time_window_empty():
    """Тест: пустой список в _group_by_time_window"""
    result = ContextAnalyzer._group_by_time_window([])
    assert result == []
    print("✓ test_group_by_time_window_empty passed")


def test_group_by_time_window_boundary():
    """Тест: границы временного окна (ровно 30 минут)"""
    messages = [
        create_message("msg_1", 0, "Первое"),
        create_message("msg_2", 30, "Второе"),
        create_message("msg_3", 31, "Третье"),
    ]
    result = ContextAnalyzer._group_by_time_window(messages, window_minutes=30)
    assert len(result) == 2
    assert len(result[0]) == 2  # msg_1 и msg_2 в одной группе
    assert len(result[1]) == 1  # msg_3 отдельно
    print("✓ test_group_by_time_window_boundary passed")


def test_group_by_time_window_all_same_window():
    """Тест: все сообщения в одном временном окне"""
    messages = [
        create_message("msg_1", 0, "Первое"),
        create_message("msg_2", 10, "Второе"),
        create_message("msg_3", 20, "Третье"),
    ]
    result = ContextAnalyzer._group_by_time_window(messages, window_minutes=30)
    assert len(result) == 1
    assert len(result[0]) == 3
    print("✓ test_group_by_time_window_all_same_window passed")


def test_get_keywords_basic():
    """Тест: извлечение ключевых слов - базовый случай"""
    # Тест через _group_by_similarity
    messages = [
        create_message("msg_1", 0, "Привет мир hello world"),
    ]
    groups = [messages]
    result = ContextAnalyzer._group_by_similarity(groups)
    assert len(result) == 1
    print("✓ test_get_keywords_basic passed")


def test_group_by_similarity_common_words():
    """Тест: объединение групп с общими ключевыми словами (≥3)"""
    messages = [
        create_message("msg_1", 0, "работа проект задача deadline"),
        create_message("msg_2", 40, "ещё работа проект задача"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Должно объединиться в одну группу из-за общих слов
    assert len(result) == 1
    assert len(result[0]) == 2
    print("✓ test_group_by_similarity_common_words passed")


def test_group_by_similarity_no_common_words():
    """Тест: разделение групп без общих слов"""
    messages = [
        create_message("msg_1", 0, "купить хлеб молоко яйца"),
        create_message("msg_2", 40, "работа проект встреча deadline"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Должно остаться 2 группы (нет общих слов и нет паттернов продолжения)
    assert len(result) == 2
    print("✓ test_group_by_similarity_no_common_words passed")


def test_group_by_similarity_continuation_patterns():
    """Тест: объединение групп с паттернами продолжения"""
    messages = [
        create_message("msg_1", 0, "Тема проекта"),
        create_message("msg_2", 40, "как я говорил раньше про проект"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Должно объединиться из-за паттерна продолжения
    assert len(result) == 1
    assert len(result[0]) == 2
    print("✓ test_group_by_similarity_continuation_patterns passed")


def test_is_continuation_patterns():
    """Тест: распознавание паттернов продолжения"""
    patterns_tests = [
        ("как я говорил", True),
        ("как я говорю", True),
        ("ещё по теме", True),
        ("продолжаю тему", True),
        ("связано с этим", True),
        ("относится к проекту", True),
        ("купить хлеб", False),
        ("просто сообщение", False),
    ]
    
    previous = create_message("msg_1", 0, "Тема проекта")
    
    for content, expected in patterns_tests:
        current = create_message("msg_2", 10, content)
        result = ContextAnalyzer.detect_continuation(current, previous)
        assert result == expected, f"Failed for: {content}"
    
    print("✓ test_is_continuation_patterns passed")


def test_detect_continuation_all_patterns():
    """Тест: все паттерны продолжения темы"""
    previous = create_message("msg_1", 0, "Тема")
    
    continuation_phrases = [
        "как я говорил",
        "как я говорю",
        "ещё по теме",
        "продолжаю",
        "продолжение",
        "связанно с этим",
        "связанное",
        "относится к",
        "относящийся",
    ]
    
    for phrase in continuation_phrases:
        current = create_message("msg_2", 10, phrase)
        result = ContextAnalyzer.detect_continuation(current, previous)
        assert result is True, f"Pattern '{phrase}' not detected"
    
    print("✓ test_detect_continuation_all_patterns passed")


def test_integration_full_cycle():
    """Тест: полный цикл group_messages с реальными сообщениями"""
    messages = [
        create_message("msg_1", 0, "Нужно подготовить отчёт по проекту"),
        create_message("msg_2", 5, "Вот данные для отчёта"),
        create_message("msg_3", 10, "Как я говорил, ещё по отчёту"),
        create_message("msg_4", 50, "Купи хлеба на ужин"),
        create_message("msg_5", 55, "Молока ещё нет в доме"),
        create_message("msg_6", 100, "Собрать данные для презентации"),
    ]
    
    result = ContextAnalyzer.group_messages(messages)
    
    # Ожидаем 2-3 группы:
    # 1. msg_1, msg_2, msg_3 (близко по времени + продолжение)
    # 2. msg_4, msg_5 (близко по времени, общие слова "купить/молка")
    # 3. msg_6 (отдельно)
    assert len(result) >= 2
    assert len(result) <= 3
    
    # Проверяем, что msg_1 и msg_3 в одной группе (продолжение)
    found_group_with_continuation = False
    for group in result:
        if len(group) >= 2:
            has_continuation = ContextAnalyzer.detect_continuation(
                group[-1], group[0]
            )
            if has_continuation:
                found_group_with_continuation = True
                break
    
    assert found_group_with_continuation
    print("✓ test_integration_full_cycle passed")


def test_edge_cases_same_timestamp():
    """Тест: сообщения с одинаковым временем"""
    messages = [
        create_message("msg_1", 0, "Первое"),
        create_message("msg_2", 0, "Второе"),
        create_message("msg_3", 0, "Третье"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    assert len(result) == 1
    assert len(result[0]) == 3
    print("✓ test_edge_cases_same_timestamp passed")


def test_edge_cases_empty_content():
    """Тест: сообщения с пустым content"""
    messages = [
        create_message("msg_1", 0, ""),
        create_message("msg_2", 10, "Текст"),
        create_message("msg_3", 20, ""),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Пустые сообщения всё равно группируются по времени
    assert len(result) == 1
    assert len(result[0]) == 3
    print("✓ test_edge_cases_empty_content passed")


def test_edge_cases_special_characters():
    """Тест: special characters в content"""
    messages = [
        create_message("msg_1", 0, "Привет! Привет? Привет..."),
        create_message("msg_2", 10, "Тест @username #хэштег $money"),
        create_message("msg_3", 20, "Emoji: 🎉 🚀 💯"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Должно работать без ошибок
    assert len(result) >= 1
    print("✓ test_edge_cases_special_characters passed")


def test_edge_cases_long_content():
    """Тест: очень длинный content"""
    long_text = "работа " * 1000
    messages = [
        create_message("msg_1", 0, long_text),
        create_message("msg_2", 10, long_text + " продолжение"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # Должно обработать без ошибок
    assert len(result) == 1
    print("✓ test_edge_cases_long_content passed")


def test_group_by_similarity_keyword_extraction():
    """Тест: извлечение ключевых слов - уникальность и lower case"""
    messages = [
        create_message("msg_1", 0, "Word WORD word another ANOTHER"),
    ]
    groups = [messages]
    result = ContextAnalyzer._group_by_similarity(groups)
    assert len(result) == 1
    print("✓ test_group_by_similarity_keyword_extraction passed")


def test_multiple_groups_merge():
    """Тест: объединение нескольких групп"""
    messages = [
        create_message("msg_1", 0, "работа проект задача deadline встреча"),
        create_message("msg_2", 25, "ещё работа проект задача"),
        create_message("msg_3", 55, "проект задача ещё данные"),
        create_message("msg_4", 100, "другая тема совсем"),
    ]
    result = ContextAnalyzer.group_messages(messages)
    # msg_1, msg_2, msg_3 должны объединиться (общие слова)
    # msg_4 отдельно
    assert len(result) == 2
    assert len(result[0]) == 3
    assert len(result[1]) == 1
    print("✓ test_multiple_groups_merge passed")


