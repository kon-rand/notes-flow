from typing import List, Set
import re
import logging

from bot.db.models import InboxMessage

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    @staticmethod
    def group_messages(messages: List[InboxMessage]) -> List[List[InboxMessage]]:
        """Главная функция группировки сообщений"""
        logger.debug(f"🔍 Группировка {len(messages)} сообщений")
        if not messages:
            logger.debug("   ⚠️ Нет сообщений")
            return []
        
        # Сортировка по времени
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        logger.debug(f"   ✓ Отсортировано по времени")
        
        # Группировка по времени
        groups = ContextAnalyzer._group_by_time_window(sorted_messages, window_minutes=30)
        logger.debug(f"   ✓ Временная группировка: {len(groups)} групп")
        
        # Объединение групп по семантике
        groups = ContextAnalyzer._group_by_similarity(groups)
        logger.debug(f"   ✓ Семантическая группировка: {len(groups)} групп")
        
        return groups
    
    @staticmethod
    def _group_by_time_window(messages: List[InboxMessage], window_minutes: int = 30) -> List[List[InboxMessage]]:
        """Группировка по временному окну"""
        logger.debug(f"   ⏰ Временная группировка (окно {window_minutes} мин)")
        if not messages:
            return []
        
        groups = []
        current_group = [messages[0]]
        
        for i in range(1, len(messages)):
            time_diff = (messages[i].timestamp - current_group[0].timestamp).total_seconds() / 60
            
            if time_diff <= window_minutes:
                current_group.append(messages[i])
            else:
                logger.debug(f"      Разделение групп: {len(current_group)} сообщений")
                groups.append(current_group)
                current_group = [messages[i]]
        
        groups.append(current_group)
        logger.debug(f"      Итого групп: {len(groups)}")
        return groups
    
    @staticmethod
    def _group_by_similarity(groups: List[List[InboxMessage]]) -> List[List[InboxMessage]]:
        """Объединение групп по семантической близости"""
        logger.debug(f"   🔀 Семантическая группировка: {len(groups)} групп")
        if len(groups) <= 1:
            logger.debug(f"      Нет групп для объединения")
            return groups
        
        # Извлечение ключевых слов из сообщений
        def get_keywords(text: str) -> Set[str]:
            # Простая токенизация: уникальные слова длиной > 3
            words = re.findall(r'\b\w{3,}\b', text.lower())
            return set(words)
        
        # Проверка на продолжение
        continuation_patterns = [
            r'как\s+я\s+говор',
            r'ещё\s+по\s+теме',
            r'продолж',
            r'связанн',
            r'связано',
            r'относ',
        ]
        
        def is_continuation(current: InboxMessage, previous: InboxMessage) -> bool:
            text = current.content.lower()
            for pattern in continuation_patterns:
                if re.search(pattern, text):
                    return True
            return False
        
        # Объединение соседних групп
        merged = [groups[0]]
        
        for i in range(1, len(groups)):
            prev_group = merged[-1]
            curr_group = groups[i]
            
            # Проверка семантической близости
            prev_keywords = set()
            for msg in prev_group:
                prev_keywords.update(get_keywords(msg.content))
            
            curr_keywords = set()
            for msg in curr_group:
                curr_keywords.update(get_keywords(msg.content))
            
            # ≥ 3 общих слова или обнаружено продолжение
            common = prev_keywords & curr_keywords
            has_continuation = is_continuation(curr_group[0], prev_group[-1])
            
            logger.debug(f"      Группа {i}: {len(common)} общих слов, continuation={has_continuation}")
            
            if len(common) >= 3 or has_continuation:
                merged[-1] = prev_group + curr_group
                logger.debug(f"         ✓ Объединено")
            else:
                merged.append(curr_group)
                logger.debug(f"         ✗ Оставлено отдельно")
        
        logger.debug(f"      Итого после объединения: {len(merged)} групп")
        return merged
    
    @staticmethod
    def detect_continuation(current: InboxMessage, previous: InboxMessage) -> bool:
        """Обнаружение продолжения темы"""
        patterns = [
            r'как\s+я\s+говор',
            r'ещё\s+по\s+теме',
            r'продолж',
            r'связанн',
            r'связано',
            r'относ',
        ]
        
        text = f"{current.content} {previous.content}".lower()
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False