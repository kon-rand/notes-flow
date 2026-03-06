# TICKET-008: Обработка пересылок

## Описание задачи
Реализовать корректную обработку пересланных сообщений из Telegram с извлечением информации об оригинальном авторе.

## Компоненты для реализации
- Улучшение `handlers/messages.py` для работы с forward_origin
- Определение типов ForwardOriginUser, ForwardOriginHiddenUser, ForwardOriginChat

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] Извлечение message.forward_origin
- [ ] Определение типа: ForwardOriginUser, ForwardOriginHiddenUser, ForwardOriginChat
- [ ] from_user = message.from_user.id (тот, кто переслал)
- [ ] sender_id = forward_author_id (оригинальный автор)
- [ ] sender_name = имя оригинального автора
- [ ] Корректное сохранение в инбокс с правильными полями
- [ ] Обработка всех типов пересылок

## Технические детали

### Обработка пересылок в handlers/messages.py
```python
from aiogram.types import Message, ForwardOrigin
from aiogram.types.forwarded import ForwardOriginUser, ForwardOriginHiddenUser, ForwardOriginChat

async def message_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверка на пересылку
    if message.forward_origin:
        # Извлечь информацию об оригинальном авторе
        forward_origin = message.forward_origin
        
        # Определение типа пересылки
        if isinstance(forward_origin, ForwardOriginUser):
            # Пересылка от пользователя
            forward_author_id = forward_origin.sender_id
            sender_name = forward_origin.sender_user.full_name
        
        elif isinstance(forward_origin, ForwardOriginHiddenUser):
            # Пересылка от скрытого пользователя (канал/группа)
            forward_author_id = forward_origin.sender_id
            sender_name = forward_origin.sender_user.full_name if forward_origin.sender_user else None
        
        elif isinstance(forward_origin, ForwardOriginChat):
            # Пересылка из чата
            forward_author_id = forward_origin.chat.id
            sender_name = forward_origin.sender_title
        
        else:
            # Неизвестный тип
            forward_author_id = user_id
            sender_name = None
        
        # Создать InboxMessage
        inbox_message = InboxMessage(
            id=str(message.message_id),
            timestamp=message.date,
            from_user=user_id,           # Тот, кто переслал
            sender_id=forward_author_id, # Оригинальный автор
            sender_name=sender_name,     # Имя оригинального автора
            content=message.text or str(message.caption) or "",
            chat_id=chat_id
        )
        
        # Сохранить в FileManager
        FileManager.append_message(user_id, inbox_message)
        
        # Отправить уведомление
        await message.answer(
            f"📩 Пересланное сообщение от {sender_name or 'пользователя'} сохранено"
        )
    
    else:
        # Обычное сообщение
        inbox_message = InboxMessage(
            id=str(message.message_id),
            timestamp=message.date,
            from_user=user_id,
            sender_id=user_id,
            sender_name=message.from_user.full_name if message.from_user else None,
            content=message.text or str(message.caption) or "",
            chat_id=chat_id
        )
        
        FileManager.append_message(user_id, inbox_message)
```

### Пример структуры данных

```
Пользователь A пересылает сообщение от Пользователя B в бота

Запись в инбокс:
- from_user: A.id (тот, кто переслал)
- sender_id: B.id (оригинальный автор)
- sender_name: "B.name" (имя оригинального автора)
- content: текст сообщения B
```

### Типы ForwardOrigin
- **ForwardOriginUser**: Пересылка от пользователя (личное сообщение)
- **ForwardOriginHiddenUser**: Пересылка от скрытого пользователя (канал, анонимный админ)
- **ForwardOriginChat**: Пересылка из чата (группа, канал)
- **ForwardOriginChatAdmin**: Пересылка от администратора чата
- **ForwardOriginUnknown**: Неизвестный тип (редко встречается)