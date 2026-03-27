# TICKET-019: Pre-deploy checks, coverage enforcement, regression e2e tests

## Описание

Реализация системы pre-deploy проверок для предотвращения регрессий при выкатке новых версий. Включает:
- Pre-deploy скрипт с проверкой тестов и покрытия кода
- Coverage enforcement с порогом 80%
- Regression e2e тесты для критических пользовательских сценариев
- Docker Compose workflow для локального тестирования

## Статус
✅ completed

## Компоненты

### 1. pre-deploy.sh
- Скрипт для запуска тестов с покрытием
- Проверяет покрытие >= 80% (настраивается через COVERAGE_THRESHOLD)
- Блокирует деплой если тесты падают или покрытие ниже порога

### 2. requirements.txt
- Добавлен `coverage>=7.5.0`

### 3. docker-compose.test.yml
- Docker Compose override для локального тестирования
- Запускает pre-deploy.sh перед стартом основного сервиса
- Старый контейнер продолжает работать во время проверок

### 4. Dockerfile.test
- Dockerfile для тестового образа
- Устанавливает зависимости и запускает pre-deploy.sh

### 5. tests/integration/test_e2e_regression.py
- 13 regression тестов для критических сценариев:
  - Bot commands: /start, /tasks, /done_, /del_, /inbox, /clear
  - Task management: создание задач, заметок, архивация
  - Forwarded messages: сохранение информации об оригинальном авторе
  - Healthcheck: проверка API функций

## Приоритет
🔴 высокий

## Тестирование

### Запуск pre-deploy проверок
```bash
./pre-deploy.sh
```

### Настройка порога покрытия
```bash
COVERAGE_THRESHOLD=90 ./pre-deploy.sh
```

### Запуск Docker Compose test workflow
```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build test
```

### Запуск только e2e тестов
```bash
pytest tests/integration/test_e2e_regression.py -v
```

## Метрики

- **Coverage**: 95% (выше порога 80%)
- **E2E тесты**: 13 passed
- **Всего тестов**: 181 passed, 4 pre-existing failures

## Документация

Обновлён README.md с разделами:
- Pre-deploy проверки
- Docker Compose test workflow
