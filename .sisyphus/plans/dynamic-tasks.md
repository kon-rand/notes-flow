# Dynamic /tasks Message Updates

## TL;DR

> **Quick Summary**: Реализовать редактирование существующих сообщений `/tasks` и `/archive` вместо отправки новых при изменении задач.

**Deliverables**:
- Обновление `UserSettings` с полями `tasks_message_id` и `archive_message_id`
- Модификация всех handler-ов команд для редактирования сообщений
- Обработка edge cases (первый запуск, удалённые сообщения, лимит 48ч)

**Estimated Effort**: Short  
**Parallel Execution**: NO - sequential (зависимости между компонентами)  
**Critical Path**: UserSettings → handlers/commands.py → handlers/summarizer.py → verification

---

## Context

### Original Request
> "Я хочу, чтобы по командам /done, /undone, /archive, /summarize(или по таймеру) редактировалось последнее сообщение с командой /tasks и там было актуальное состояние"

### Interview Summary

**Key Discussions**:
- **Хранение message_id**: В `user_settings.py` (добавить `tasks_message_id` и `archive_message_id`)
- **Команды для обновления**: `/tasks`, `/archive`, `/notes`, `/inbox`, `/clear`, `/done_X`, `/undone_X`, `/summarize` (включая таймер)
- **Edge cases**: Если message_id не найден - просто отправить новое сообщение, без ошибок
- **Таймер саммаризации**: Обновлять `/tasks` после автоматической саммаризации

**Research Findings**:
- `/tasks` сейчас отправляет НОВОЕ сообщение каждый раз (`message.answer()`)
- Нет трекинга message_id отправленных сообщений
- `last_message_id` в `user_settings.py` используется для генерации ID задач, не для бота
- Команды находятся в `handlers/commands.py`

---

## Work Objectives

### Core Objective
Реализовать динамическое обновление сообщений `/tasks` и `/archive` через редактирование существующих сообщений вместо отправки новых.

### Concrete Deliverables
- Модификация `UserSettings` модели
- Обновление всех handler-ов команд
- Интеграция с таймером саммаризации
- Тесты для новой функциональности

### Definition of Done
- [ ] Все команды, которые меняют задачи, обновляют сообщения через `edit_message_text`
- [ ] Edge cases обработаны (первый запуск, удалённые сообщения, >48ч)
- [ ] Тесты проходят (unit + integration)
- [ ] Документация обновлена

### Must Have
- ✅ Хранение `tasks_message_id` и `archive_message_id` в `user_settings.py`
- ✅ Редактирование сообщений через `message.edit_message_text()` или `bot.edit_message_text()`
- ✅ Graceful handling при отсутствии message_id
- ✅ Обновление после таймерной саммаризации

### Must NOT Have (Guardrails)
- ❌ Не отправлять дубликаты сообщений
- ❌ Не хранить историю message_id (только последний)
- ❌ Не требовать ручного вмешательства при ошибках
- ❌ Не усложнять существующую логику команд

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: TDD
- **Framework**: pytest (bun test)
- **Workflow**: RED → GREEN → REFACTOR для каждого компонента

### QA Policy
Каждый компонент будет протестирован через:
1. **Unit tests**: pytest для логики
2. **Integration tests**: реальные вызовы handler-ов
3. **Manual QA**: curl для API endpoints

---

## Execution Strategy

### Sequential Execution Waves

```
Wave 1 (Foundation - core infrastructure):
├── Task 1: Обновление UserSettings модели
├── Task 2: Добавление helper функций для редактирования
└── Task 3: Модификация tasks_handler

Wave 2 (Command handlers - parallel):
├── Task 4: Модификация archive_handler
├── Task 5: Модификация notes_handler
├── Task 6: Модификация inbox_handler
├── Task 7: Модификация clear_handler
└── Task 8: Модификация done_task_handler
├── Task 9: Модификация undone_task_handler

Wave 3 (Timer integration):
├── Task 10: Интеграция с таймером саммаризации
└── Task 11: Обновление summarizer.py

Wave 4 (Testing & Polish):
├── Task 12: Unit tests для всех handler-ов
├── Task 13: Integration tests
├── Task 14: Documentation update
└── Task 15: Final verification

Critical Path: Task 1 → Task 3 → Task 12 → Task 15
Parallel Speedup: ~40% faster than sequential
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

- **1**: — → 2, 3, 4, 5, 6, 7, 8, 9
- **2**: 1 → 3, 4, 5, 6, 7, 8, 9
- **3**: 1, 2 → 12
- **4**: 1, 2 → 12
- **5**: 1, 2 → 12
- **6**: 1, 2 → 12
- **7**: 1, 2 → 12
- **8**: 1, 2 → 12
- **9**: 1, 2 → 12
- **10**: 1, 2, 3, 4, 5, 6, 7, 8, 9 → 11, 12
- **11**: 10 → 12
- **12**: 3, 4, 5, 6, 7, 8, 9, 11 → 13, 14
- **13**: 12 → 15
- **14**: 12 → 15
- **15**: 13, 14 → DONE

### Agent Dispatch Summary

- **Wave 1**: 3 tasks → `quick` (простые изменения)
- **Wave 2**: 6 tasks → `quick` (шаблонные изменения)
- **Wave 3**: 2 tasks → `unspecified-high` (интеграция)
- **Wave 4**: 4 tasks → `quick` (тесты и документация)

---

## TODOs

### Wave 1: Foundation

- [ ] 1. Обновление UserSettings модели

  **What to do**:
  - Открыть `bot/config/user_settings.py`
  - Добавить поля `tasks_message_id: Optional[int] = None` и `archive_message_id: Optional[int] = None`
  - Обновить модель для поддержки новых полей
  - Проверить миграции (если есть)

  **Must NOT do**:
  - Не менять существующие поля
  - Не удалять валидацию

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Простое добавление полей в модель
  > **Skills**: `[]`
  >   - Нет специализированных навыков не нужно

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Все остальные задачи (зависят от модели)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `bot/config/user_settings.py` - текущая структура UserSettings
  - `bot/db/file_manager.py` - как используются поля UserSettings

  **Acceptance Criteria**:
  - [ ] Модель UserSettings включает `tasks_message_id: Optional[int] = None`
  - [ ] Модель UserSettings включает `archive_message_id: Optional[int] = None`
  - [ ] `bun test` проходит без ошибок

  **QA Scenarios**:
  ```
  Scenario: UserSettings включает новые поля
    Tool: Bash (python REPL)
    Preconditions: bot/config/user_settings.py существует
    Steps:
      1. python3 -c "from bot.config.user_settings import UserSettings; import inspect; print(inspect.signature(UserSettings.__init__))"
    Expected Result: Подпись включает tasks_message_id и archive_message_id
    Failure Indicators: AttributeError или отсутствие полей в сигнатуре
    Evidence: .sisyphus/evidence/task-1-user-settings-fields.txt
  ```

  **Commit**: YES
  - Message: `feat: add message_id fields to UserSettings`
  - Files: `bot/config/user_settings.py`
  - Pre-commit: `bun test`

---

- [ ] 2. Добавление helper функций для редактирования

  **What to do**:
  - Создать файл `bot/helpers/message_updater.py`
  - Добавить функцию `update_or_create_task_message(user_id: int, text: str) -> int`
  - Добавить функцию `update_or_create_archive_message(user_id: int, text: str) -> int`
  - Реализовать логику: если message_id есть → edit, иначе → send + save

  **Must NOT do**:
  - Не усложнять логику
  - Не добавлять лишние зависимости

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Шаблонные функции
  > **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (зависит от UserSettings)
  - **Blocks**: Wave 2 (все handler-ы)
  - **Blocked By**: Task 1

  **References**:
  - `handlers/commands.py:tasks_handler` - текущая логика отправки
  - `bot/config/user_settings.py` - доступ к полям message_id
  - aiogram docs: `Message.edit_message_text()`, `Bot.edit_message_text()`

  **Acceptance Criteria**:
  - [ ] Функция `update_or_create_task_message` существует
  - [ ] Функция `update_or_create_archive_message` существует
  - [ ] Логика: edit если message_id есть, иначе send + save

  **QA Scenarios**:
  ```
  Scenario: Редактирование существующего сообщения
    Tool: Python (mock test)
    Preconditions: user_settings.tasks_message_id = 123
    Steps:
      1. Вызвать update_or_create_task_message(user_id=1, text="new text")
      2. Проверить вызов edit_message_text
    Expected Result: Вызван edit_message_text с message_id=123
    Failure Indicators: Вызван answer вместо edit
    Evidence: .sisyphus/evidence/task-2-edit-existing.txt

  Scenario: Отправка нового сообщения (message_id = None)
    Tool: Python (mock test)
    Preconditions: user_settings.tasks_message_id = None
    Steps:
      1. Вызвать update_or_create_task_message(user_id=1, text="new text")
      2. Проверить вызов answer
    Expected Result: Вызван answer, message_id сохранён
    Failure Indicators: Вызван edit с None
    Evidence: .sisyphus/evidence/task-2-send-new.txt
  ```

  **Commit**: YES
  - Message: `feat: add message updater helper functions`
  - Files: `bot/helpers/message_updater.py`
  - Pre-commit: `bun test`

---

- [ ] 3. Модификация tasks_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `tasks_handler` (строки ~169-202)
  - Заменить `message.answer(response)` на вызов `update_or_create_task_message`
  - Сохранить возвращённый message_id в user_settings

  **Must NOT do**:
  - Не менять логику формирования ответа
  - Не удалять существующую функциональность

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > - Reason: Замена одного вызова на другой
  > **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (зависит от Tasks 1, 2)
  - **Blocks**: Task 12 (тесты)
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `handlers/commands.py:tasks_handler` - текущая реализация
  - `bot/helpers/message_updater.py` - новая функция
  - `bot/db/file_manager.py` - как обновлять user_settings

  **Acceptance Criteria**:
  - [ ] tasks_handler использует update_or_create_task_message
  - [ ] message_id сохраняется в user_settings

  **QA Scenarios**:
  ```
  Scenario: /tasks обновляет существующее сообщение
    Tool: Python (mock test)
    Preconditions: user_settings.tasks_message_id = 123
    Steps:
      1. Запустить tasks_handler с user_id=1
      2. Проверить вызов edit_message_text
    Expected Result: Сообщение отредактировано, message_id обновлён
    Failure Indicators: Отправлено новое сообщение
    Evidence: .sisyphus/evidence/task-3-edit-task.txt

  Scenario: /tasks отправляет новое сообщение (первый раз)
    Tool: Python (mock test)
    Preconditions: user_settings.tasks_message_id = None
    Steps:
      1. Запустить tasks_handler с user_id=1
      2. Проверить вызов answer
    Expected Result: Отправлено новое сообщение, message_id сохранён
    Failure Indicators: Попытка edit с None
    Evidence: .sisyphus/evidence/task-3-new-task.txt
  ```

  **Commit**: YES
  - Message: `feat: tasks_handler uses message updater`
  - Files: `handlers/commands.py`
  - Pre-commit: `bun test handlers/commands/test_commands.py`

---

### Wave 2: Command Handlers

- [ ] 4. Модификация archive_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `archive_handler`
  - Заменить `message.answer(response)` на `update_or_create_archive_message`
  - Сохранить message_id

  **Must NOT do**:
  - Не менять логику формирования ответа

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 5-9

  **References**:
  - `handlers/commands.py:archive_handler`

  **Acceptance Criteria**:
  - [ ] archive_handler использует update_or_create_archive_message

  **Commit**: YES
  - Message: `feat: archive_handler uses message updater`

---

- [ ] 5. Модификация notes_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `notes_handler`
  - Заменить `message.answer(response)` на `update_or_create_archive_message` (или отдельную функцию)
  - Сохранить message_id

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 4, 6-9

  **References**:
  - `handlers/commands.py:notes_handler`

  **Acceptance Criteria**:
  - [ ] notes_handler обновляет своё сообщение

  **Commit**: YES
  - Message: `feat: notes_handler uses message updater`

---

- [ ] 6. Модификация inbox_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `inbox_handler`
  - Заменить `message.answer(response)` на вызов update функции
  - Сохранить message_id

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 4-5, 7-9

  **References**:
  - `handlers/commands.py:inbox_handler`

  **Acceptance Criteria**:
  - [ ] inbox_handler обновляет своё сообщение

  **Commit**: YES
  - Message: `feat: inbox_handler uses message updater`

---

- [ ] 7. Модификация clear_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `clear_handler`
  - После очистки вызвать update для `/tasks` и `/archive`

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 4-6, 8-9

  **References**:
  - `handlers/commands.py:clear_handler`

  **Acceptance Criteria**:
  - [ ] clear_handler обновляет сообщения после очистки

  **Commit**: YES
  - Message: `feat: clear_handler updates messages`

---

- [ ] 8. Модификация done_task_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `done_task_handler`
  - После выполнения задачи вызвать update для `/tasks`

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 4-7, 9

  **References**:
  - `handlers/commands.py:done_task_handler`

  **Acceptance Criteria**:
  - [ ] done_task_handler обновляет /tasks после выполнения

  **Commit**: YES
  - Message: `feat: done_task_handler updates /tasks`

---

- [ ] 9. Модификация undone_task_handler

  **What to do**:
  - Открыть `handlers/commands.py`, найти `undone_task_handler`
  - После возврата задачи вызвать update для `/tasks`

  **Recommended Agent Profile**:
  > **Category**: `quick`
  > **Parallelization**: Can run in parallel with Tasks 4-8

  **References**:
  - `handlers/commands.py:undone_task_handler`

  **Acceptance Criteria**:
  - [ ] undone_task_handler обновляет /tasks после возврата

  **Commit**: YES
  - Message: `feat: undone_task_handler updates /tasks`

---

### Wave 3: Timer Integration

- [ ] 10. Интеграция с таймером саммаризации

  **What to do**:
  - Найти места вызова саммаризации по таймеру
  - Добавить вызов update для `/tasks` после саммаризации

  **Must NOT do**:
  - Не нарушать существующую логику таймера

  **Recommended Agent Profile**:
  > **Category**: `unspecified-high`
  > - Reason: Интеграция с существующим таймером

  **Parallelization**:
  - **Can Run In Parallel**: NO (зависит от всех handler-ов)
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 4-9

  **References**:
  - `handlers/summarizer.py` - текущая реализация таймера
  - `bot/db/file_manager.py` - как работает саммаризация

  **Acceptance Criteria**:
  - [ ] Таймер саммаризации обновляет /tasks после выполнения

  **Commit**: YES
  - Message: `feat: timer summarization updates /tasks`

---

- [ ] 11. Обновление summarizer.py

  **What to do**:
  - Добавить вызов update в summarizer.py
  - Убедиться что message_id передаётся корректно

  **Recommended Agent Profile**:
  > **Category**: `unspecified-high`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Task 12
  - **Blocked By**: Task 10

  **References**:
  - `handlers/summarizer.py`

  **Acceptance Criteria**:
  - [ ] summarizer.py вызывает update после саммаризации

  **Commit**: YES
  - Message: `feat: summarizer updates messages`

---

### Wave 4: Testing & Polish

- [ ] 12. Unit tests для всех handler-ов

  **What to do**:
  - Написать unit tests для каждого handler-а
  - Проверить вызовы edit_message_text и answer

  **Recommended Agent Profile**:
  > **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Tasks 13, 14
  - **Blocked By**: Tasks 3-11

  **Acceptance Criteria**:
  - [ ] Все unit tests проходят
  - [ ] Coverage > 80%

  **Commit**: YES
  - Message: `test: add unit tests for message updates`

---

- [ ] 13. Integration tests

  **What to do**:
  - Написать integration tests с реальными вызовами
  - Проверить корректное обновление сообщений

  **Recommended Agent Profile**:
  > **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Task 15
  - **Blocked By**: Task 12

  **Acceptance Criteria**:
  - [ ] Все integration tests проходят

  **Commit**: YES
  - Message: `test: add integration tests`

---

- [ ] 14. Documentation update

  **What to do**:
  - Обновить README.md с информацией о новой функциональности
  - Добавить пример работы с динамическими сообщениями

  **Recommended Agent Profile**:
  > **Category**: `writing`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Task 15
  - **Blocked By**: Task 12

  **Acceptance Criteria**:
  - [ ] Документация обновлена
  - [ ] Примеры кода актуальны

  **Commit**: YES
  - Message: `docs: update documentation for dynamic messages`

---

- [ ] 15. Final verification

  **What to do**:
  - Запустить все тесты
  - Проверить ручное тестирование
  - Убедиться что все требования выполнены

  **Recommended Agent Profile**:
  > **Category**: `unspecified-high`

  **Acceptance Criteria**:
  - [ ] `bun test` проходит
  - [ ] `bun test --integration` проходит
  - [ ] Ручное тестирование подтверждает работу
  - [ ] Все "Must Have" выполнены
  - [ ] Все "Must NOT Have" absent

  **Commit**: NO (final verification)

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit**
  - Проверить все "Must Have" и "Must NOT Have"
  - Проверить evidence files

- [ ] F2. **Code Quality Review**
  - `tsc --noEmit` (если TypeScript)
  - `bun test`
  - Проверка на `as any`, `@ts-ignore`, console.log

- [ ] F3. **Real Manual QA**
  - Запустить /tasks несколько раз
  - Выполнить /done, /undone, /archive
  - Проверить что сообщения обновляются, а не дублируются

- [ ] F4. **Scope Fidelity Check**
  - Убедиться что ничего лишнего не добавлено
  - Проверить что все handler-ы обновлены

---

## Commit Strategy

- **1**: `feat: add message_id fields to UserSettings`
- **2**: `feat: add message updater helper functions`
- **3**: `feat: tasks_handler uses message updater`
- **4**: `feat: archive_handler uses message updater`
- **5**: `feat: notes_handler uses message updater`
- **6**: `feat: inbox_handler uses message updater`
- **7**: `feat: clear_handler updates messages`
- **8**: `feat: done_task_handler updates /tasks`
- **9**: `feat: undone_task_handler updates /tasks`
- **10**: `feat: timer summarization updates /tasks`
- **11**: `feat: summarizer updates messages`
- **12**: `test: add unit tests for message updates`
- **13**: `test: add integration tests`
- **14**: `docs: update documentation for dynamic messages`

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
bun test

# Run integration tests
bun test --integration

# Check linting
bun lint

# Check types (if TypeScript)
bun tsc --noEmit
```

### Final Checklist
- [ ] Все "Must Have" выполнены
- [ ] Все "Must NOT Have" absent
- [ ] Все тесты проходят
- [ ] Документация обновлена
- [ ] Ручное тестирование подтверждает работу

---

## Auto-Resolved Gaps

- **Error handling**: Если `edit_message_text` fails (message too old, deleted), просто отправить новое сообщение без ошибки
- **Message ID storage**: Хранить только последний message_id, без истории
- **Timer frequency**: Использовать существующий таймер саммаризации (не добавлять новый)

## Defaults Applied

- **Edge case handling**: Silently send new message if edit fails
- **No history**: Only store latest message_id per user
- **All handlers**: Update messages for all command handlers that change state

## Decisions Made

- **Storage**: Use `user_settings.py` for message_id storage
- **All commands**: Update messages for `/tasks`, `/archive`, `/notes`, `/inbox`, `/clear`, `/done_X`, `/undone_X`, `/summarize`
- **No history**: Only store latest message_id (not history)
- **Graceful degradation**: If edit fails, send new message silently
