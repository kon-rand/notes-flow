# Notes Flow

Telegram бот для управления заметками.

## Требования

- Python 3.12+

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

2. Активируйте окружение:
```bash
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте `.env.example` в `.env` и настройте переменные окружения.

## Запуск

```bash
python bot/main.py
```

## Разработка

### Запуск тестов

```bash
pytest
```

### Конвенции тестов

Следуйте [CONVENTIONS.md](TEST_CONVENTIONS.md) для написания тестов.

### Концепция работы агентов

Проект управляется командой агентов согласно [AGENTS.md](AGENTS.md).