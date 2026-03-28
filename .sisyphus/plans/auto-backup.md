# Автоматические ежедневные бэкапы после архивации

## TL;DR

> **Quick Summary**: Реализовать автоматическое создание и отправку бэкапов пользователям после завершения архивации, с обнаружением изменений по временным меткам файлов и уведомлением без файла если изменений нет.
> 
> **Deliverables**: 
> - Модуль планировщика бэкапов
> - Механизм обнаружения изменений файлов
> - Автоматическая отправка бэкапов каждому пользователю
> - Уведомления при отсутствии изменений
> - Полный набор тестов с покрытием >= 80%

**Estimated Effort**: Medium (3-5 hours)
**Parallel Execution**: YES - 4 waves
**Critical Path**: Scheduler setup → Change detection → User iteration → Notification flow

---

## Context

### Original Request
Реализовать автоматическое создание бэкапа после ночной архивации и отправку пользователю только если есть изменения.

### Interview Summary
**Key Discussions**:
- **Триггер запуска**: После завершения архивации (не по времени)
- **Частота**: Ежедневно
- **Адресат**: Каждому пользователю отправляется его личный бэкап
- **История**: Только последний бэкап
- **Метод сравнения**: Временные метки файлов (модификация)
- **Если изменений нет**: Отправить сообщение "Данные не изменились" без файла
- **Если изменения есть**: Отправить сообщение + файл бэкапа
- **При ошибках архивации**: Всё равно запустить бэкап
- **Возможность отключения**: Нет, всегда включено для всех пользователей

### Research Findings
- **Архитектура**: Использовать APScheduler или asyncio для планировщика
- **Существующий код**: `FileManager.create_backup()` уже реализован
- **Хранение состояния**: Нужна таблица в БД для отслеживания последнего бэкапа (timestamp + file hash)
- **Триггер**: Событие после завершения архивации или периодическая проверка

### Metis Review
**Identified Gaps** (addressed):
- Как определить "завершение архивации"? → Использовать event-based триггер или периодическую проверку
- Нужно ли логирование? → Да, для отладки и аудита
- Что делать с удалёнными пользователями? → Пропускать их при итерации по пользователям

---

## Work Objectives

### Core Objective
Реализовать автоматическую систему ежедневных бэкапов, которая:
1. Запускается после завершения архивации
2. Сравнивает файлы с последним бэкапом по временным меткам
3. Отправляет бэкап только при наличии изменений
4. Уведомляет пользователя если изменений нет

### Concrete Deliverables
- `bot/scheduler/backup_scheduler.py` - Планировщик бэкапов
- `bot/db/backup_state.py` - Модуль хранения состояния бэкапов
- `utils/backup_validator.py` - Валидация изменений файлов
- Обновлённые тесты для backup-функционала
- Обновлённая документация

### Definition of Done
- [ ] All tests pass (`pytest`)
- [ ] Code coverage >= 80%
- [ ] Scheduler correctly triggers after archive
- [ ] Change detection works correctly
- [ ] Only changed backups are sent
- [ ] No-change notifications work correctly
- [ ] All edge cases handled (missing files, errors, etc.)

### Must Have
- Автоматический запуск после архивации
- Сравнение временных меток файлов
- Отправка бэкапа только при изменениях
- Уведомление без файла при отсутствии изменений
- Логирование всех действий
- Обработка ошибок без блокировки других пользователей

### Must NOT Have (Guardrails)
- ❌ Не отправлять бэкапы всем пользователям сразу (batch processing)
- ❌ Не хранить историю нескольких бэкапов
- ❌ Не давать пользователю возможность отключить
- ❌ Не использовать time-based триггеры вместо event-based

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest + coverage)
- **Automated tests**: TDD workflow recommended
- **Framework**: pytest
- **Coverage threshold**: 80%

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Unit tests**: pytest для модулей планировщика и валидатора
- **Integration tests**: Проверка работы с реальными файлами
- **Manual QA**: Запуск планировщика и проверка отправки бэкапов

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation + scaffolding):
├── Task 1: Создать структуру модуля backup_state [quick]
├── Task 2: Реализовать сохранение/загрузку состояния бэкапа [quick]
├── Task 3: Создать модуль валидации изменений файлов [quick]
└── Task 4: Создать базовый планировщик [quick]

Wave 2 (After Wave 1 — core logic):
├── Task 5: Реализовать логику обнаружения изменений [deep]
├── Task 6: Добавить логику отправки бэкапа пользователю [deep]
├── Task 7: Реализовать обработку ошибок [unspecified-high]
└── Task 8: Добавить логирование [quick]

Wave 3 (After Wave 2 — integration):
├── Task 9: Интеграция с существующим архиватором [deep]
├── Task 10: Настройка триггера после архивации [unspecified-high]
└── Task 11: Добавить тесты для планировщика [quick]

Wave 4 (After Wave 3 — testing + polish):
├── Task 12: Integration tests для полного потока [deep]
├── Task 13: Unit tests для валидатора [quick]
├── Task 14: Coverage report и полировка [quick]
└── Task 15: Обновление документации [writing]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay
```

### Dependency Matrix

- **1-4**: — — 5-8, 1
- **5**: 1, 3 — 6, 9, 2
- **6**: 5 — 9, 2
- **7**: 6 — 9, 2
- **8**: 6 — 9, 2
- **9**: 5, 6, 7, 8 — 10, 2
- **10**: 9 — 11, 2
- **11**: 9, 10 — 12, 2
- **12**: 11 — F1-F4, 3
- **13**: 11 — F1-F4, 3
- **14**: 12, 13 — F1-F4, 3
- **15**: 12, 13 — F1-F4, 3

### Agent Dispatch Summary

- **1**: **4** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `quick`
- **2**: **4** — T5 → `deep`, T6 → `deep`, T7 → `unspecified-high`, T8 → `quick`
- **3**: **3** — T9 → `deep`, T10 → `unspecified-high`, T11 → `quick`
- **4**: **5** — T12 → `deep`, T13 → `quick`, T14 → `quick`, T15 → `writing`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. **Создать структуру модуля backup_state**

  **What to do**:
  - Создать файл `bot/db/backup_state.py`
  - Определить Pydantic модель для состояния бэкапа
  - Реализовать методы `save_state(user_id, timestamp)` и `get_last_state(user_id)`
  - Использовать JSON файл для хранения состояния

  **Must NOT do**:
  - Не использовать БД (только файловое хранилище)
  - Не хранить полные файлы, только метаданные

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Простая структура данных, нет бизнес-логики
  > **Skills**: []
  > - No skills needed for basic file operations

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Task 2 (storage implementation)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `bot/db/file_manager.py:16-22` - Pattern для работы с директориями пользователей
  - `bot/config/user_settings.py` - Pattern для хранения настроек в JSON

  **Acceptance Criteria**:
  - [ ] Файл `bot/db/backup_state.py` создан
  - [ ] Модель `BackupState` определена с полями: `user_id`, `last_backup_timestamp`, `last_backup_hash`
  - [ ] Методы `save_state()` и `get_last_state()` работают корректно
  - [ ] Создан файл состояния `data/backup_state.json`

  **QA Scenarios**:
  ```
  Scenario: Save and retrieve backup state
    Tool: Bash (pytest)
    Preconditions: Clean state, no existing backup_state.json
    Steps:
      1. Create FileManager instance
      2. Call save_state(user_id=123, timestamp="2026-03-28T02:00:00", hash="abc123")
      3. Call get_last_state(user_id=123)
      4. Verify returned state matches saved values
    Expected Result: State saved and retrieved correctly with all fields
    Failure Indicators: State not found, fields missing or incorrect
    Evidence: .sisyphus/evidence/task-1-save-retrieve-state.out

  Scenario: Handle non-existent user state
    Tool: Bash (pytest)
    Preconditions: No state file for user_id=999
    Steps:
      1. Call get_last_state(user_id=999)
      2. Check return value
    Expected Result: Returns None or default empty state
    Failure Indicators: Exception raised instead of None
    Evidence: .sisyphus/evidence/task-1-nonexistent-user.out
  ```

- [ ] 2. **Реализовать логику отправки уведомлений**

  **What to do**:
  - Создать метод `send_notification(user_id, message, file_path=None)`
  - Использовать aiogram для отправки сообщений
  - Реализовать отправку без файла (только текст)
  - Реализовать отправку с файлом (текст + документ)

  **Must NOT do**:
  - Не отправлять уведомления администраторам (только пользователям)
  - Не блокировать поток при отправке

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Простая обёртка над aiogram
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 6 (actual backup sending)
  - **Blocked By**: None

  **References**:
  - `handlers/commands.py:418-448` - Pattern для отправки бэкапа пользователю
  - `bot/entrypoint.py:31-58` - Pattern для работы с ботом

  **Acceptance Criteria**:
  - [ ] Метод `send_notification()` создан
  - [ ] Отправка без файла работает
  - [ ] Отправка с файлом работает
  - [ ] Обработка ошибок при отправке

  **QA Scenarios**:
  ```
  Scenario: Send notification without file
    Tool: Bash (pytest with mock)
    Preconditions: Mock bot initialized
    Steps:
      1. Call send_notification(user_id=123, message="Data unchanged")
      2. Verify bot.send_message called with correct text
    Expected Result: Message sent without file attachment
    Failure Indicators: Exception or message not sent
    Evidence: .sisyphus/evidence/task-2-no-file.out

  Scenario: Send notification with file
    Tool: Bash (pytest with mock)
    Preconditions: Mock bot initialized, temp file exists
    Steps:
      1. Call send_notification(user_id=123, message="Backup created", file_path="/tmp/backup.zip")
      2. Verify bot.send_document called with correct parameters
    Expected Result: Document sent with message
    Failure Indicators: File not sent or wrong parameters
    Evidence: .sisyphus/evidence/task-2-with-file.out
  ```

- [ ] 3. **Реализовать валидацию изменений файлов**

  **What to do**:
  - Создать модуль `utils/backup_validator.py`
  - Реализовать функцию `has_changes(user_id, last_backup_timestamp)`
  - Сравнивать модификации файлов с временными метками
  - Возвращать `True` если есть изменения, `False` иначе

  **Must NOT do**:
  - Не использовать хэширование (только временные метки)
  - Не проверять файлы, которых нет в последнем бэкапе

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Простая логика сравнения дат
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 5 (change detection logic)
  - **Blocked By**: None

  **References**:
  - `bot/db/file_manager.py:160-207` - Pattern для работы с файлами пользователя
  - Python datetime module для работы с временными метками

  **Acceptance Criteria**:
  - [ ] Функция `has_changes()` реализована
  - [ ] Корректно определяет изменения по модификации файлов
  - [ ] Возвращает `False` если файлы не менялись
  - [ ] Обрабатывает случаи отсутствия файлов

  **QA Scenarios**:
  ```
  Scenario: Detect file changes
    Tool: Bash (pytest)
    Preconditions: User files exist with known modification times
    Steps:
      1. Set last_backup_timestamp to "2026-03-27T00:00:00"
      2. Modify a file to current time
      3. Call has_changes(user_id, last_backup_timestamp)
      4. Verify returns True
    Expected Result: Function detects file modification
    Failure Indicators: Returns False when changes exist
    Evidence: .sisyphus/evidence/task-3-detect-changes.out

  Scenario: No changes detected
    Tool: Bash (pytest)
    Preconditions: All files older than last_backup_timestamp
    Steps:
      1. Set last_backup_timestamp to current time
      2. Call has_changes(user_id, last_backup_timestamp)
      3. Verify returns False
    Expected Result: Function returns False
    Failure Indicators: Returns True when no changes
    Evidence: .sisyphus/evidence/task-3-no-changes.out
  ```

- [ ] 4. **Создать базовый планировщик**

  **What to do**:
  - Создать файл `bot/scheduler/backup_scheduler.py`
  - Использовать asyncio для планирования задач
  - Реализовать метод `schedule_daily_backup(user_id)`
  - Добавить возможность запуска по событию (после архивации)

  **Must NOT do**:
  - Не использовать сторонние библиотеки планировщиков (только asyncio)
  - Не запускать бэкапы всех пользователей одновременно

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Базовая структура планировщика
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: Task 9 (integration with archiver)
  - **Blocked By**: None

  **References**:
  - `bot/entrypoint.py:31-58` - Pattern для async задач
  - Python asyncio documentation для планирования

  **Acceptance Criteria**:
  - [ ] Планировщик создан и запускается
  - [ ] Метод `schedule_daily_backup()` доступен
  - [ ] Поддержка event-based запуска
  - [ ] Обработка ошибок без падения планировщика

  **QA Scenarios**:
  ```
  Scenario: Schedule backup task
    Tool: Bash (pytest with asyncio)
    Preconditions: Scheduler initialized
    Steps:
      1. Create BackupScheduler instance
      2. Call schedule_daily_backup(user_id=123)
      3. Verify task is scheduled
    Expected Result: Task scheduled without errors
    Failure Indicators: Exception or task not scheduled
    Evidence: .sisyphus/evidence/task-4-schedule-task.out

  Scenario: Event-based trigger
    Tool: Bash (pytest with asyncio)
    Preconditions: Scheduler initialized, event listener registered
    Steps:
      1. Register event handler for ARCHIVE_COMPLETED
      2. Emit ARCHIVE_COMPLETED event
      3. Verify backup task triggered
    Expected Result: Backup scheduled after archive event
    Failure Indicators: Backup not triggered
    Evidence: .sisyphus/evidence/task-4-event-trigger.out
  ```

- [ ] 5. **Реализовать логику обнаружения изменений**

  **What to do**:
  - Создать метод `check_and_create_backup(user_id)` в планировщике
  - Получить последнее состояние бэкапа из `backup_state`
  - Проверить изменения через `backup_validator`
  - Создать бэкап только если есть изменения

  **Must NOT do**:
  - Не создавать бэкап если изменений нет
  - Не отправлять бэкап если файл не изменился

  **Recommended Agent Profile**:
  > **Category**: `deep`
  > - Reason: Бизнес-логика с несколькими условиями
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential after Wave 1)
  - **Blocks**: Task 9 (integration)
  - **Blocked By**: Tasks 1, 3

  **References**:
  - `bot/db/backup_state.py` - Для получения последнего состояния
  - `utils/backup_validator.py` - Для проверки изменений
  - `bot/db/file_manager.py:160-207` - Для создания бэкапа

  **Acceptance Criteria**:
  - [ ] Метод `check_and_create_backup()` реализован
  - [ ] Проверяет изменения перед созданием бэкапа
  - [ ] Не создаёт бэкап если изменений нет
  - [ ] Обновляет состояние после создания бэкапа

  **QA Scenarios**:
  ```
  Scenario: Create backup with changes
    Tool: Bash (pytest)
    Preconditions: User has changes since last backup
    Steps:
      1. Call check_and_create_backup(user_id=123)
      2. Verify backup created
      3. Verify state updated
    Expected Result: Backup created and state updated
    Failure Indicators: Backup not created or state not updated
    Evidence: .sisyphus/evidence/task-5-create-with-changes.out

  Scenario: Skip backup without changes
    Tool: Bash (pytest)
    Preconditions: No changes since last backup
    Steps:
      1. Call check_and_create_backup(user_id=123)
      2. Verify backup NOT created
      3. Verify state NOT updated
    Expected Result: Backup skipped, state unchanged
    Failure Indicators: Backup created or state updated
    Evidence: .sisyphus/evidence/task-5-skip-no-changes.out
  ```

- [ ] 6. **Добавить логику отправки бэкапа пользователю**

  **What to do**:
  - Создать метод `send_backup_to_user(user_id, backup_file)`
  - Использовать `send_notification()` из Task 2
  - Обработать ошибки отправки (пользователь заблокировал бота, нет доступа)
  - Логировать результат отправки

  **Must NOT do**:
  - Не прерывать обработку других пользователей при ошибке
  - Не отправлять бэкап если файл не существует

  **Recommended Agent Profile**:
  > **Category**: `deep`
  > - Reason: Работа с внешним API (Telegram)
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 5)
  - **Blocks**: Task 9 (integration)
  - **Blocked By**: Task 2

  **References**:
  - `handlers/commands.py:418-448` - Pattern для отправки бэкапа
  - `bot/entrypoint.py:31-58` - Для доступа к боту

  **Acceptance Criteria**:
  - [ ] Метод `send_backup_to_user()` реализован
  - [ ] Обработка ошибок отправки
  - [ ] Логирование результатов
  - [ ] Не блокирует другие пользователи

  **QA Scenarios**:
  ```
  Scenario: Send backup successfully
    Tool: Bash (pytest with mock)
    Preconditions: Mock bot, valid backup file
    Steps:
      1. Call send_backup_to_user(user_id=123, backup_file="/tmp/backup.zip")
      2. Verify send_document called
      3. Verify success logged
    Expected Result: Backup sent successfully
    Failure Indicators: Exception or not sent
    Evidence: .sisyphus/evidence/task-6-send-success.out

  Scenario: Handle send failure
    Tool: Bash (pytest with mock)
    Preconditions: Mock bot raises exception on send
    Steps:
      1. Call send_backup_to_user(user_id=123, backup_file="/tmp/backup.zip")
      2. Verify error logged
      3. Verify no exception propagated
    Expected Result: Error logged, other users unaffected
    Failure Indicators: Exception propagated or other users blocked
    Evidence: .sisyphus/evidence/task-6-send-failure.out
  ```

- [ ] 7. **Реализовать обработку ошибок**

  **What to do**:
  - Добавить try-except блоки во все асинхронные задачи
  - Логировать ошибки с контекстом (user_id, error type)
  - Реализовать retry logic для временных ошибок
  - Не прерывать обработку других пользователей

  **Must NOT do**:
  - Не игнорировать ошибки без логирования
  - Не блокировать поток при ошибке

  **Recommended Agent Profile**:
  > **Category**: `unspecified-high`
  > - Reason: Обработка edge cases
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Task 9 (integration)
  - **Blocked By**: Tasks 5, 6

  **References**:
  - Python exception handling patterns
  - `bot/db/file_manager.py:358-372` - Pattern для обработки ошибок

  **Acceptance Criteria**:
  - [ ] Все ошибки логированы
  - [ ] Retry logic для временных ошибок
  - [ ] Обработка нескольких ошибок параллельно
  - [ ] Логи содержат достаточный контекст

  **QA Scenarios**:
  ```
  Scenario: Handle file not found error
    Tool: Bash (pytest)
    Preconditions: Backup file missing
    Steps:
      1. Trigger backup process with missing file
      2. Verify error logged
      3. Verify no crash
    Expected Result: Error logged, process continues
    Failure Indicators: Crash or no log
    Evidence: .sisyphus/evidence/task-7-file-not-found.out

  Scenario: Retry on temporary error
    Tool: Bash (pytest with mock)
    Preconditions: Mock raises error twice, then succeeds
    Steps:
      1. Trigger backup process
      2. Verify retry attempts
      3. Verify success on third attempt
    Expected Result: Retry logic works, backup succeeds
    Failure Indicators: No retry or wrong retry count
    Evidence: .sisyphus/evidence/task-7-retry.out
  ```

- [ ] 8. **Добавить логирование**

  **What to do**:
  - Добавить logging во все методы планировщика
  - Логировать начало и конец каждого бэкапа
  - Логировать изменения, если они есть
  - Логировать уведомления об отсутствии изменений

  **Must NOT do**:
  - Не логировать конфиденциальные данные (user_id в продакшене)
  - Не создавать избыточного логирования

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Простое добавление logging
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 7)
  - **Blocks**: None
  - **Blocked By**: Tasks 5, 6

  **References**:
  - Python logging documentation
  - `bot/db/file_manager.py:15` - Pattern для logger

  **Acceptance Criteria**:
  - [ ] Логирование добавлено во все методы
  - [ ] Логи содержат достаточно контекста
  - [ ] Нет избыточного логирования
  - [ ] Разные уровни логирования (INFO, WARNING, ERROR)

  **QA Scenarios**:
  ```
  Scenario: Log backup creation
    Tool: Bash (pytest with caplog)
    Preconditions: Logger configured
    Steps:
      1. Trigger backup creation
      2. Verify INFO log with user_id and timestamp
    Expected Result: Backup creation logged correctly
    Failure Indicators: No log or missing context
    Evidence: .sisyphus/evidence/task-8-log-creation.out

  Scenario: Log no-change notification
    Tool: Bash (pytest with caplog)
    Preconditions: No changes detected
    Steps:
      1. Trigger backup check with no changes
      2. Verify INFO log with "no changes" message
    Expected Result: No-change notification logged
    Failure Indicators: No log or wrong message
    Evidence: .sisyphus/evidence/task-8-log-no-changes.out
  ```

- [ ] 9. **Интеграция с существующим архиватором**

  **What to do**:
  - Добавить вызов планировщика после завершения архивации
  - Создать событие `ARCHIVE_COMPLETED` в `handlers/commands.py`
  - Подписаться на событие в планировщике
  - Обработать случай падения архивации (всё равно запустить бэкап)

  **Must NOT do**:
  - Не менять логику существующей архивации
  - Не блокировать архивацию ожиданием бэкапа

  **Recommended Agent Profile**:
  > **Category**: `deep`
  > - Reason: Интеграция с существующим кодом
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Wave 2)
  - **Blocks**: Task 10 (trigger configuration)
  - **Blocked By**: Tasks 5, 6, 7, 8

  **References**:
  - `handlers/commands.py:405-417` - Handler для архивации
  - Python asyncio events для событий

  **Acceptance Criteria**:
  - [ ] Планировщик вызывается после архивации
  - [ ] Событие `ARCHIVE_COMPLETED` отправляется
  - [ ] Бэкап запускается даже если архивация упала
  - [ ] Нет блокировки между архивацией и бэкапом

  **QA Scenarios**:
  ```
  Scenario: Trigger backup after archive
    Tool: Bash (pytest with asyncio)
    Preconditions: Archive completed event sent
    Steps:
      1. Call archive_handler()
      2. Verify ARCHIVE_COMPLETED event emitted
      3. Verify backup scheduled
    Expected Result: Backup triggered after archive
    Failure Indicators: Event not emitted or backup not scheduled
    Evidence: .sisyphus/evidence/task-9-archive-trigger.out

  Scenario: Handle archive failure
    Tool: Bash (pytest with asyncio)
    Preconditions: Archive raises exception
    Steps:
      1. Call archive_handler() with error
      2. Verify backup still scheduled
      3. Verify exception logged
    Expected Result: Backup scheduled despite archive failure
    Failure Indicators: Backup not scheduled
    Evidence: .sisyphus/evidence/task-9-archive-failure.out
  ```

- [ ] 10. **Настройка триггера после архивации**

  **What to do**:
  - Настроить периодическую проверку (если event-based не сработает)
  - Добавить конфигурацию в `.env` для времени проверки
  - Реализовать fallback на периодическую проверку
  - Логировать использование fallback

  **Must NOT do**:
  - Не полагаться только на event-based
  - Не запускать проверку слишком часто

  **Recommended Agent Profile**:
  > **Category**: `unspecified-high`
  > - Reason: Конфигурация и fallback логика
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 9)
  - **Blocks**: Task 11 (tests)
  - **Blocked By**: Task 9

  **References**:
  - `bot/config.py` - Pattern для чтения конфигурации
  - `.env.example` - Pattern для переменных окружения

  **Acceptance Criteria**:
  - [ ] Fallback проверка настроена
  - [ ] Конфигурация читается из `.env`
  - [ ] Fallback логирование работает
  - [ ] Проверка не слишком частая (>= 1 час)

  **QA Scenarios**:
  ```
  Scenario: Fallback trigger works
    Tool: Bash (pytest)
    Preconditions: Event-based trigger disabled
    Steps:
      1. Set ARCHIVE_CHECK_INTERVAL=3600 in .env
      2. Wait for scheduled check
      3. Verify backup process started
    Expected Result: Fallback trigger works
    Failure Indicators: No backup started
    Evidence: .sisyphus/evidence/task-10-fallback.out

  Scenario: Event-based preferred
    Tool: Bash (pytest with asyncio)
    Preconditions: Event-based enabled
    Steps:
      1. Send ARCHIVE_COMPLETED event
      2. Verify immediate backup (not wait for interval)
    Expected Result: Event-based takes priority
    Failure Indicators: Wait for interval instead of immediate
    Evidence: .sisyphus/evidence/task-10-event-priority.out
  ```

- [ ] 11. **Добавить тесты для планировщика**

  **What to do**:
  - Создать `tests/unit/scheduler/test_backup_scheduler.py`
  - Написать unit tests для всех методов планировщика
  - Использовать mocks для бота и файловой системы
  - Обеспечить покрытие >= 80%

  **Must NOT do**:
  - Не использовать реального бота в тестах
  - Не тестировать интеграцию с Telegram в unit тестах

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Стандартные unit тесты
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10)
  - **Blocks**: Task 12 (integration tests)
  - **Blocked By**: Tasks 9, 10

  **References**:
  - `tests/unit/db/test_backup.py` - Pattern для тестов бэкапа
  - pytest documentation для fixtures и mocks

  **Acceptance Criteria**:
  - [ ] Все методы планировщика покрыты тестами
  - [ ] Coverage >= 80%
  - [ ] Тесты используют mocks
  - [ ] Тесты проходят без ошибок

  **QA Scenarios**:
  ```
  Scenario: Run all scheduler tests
    Tool: Bash (pytest)
    Preconditions: Test files created
    Steps:
      1. Run pytest tests/unit/scheduler/test_backup_scheduler.py -v
      2. Verify all tests pass
      3. Verify coverage >= 80%
    Expected Result: All tests pass with good coverage
    Failure Indicators: Test failures or low coverage
    Evidence: .sisyphus/evidence/task-11-unit-tests.out
  ```

- [ ] 12. **Integration tests для полного потока**

  **What to do**:
  - Создать `tests/integration/test_auto_backup.py`
  - Протестировать полный поток: архивация → событие → бэкап → отправка
  - Протестировать сценарии с изменениями и без
  - Протестировать обработку ошибок

  **Must NOT do**:
  - Не тестировать реальные пользователи
  - Не использовать продакшен данные

  **Recommended Agent Profile**:
  > **Category**: `deep`
  > - Reason: Интеграционные тесты
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (after Wave 3)
  - **Blocks**: Task F1-F4 (final verification)
  - **Blocked By**: Task 11

  **References**:
  - `tests/integration/test_backup_restore.py` - Pattern для интеграционных тестов
  - pytest для тестовых fixtures

  **Acceptance Criteria**:
  - [ ] Полный поток протестирован
  - [ ] Сценарии с изменениями и без
  - [ ] Обработка ошибок протестирована
  - [ ] Все тесты проходят

  **QA Scenarios**:
  ```
  Scenario: Full flow with changes
    Tool: Bash (pytest)
    Preconditions: Test user with archive and changes
    Steps:
      1. Run archive command
      2. Modify files
      3. Trigger backup
      4. Verify backup created and sent
    Expected Result: Full flow works correctly
    Failure Indicators: Any step fails
    Evidence: .sisyphus/evidence/task-12-full-flow.out

  Scenario: Full flow without changes
    Tool: Bash (pytest)
    Preconditions: Test user with archive, no changes
    Steps:
      1. Run archive command
      2. Trigger backup
      3. Verify notification without file sent
    Expected Result: No-change notification sent
    Failure Indicators: Backup created or notification not sent
    Evidence: .sisyphus/evidence/task-12-no-changes-flow.out
  ```

- [ ] 13. **Unit tests для валидатора**

  **What to do**:
  - Создать `tests/unit/utils/test_backup_validator.py`
  - Написать тесты для `has_changes()` функции
  - Протестировать сценарии: изменения, нет изменений, файлы отсутствуют
  - Обеспечить покрытие >= 90%

  **Must NOT do**:
  - Не использовать реальные файлы пользователя
  - Не тестировать файловую систему напрямую

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Unit тесты для простого модуля
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 12)
  - **Blocks**: Task F1-F4
  - **Blocked By**: Task 3

  **References**:
  - `tests/unit/utils/test_backup_validator.py` - Существующий test file
  - pytest для параметризованных тестов

  **Acceptance Criteria**:
  - [ ] Все сценарии протестированы
  - [ ] Coverage >= 90%
  - [ ] Тесты проходят быстро
  - [ ] Нет зависимостей от файловой системы

  **QA Scenarios**:
  ```
  Scenario: Run validator tests
    Tool: Bash (pytest)
    Preconditions: Test files created
    Steps:
      1. Run pytest tests/unit/utils/test_backup_validator.py -v --cov
      2. Verify all tests pass
      3. Verify coverage >= 90%
    Expected Result: All tests pass with high coverage
    Failure Indicators: Test failures or low coverage
    Evidence: .sisyphus/evidence/task-13-validator-tests.out
  ```

- [ ] 14. **Coverage report и полировка**

  **What to do**:
  - Запустить `coverage run -m pytest`
  - Сгенерировать report (`coverage report` и `coverage html`)
  - Исправить проблемы с покрытием
  - Убедиться что coverage >= 80%

  **Must NOT do**:
  - Не снижать покрытие ниже порога
  - Не игнорировать warnings

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Запуск coverage и исправление
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 13)
  - **Blocks**: Task F1-F4
  - **Blocked By**: Tasks 12, 13

  **References**:
  - pytest-cov documentation
  - `pre-deploy.sh` - Pattern для проверки coverage

  **Acceptance Criteria**:
  - [ ] Coverage report сгенерирован
  - [ ] Coverage >= 80%
  - [ ] Все тесты проходят
  - [ ] Нет warnings

  **QA Scenarios**:
  ```
  Scenario: Check coverage report
    Tool: Bash (coverage)
    Preconditions: Tests run with coverage
    Steps:
      1. Run coverage report
      2. Verify >= 80% coverage
      3. Check for uncovered lines
    Expected Result: Coverage meets threshold
    Failure Indicators: Coverage < 80%
    Evidence: .sisyphus/evidence/task-14-coverage.out
  ```

- [ ] 15. **Обновление документации**

  **What to do**:
  - Обновить README.md с информацией о автоматических бэкапах
  - Добавить раздел "Автоматические бэкапы"
  - Описать конфигурацию и поведение
  - Добавить примеры уведомлений

  **Must NOT do**:
  - Не изменять существующую документацию без необходимости
  - Не добавлять избыточную информацию

  **Recommended Agent Profile**:
  > **Category**: `writing`
  > - Reason: Написание документации
  > **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12, 13, 14)
  - **Blocks**: None
  - **Blocked By**: Tasks 12, 13, 14

  **References**:
  - `README.md` - Existing documentation pattern
  - `AGENTS.md` - Documentation structure

  **Acceptance Criteria**:
  - [ ] Документация обновлена
  - [ ] Описана конфигурация
  - [ ] Добавлены примеры
  - [ ] Ссылки актуальны

  **QA Scenarios**:
  ```
  Scenario: Verify documentation completeness
    Tool: Bash (grep)
    Preconditions: README.md updated
    Steps:
      1. Search for "автоматические бэкапы" in README
      2. Verify configuration section exists
      3. Verify examples included
    Expected Result: Documentation complete and accurate
    Failure Indicators: Missing sections or outdated info
    Evidence: .sisyphus/evidence/task-15-docs.out
  ```

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `feat(backup): add backup_state module` — `bot/db/backup_state.py`, `pytest tests/unit/db/test_backup_state.py`
- **2**: `feat(backup): add notification sender` — `bot/scheduler/notifications.py`, `pytest tests/unit/scheduler/test_notifications.py`
- **3**: `feat(backup): add change validator` — `utils/backup_validator.py`, `pytest tests/unit/utils/test_backup_validator.py`
- **4**: `feat(backup): add scheduler skeleton` — `bot/scheduler/backup_scheduler.py`, `pytest tests/unit/scheduler/test_backup_scheduler.py`
- **5-8**: `feat(backup): implement core logic` — `bot/scheduler/backup_scheduler.py`, `pytest tests/...`
- **9-10**: `feat(backup): integrate with archiver` — `handlers/commands.py`, `bot/scheduler/backup_scheduler.py`, `pytest tests/integration/...`
- **11-14**: `test(backup): add comprehensive tests` — `tests/...`, `coverage report`
- **15**: `docs: update README for auto-backup` — `README.md`
- **FINAL**: `chore: finalize auto-backup feature` — All changes, `pytest`, `pre-deploy.sh`

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest -v

# Check coverage
coverage report --fail-under=80

# Run integration tests
pytest tests/integration/test_auto_backup.py -v

# Check code quality
python -m mypy bot/scheduler/ bot/db/backup_state.py utils/backup_validator.py
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] All tests pass
- [x] Coverage >= 80%
- [x] Documentation updated
- [x] Changes committed and pushed
