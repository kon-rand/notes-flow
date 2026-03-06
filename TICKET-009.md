# TICKET-009: Тестирование и полировка

## Описание задачи
Провести тестирование всех компонентов, исправить ошибки, добавить обработку edge cases и завершить реализацию бота.

## Компоненты для реализации
- Тестирование всех модулей
- Обработка ошибок и edge cases
- Улучшение UX и отчётов
- Финальная полировка

## Приоритет
🟡 Высокий

## Критерии приёмки
- [ ] Все модули проходят тестирование
- [ ] Обработка ошибок при недоступности Ollama
- [ ] Обработка пустых инбоксов
- [ ] Корректная работа с большими сообщениями
- [ ] Обработка пересылок без информации об авторе
- [ ] Graceful handling ошибок FileManager
- [ ] Все команды работают корректно
- [ ] Инбокс очищается после саммаризации
- [ ] Статистика в /start показывается корректно

## Технические детали

### Обработка ошибок в OllamaClient
```python
async def summarize_group(self, messages: List[InboxMessage]) -> Dict[str, Any]:
    """Анализ группы сообщений через Ollama"""
    try:
        messages_text = self._format_messages(messages)
        prompt = await self._build_prompt(messages_text)
        
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.config.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60.0
        )
        
        if response.status_code != 200:
            return {"action": "skip"}
        
        result = response.json()
        return self._parse_response(result["response"])
    
    except httpx.ConnectError:
        # Ollama недоступен
        return {"action": "skip"}
    except httpx.TimeoutException:
        # Timeout запроса
        return {"action": "skip"}
    except Exception as e:
        # Любая другая ошибка
        return {"action": "skip"}
```

### Обработка ошибок в FileManager
```python
class FileManager:
    @staticmethod
    def append_message(user_id: int, message: InboxMessage) -> bool:
        """Добавить сообщение в инбокс"""
        try:
            # Создать директорию пользователя если нет
            user_dir = Path(f"data/{user_id}")
            user_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = user_dir / "inbox.md"
            
            # Чтение существующих данных
            data = FileManager._read_yaml_file(file_path)
            
            # Добавление нового сообщения
            data["messages"].append(message.model_dump())
            
            # Запись
            FileManager._write_yaml_file(file_path, data)
            return True
        
        except Exception as e:
            # Логирование ошибки
            print(f"Error appending message: {e}")
            return False
    
    @staticmethod
    def read_messages(user_id: int) -> List[InboxMessage]:
        """Читать все сообщения"""
        try:
            file_path = Path(f"data/{user_id}/inbox.md")
            
            if not file_path.exists():
                return []
            
            data = FileManager._read_yaml_file(file_path)
            return [InboxMessage(**msg) for msg in data.get("messages", [])]
        
        except Exception as e:
            print(f"Error reading messages: {e}")
            return []
```

### Обработка пересылок без информации об авторе
```python
if isinstance(forward_origin, ForwardOriginHiddenUser):
    # Пересылка от скрытого пользователя (канал)
    forward_author_id = forward_origin.sender_id
    # sender_name может быть None для каналов
    sender_name = forward_origin.sender_user.full_name if forward_origin.sender_user else None
    
    inbox_message = InboxMessage(
        id=str(message.message_id),
        timestamp=message.date,
        from_user=user_id,
        sender_id=forward_author_id,
        sender_name=sender_name,  # Может быть None
        content=message.text or str(message.caption) or "",
        chat_id=chat_id
    )
```

### Улучшение отчётов саммаризации
```python
async def auto_summarize(user_id: int):
    """Автоматическая саммаризация"""
    messages = FileManager.read_messages(user_id)
    
    if not messages:
        await send_message(user_id, "📭 Инбокс пуст — нечего саммаризировать")
        return
    
    # ... обработка групп ...
    
    # Улучшенный отчёт
    if tasks_created > 0 or notes_created > 0:
        report = f"""
♻️ Саммаризация завершена!

📊 Результаты:
  ✅ Задачи: {tasks_created}
  📝 Заметки: {notes_created}
  ⏭ Пропущено: {skipped}

📋 Детали:
"""
        for item in report:
            report += f"  • {item}\n"
        
        await send_message(user_id, report)
    else:
        await send_message(user_id, "♻️ Саммаризация завершена — ничего не найдено для сохранения")
```

### Тестовые сценарии
1. **Обработка пустого инбокса** - команда /summarize без сообщений
2. **Пересылка из канала** - ForwardOriginHiddenUser без sender_name
3. **Пересылка из чата** - ForwardOriginChat с sender_title
4. **Большие сообщения** - сообщения > 4096 символов (лимит Telegram)
5. **Ollama недоступен** - обработка ошибок сети
6. **Одновременные сообщения** - проверка работы таймеров
7. **Повторная саммаризация** - корректное добавление задач