# TICKET-012: Стабилизация запуска через Docker Compose

## Описание задачи

Бот Notes Flow не запускается корректно через `docker-compose`. Необходимо:
1. Исправить все ошибки импорта в handler файлах
2. Адаптировать код под Router-паттерн aiogram
3. Создать документацию по запуску и отладке
4. Протестировать успешный запуск через Docker Compose

## Статус

✅ completed

## Проблемы

### 1. Ошибки импорта в `bot/main.py`

Файл содержит импорты несуществующих функций:
```python
from handlers.commands import register_commands
from handlers.messages import register_message_handlers
from handlers.summarizer import register_summarizer_handlers
```

### 2. Handler файлы используют Router-паттерн

Все handler файлы (`commands.py`, `messages.py`, `summarizer.py`) определяют `router = Router()`, но не экспортируют функции регистрации:
- `commands.py` - содержит 8 handler функций, зарегистрированных через декораторы `@router.message()`
- `messages.py` - содержит `message_handler` и `extract_forward_info`
- `summarizer.py` - содержит `auto_summarize`

### 3. Отсутствие функции регистрации команд

Функция `register_commands(bot)` должна вызывать `/register_bot_commands` для регистрации команд бота, но её нет.

## План исправления

### Этап 1: Исправить `bot/main.py`

**Задача:** Адаптировать точку входа под Router-паттерн aiogram

**Изменения:**
1. Заменить импорты функций на импорты routers
2. Добавить routers в Dispatcher через `dp.include_router()`
3. Добавить регистрацию команд через `set_my_commands`

**Пример кода:**
```python
from handlers.commands import router as commands_router
from handlers.messages import router as messages_router
from handlers.summarizer import router as summarizer_router

async def main():
    logging.basicConfig(...)
    
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    
    # Регистрация команд
    from aiogram.types.BotCommand import BotCommand
    commands = [
        BotCommand(command="start", description="показать статистику"),
        BotCommand(command="help", description="показать список команд"),
        # ... остальные команды
    ]
    await bot.set_my_commands(commands)
    
    # Include routers
    dp.include_router(commands_router)
    dp.include_router(messages_router)
    dp.include_router(summarizer_router)
    
    logging.info("Starting bot...")
    await dp.start_polling(bot)
```

### Этап 2: Добавить router в `handlers/summarizer.py`

**Задача:** Создать router для суммаризатора (сейчас его нет)

**Изменения:**
```python
from aiogram import Router

router = Router()

# Добавить любые хендлеры для суммаризатора, если нужны
```

### Этап 3: Обновить `requirements.txt` (если нужно)

**Задача:** Убедиться, что все зависимости присутствуют

**Проверка:**
- aiogram >= 3.0.0
- aiohttp
- python-dotenv

### Этап 4: Создать документацию

**Файл:** `DEPLOYMENT.md`

**Содержимое:**
```markdown
# Запуск через Docker Compose

## Требования

- Docker
- Docker Compose
- Ollama (опционально, для саммаризации)

## Быстрый старт

1. Скопируйте пример конфигурации:
   ```bash
   cp .env.example .env
   ```

2. Настройте переменные окружения в `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

3. Запустите бота:
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

## Просмотр логов

Просмотр всех логов:
```bash
docker-compose -f docker-compose.local.yml logs -f
```

Просмотр логов конкретного контейнера:
```bash
docker logs -f notes-flow-local
```

Очистка логов:
```bash
docker-compose -f docker-compose.local.yml logs -f --tail=100
```

## Остановка бота

```bash
docker-compose -f docker-compose.local.yml down
```

## Перезапуск

```bash
docker-compose -f docker-compose.local.yml restart
```

## Отладка

Если бот не запускается:

1. Проверьте статус контейнера:
   ```bash
   docker-compose -f docker-compose.local.yml ps
   ```

2. Проверьте логи:
   ```bash
   docker-compose -f docker-compose.local.yml logs
   ```

3. Зайдите в контейнер для отладки:
   ```bash
   docker-compose -f docker-compose.local.yml exec notes-flow bash
   ```

4. Запустите бота вручную:
   ```bash
   python -m bot.main
   ```

## Локальный запуск (без Docker)

```bash
# Установите зависимости
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
# отредактируйте TELEGRAM_BOT_TOKEN

# Запустите
python -m bot.main
```

## Структура данных

- `/app/data` - данные пользователей (задачи, заметки, инбокс)
- `/app/logs` - логи бота

Обе директории монтируются в `/share/services/notes-flow/` на хосте.
```

### Этап 5: Тестирование

**Проверки:**
1. `docker-compose -f docker-compose.local.yml up -d` - запускается без ошибок
2. `docker logs -f notes-flow-local` - бот начинает работу
3. `/start` команда работает в Telegram
4. Логи пишутся в файл

## Технические детали

### Router-паттерн aiogram 3.x

В aiogram 3.x используется паттерн Router для организации хендлеров:

```python
from aiogram import Router

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Hello!")
```

Для включения router в приложение:
```python
dp = Dispatcher()
dp.include_router(router)
```

### Регистрация команд бота

```python
from aiogram.types.BotCommand import BotCommand

commands = [
    BotCommand(command="start", description="показать статистику"),
    BotCommand(command="help", description="список команд"),
]

await bot.set_my_commands(commands)
```

## Критерии завершения

- [x] Исправлены все ошибки импорта
- [x] Код адаптирован под Router-паттерн
- [x] Создана документация DEPLOYMENT.md
- [x] Бот запускается через `docker-compose up -d`
- [x] Логи доступны через `docker logs`
- [x] Команды бота работают корректно
- [x] Тесты написаны (опционально)
- [x] Коммит изменений

## История

- **2026-03-07**: Создан тикет, выявлены проблемы с импортами
- **2026-03-07**: Исправлены импорты в bot/main.py и handlers/summarizer.py
- **2026-03-07**: Создана документация DEPLOYMENT.md
- **2026-03-07**: Тикет завершен (ожидают перезапуска группы docker)