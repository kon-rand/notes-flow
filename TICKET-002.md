# TICKET-002: Обработка сообщений

## Описание задачи
Реализовать обработчик входящих сообщений из Telegram, включая извлечение данных, создание InboxMessage и сохранение в FileManager.

## Компоненты для реализации
- `handlers/messages.py` - message_handler для обработки входящих сообщений
- Интеграция с FileManager.append_message

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] message_handler корректно извлекает user_id из message.from_user.id
- [ ] Обработка пересланных сообщений с извлечением forward_origin
- [ ] Создание InboxMessage с правильными полями
- [ ] Сохранение сообщения в FileManager.append_message(user_id, message)
- [ ] Пересылки корректно идентифицируются (ForwardOriginUser, ForwardOriginHiddenUser, ForwardOriginChat)
- [ ] for from_user = message.from_user.id (тот, кто переслал)
- [ ] for sender_id = forward_author_id (оригинальный автор)
- [ ] for sender_name = имя оригинального автора

## Технические детали

### Обработка обычных сообщений
```python
# handlers/messages.py
async def message_handler(message: Message):
    user_id = message.from_user.id
    
    # Создать InboxMessage
    inbox_message = InboxMessage(
        id=str(message.message_id),
        timestamp=message.date,
        from_user=user_id,
        sender_id=user_id,
        sender_name=message.from_user.full_name if message.from_user else None,
        content=message.text or str(message.caption),
        chat_id=message.chat.id
    )
    
    # Сохранить в FileManager
    FileManager.append_message(user_id, inbox_message)
```

### Обработка пересылок
```python
# handlers/messages.py
async def message_handler(message: Message):
    user_id = message.from_user.id
    
    if message.forward_origin:
        # Определить тип пересылки
        forward_type = message.forward_origin.__class__.__name__
        
        # Извлечь оригинального автора
        if forward_type == "ForwardOriginUser":
            forward_author_id = message.forward_origin.sender_id
            sender_name = message.forward_origin.sender_user.name
        elif forward_type == "ForwardOriginHiddenUser":
            forward_author_id = message.forward_origin.sender_id
            sender_name = message.forward_origin.sender_user.name
        elif forward_type == "ForwardOriginChat":
            forward_author_id = message.forward_origin.chat.id
            sender_name = message.forward_origin.sender_title
        
        # Создать InboxMessage
        inbox_message = InboxMessage(
            id=str(message.message_id),
            timestamp=message.date,
            from_user=user_id,
            sender_id=forward_author_id,
            sender_name=sender_name,
            content=message.text or str(message.caption),
            chat_id=message.chat.id
        )
        
        FileManager.append_message(user_id, inbox_message)
```

### Пример записи в инбокс для пересылки:
```
Пользователь A пересылает сообщение от Пользователя B в бота

Запись в инбокс:
- from_user: A.id
- sender_id: B.id
- sender_name: "B.name"
- content: текст сообщения B
```