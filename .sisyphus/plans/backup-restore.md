# Backup/Restore Feature

## TL;DR

> **Quick Summary**: Реализация команды `/backup` для создания ZIP архива всех данных пользователя и команды `/restore` для восстановления из архива с полной валидацией и подтверждением перед восстановлением.
> 
> **Deliverables**:
> - Команда `/backup` - создание и отправка ZIP архива
> - Команда `/restore` - прием ZIP файла, валидация, восстановление
> - Методы FileManager для работы с бэкапами
> - Валидатор формата бэкапов
> - Полная обработка ошибок с откатом
> - Тесты для всех сценариев
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: FileManager methods → Command handlers → Document handler → Tests

---

## Context

### Original Request
"Спроектируйте фичу: возможность бекапа данных пользователя через команду /backup. все таски, заметки, инбок, архивы и т.д. должны сложиться в zip архив и отправиться пользователю. так же нужна возможность восстановления из архива командой /restore и загрузкой архива следующим сообщением"

### Interview Summary

**Key Discussions**:
- **Conflict handling**: Спрашивать пользователя перед восстановлением (создавать предварительный бэкап)
- **Settings**: Восстанавливать только для текущего пользователя из user_settings.json
- **Validation**: Полная валидация + количественные метрики (сколько задач, заметок, сообщений)
- **Rollback**: Полное откатывание при любой ошибке восстановления

**Research Findings**:
- **Data storage**: Markdown файлы с YAML frontmatter в `data/{user_id}/`
- **Existing backup**: Частичный - только inbox.md через `save_backup()`
- **No file uploads**: Сейчас только текстовые сообщения, нужно добавить обработку документов
- **Command pattern**: Используются aiogram routers с Command фильтром

### Metis Review
**Identified Gaps** (addressed):
- **Validation**: Добавлена полная валидация формата YAML и целостности данных
- **Rollback strategy**: Реализовано создание предварительного бэкапа перед восстановлением
- **User confirmation**: Добавлен предварительный просмотр с количественными метриками
- **Settings handling**: Специальная логика для user_settings.json (только для текущего user_id)

---

## Work Objectives

### Core Objective
Реализовать полную систему бекапа и восстановления данных пользователя через Telegram команды с валидацией, подтверждением и откатом при ошибках.

### Concrete Deliverables
- Команда `/backup` в handlers/commands.py
- Команда `/restore` в handlers/commands.py
- Document handler в handlers/messages.py для приема ZIP файлов
- Методы FileManager для работы с бэкапами
- Валидатор формата бэкапов
- Тесты для всех сценариев

### Definition of Done
- [ ] Все тесты проходят (pytest)
- [ ] Команды добавлены в список бота
- [ ] Ручное тестирование бэкапа и восстановления
- [ ] Документация обновлена в README.md

### Must Have
- [x] Создание ZIP архива всех данных пользователя
- [x] Отправка ZIP через Telegram
- [x] Прием ZIP файла от пользователя
- [x] Валидация формата бэкапа
- [x] Предварительный просмотр с метриками
- [x] Подтверждение пользователя перед восстановлением
- [x] Автоматический бэкап перед восстановлением
- [x] Полное откатывание при ошибке
- [x] Обработка всех ошибок с пользовательскими сообщениями

### Must NOT Have (Guardrails)
- [ ] НЕ шифровать бэкапы (вне scope)
- [ ] НЕ хранить бэкапы на сервере (только через Telegram)
- [ ] НЕ выбиратьочное восстановление (только полный restore)
- [ ] НЕ использовать базы данных (только файловое хранилище)

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: YES (TDD)
- **Framework**: pytest + pytest-asyncio
- **If TDD**: Each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios (see TODO template below).
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **TUI/CLI**: Use interactive_bash (tmux) — Run command, send keystrokes, validate output
- **API/Backend**: Use Bash (curl) — Send requests, assert status + response fields
- **Library/Module**: Use Bash (bun/node REPL) — Import, call functions, compare output

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — core functionality):
├── Task 1: Add backup/restore commands to bot main.py [quick]
├── Task 2: Create FileManager.create_backup() method [quick]
├── Task 3: Create FileManager.restore_from_backup() method [unspecified-high]
└── Task 4: Add ZIP file handling utilities [quick]

Wave 2 (After Wave 1 — validation and user interaction):
├── Task 5: Create BackupValidator class [unspecified-high]
├── Task 6: Implement restore summary generation [quick]
├── Task 7: Implement rollback manager [unspecified-high]
└── Task 8: Add /backup command handler [quick]

Wave 3 (After Wave 2 — document handling and integration):
├── Task 9: Add document handler for /restore [quick]
├── Task 10: Add tests for backup methods [quick]
├── Task 11: Add tests for restore methods [unspecified-high]
├── Task 12: Add integration tests for commands [unspecified-high]
└── Task 13: Update README.md with documentation [quick]

Wave FINAL (After ALL tasks — verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1 | — | 8, 9 |
| 2 | — | 3, 8 |
| 3 | 2 | 4, 7, 11 |
| 4 | 2 | 3, 9 |
| 5 | 3 | 6, 11 |
| 6 | 5 | 7, 12 |
| 7 | 3, 6 | 11 |
| 8 | 1, 2 | — |
| 9 | 1, 3, 4 | — |
| 10 | 2 | — |
| 11 | 3, 5, 7 | — |
| 12 | 6, 8, 9 | — |
| 13 | — | — |

### Agent Dispatch Summary

- **Wave 1**: 
  - T1 → `quick`
  - T2 → `quick`
  - T3 → `unspecified-high`
  - T4 → `quick`
  
- **Wave 2**: 
  - T5 → `unspecified-high`
  - T6 → `quick`
  - T7 → `unspecified-high`
  - T8 → `quick`
  
- **Wave 3**: 
  - T9 → `quick`
  - T10 → `quick`
  - T11 → `unspecified-high`
  - T12 → `unspecified-high`
  - T13 → `quick`
  
- **Final**: 
  - F1 → `oracle`
  - F2 → `unspecified-high`
  - F3 → `unspecified-high`
  - F4 → `deep`

---

## TODOs

- [ ] 1. **Add backup/restore commands to bot main.py**

  **What to do**:
  - Import BotCommand from aiogram.types
  - Add backup and restore commands to commands list in bot/main.py
  - Register new handlers in main router
  - Test that commands appear in bot's command list

  **Must NOT do**:
  - Do not implement handlers yet
  - Do not add logic to command definitions

  **Recommended Agent Profile**:
  > Quick task requiring familiarity with aiogram bot setup and command registration patterns.
  - **Category**: `quick`
    - Reason: Simple configuration change, no complex logic
  - **Skills**: []
    - None needed - straightforward file edit
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed for this small change

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 4)
  - **Blocks**: Tasks 8, 9 (command handlers depend on registration)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `bot/main.py:20-30` - Existing BotCommand definitions pattern
  - `bot/main.py:80-100` - Router registration pattern

  **Acceptance Criteria**:
  - [ ] bot/main.py contains backup and restore BotCommand definitions
  - [ ] Commands registered in bot command list
  - [ ] No syntax errors in bot/main.py

  **QA Scenarios**:
  ```
  Scenario: Verify commands are registered
    Tool: Bash
    Preconditions: bot/main.py exists with command definitions
    Steps:
      1. Run python3 -c "from bot.main import bot; print([cmd.command for cmd in bot.get_my_commands()])"
    Expected Result: Output contains 'backup' and 'restore'
    Failure Indicators: AttributeError, commands not in list
    Evidence: .sisyphus/evidence/task-1-command-registration.txt
  ```

- [ ] 2. **Create FileManager.create_backup() method**

  **What to do**:
  - Add method to bot/db/file_manager.py
  - Collect all user files: inbox.md, tasks.md, notes.md, archive/*, inbox_backup/*
  - Create ZIP in memory using zipfile module
  - Return BytesIO object for Telegram sending
  - Handle errors gracefully

  **Must NOT do**:
  - Do not send file yet (that's handler's job)
  - Do not include user_settings.json (global file)

  **Recommended Agent Profile**:
  > Quick task with clear requirements and existing pattern to follow.
  - **Category**: `quick`
    - Reason: Straightforward file operations with zipfile
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 4)
  - **Blocks**: Tasks 3, 8 (restore and handler depend on this)
  - **Blocked By**: None

  **References**:
  - `bot/db/file_manager.py:save_backup()` - Existing backup pattern
  - `bot/db/file_manager.py:_get_user_dir()` - User directory helper

  **Acceptance Criteria**:
  - [ ] create_backup(user_id) method exists in FileManager
  - [ ] Returns BytesIO object with ZIP data
  - [ ] Includes inbox.md, tasks.md, notes.md, archive/*, inbox_backup/*
  - [ ] Handles empty directories gracefully

  **QA Scenarios**:
  ```
  Scenario: Create backup with user data
    Tool: Python REPL
    Preconditions: data/{user_id}/ exists with test files
    Steps:
      1. python3 -c "from bot.db.file_manager import FileManager; fm = FileManager(); result = fm.create_backup(123456)"
      2. import io; assert isinstance(result, io.BytesIO)
      3. import zipfile; zf = zipfile.ZipFile(result); files = zf.namelist()
      4. assert 'inbox.md' in files, 'tasks.md' in files, 'notes.md' in files
    Expected Result: BytesIO object with valid ZIP containing all user files
    Failure Indicators: FileNotFoundError, KeyError for missing files
    Evidence: .sisyphus/evidence/task-2-create-backup-success.bin

  Scenario: Create backup with no user data
    Tool: Python REPL
    Preconditions: data/{user_id}/ does not exist
    Steps:
      1. python3 -c "from bot.db.file_manager import FileManager; fm = FileManager(); result = fm.create_backup(999999)"
    Expected Result: Returns None or empty BytesIO
    Failure Indicators: Exception raised
    Evidence: .sisyphus/evidence/task-2-create-backup-empty.txt
  ```

- [ ] 3. **Create FileManager.restore_from_backup() method**

  **What to do**:
  - Add method to bot/db/file_manager.py
  - Accept ZIP file path as parameter
  - Extract to temporary directory
  - Call BackupValidator for validation
  - Create pre-restore backup for rollback
  - Extract to final location
  - Handle settings.json extraction for current user
  - Return success/failure with error message

  **Must NOT do**:
  - Do not auto-execute without validation
  - Do not skip rollback mechanism

  **Recommended Agent Profile**:
  > Complex task with multiple steps and error handling requirements.
  - **Category**: `unspecified-high`
    - Reason: Requires careful error handling and rollback logic
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential)
  - **Blocks**: Tasks 5, 7, 11 (validation, rollback, tests depend on this)
  - **Blocked By**: Task 2 (create_backup)

  **References**:
  - `bot/db/file_manager.py:_get_user_dir()` - User directory helper
  - `tests/integration/test_commands_archive.py` - Test patterns for error handling

  **Acceptance Criteria**:
  - [ ] restore_from_backup(user_id, zip_path) method exists
  - [ ] Extracts ZIP to temp directory
  - [ ] Validates contents using BackupValidator
  - [ ] Creates pre-restore backup
  - [ ] Extracts to final location
  - [ ] Handles user_settings.json correctly
  - [ ] Returns dict with success/error status

  **QA Scenarios**:
  ```
  Scenario: Restore from valid backup
    Tool: Python REPL
    Preconditions: data/{user_id}/ exists, valid backup ZIP created
    Steps:
      1. python3 -c "from bot.db.file_manager import FileManager; fm = FileManager(); result = fm.restore_from_backup(123456, '/tmp/backup.zip')"
      2. assert result['success'] == True
    Expected Result: Success dict with extracted files
    Failure Indicators: result['success'] == False
    Evidence: .sisyphus/evidence/task-3-restore-success.json

  Scenario: Restore from invalid backup
    Tool: Python REPL
    Preconditions: Corrupted ZIP file
    Steps:
      1. python3 -c "from bot.db.file_manager import FileManager; fm = FileManager(); result = fm.restore_from_backup(123456, '/tmp/invalid.zip')"
      2. assert result['success'] == False
    Expected Result: Error dict with message
    Failure Indicators: Exception raised instead of error dict
    Evidence: .sisyphus/evidence/task-3-restore-error.json
  ```

- [ ] 4. **Add ZIP file handling utilities**

  **What to do**:
  - Add helper functions for ZIP creation and extraction
  - Add utility for getting file sizes in human-readable format
  - Add utility for calculating checksums (optional)
  - Handle file path resolution

  **Must NOT do**:
  - Do not add complex compression algorithms (use standard zipfile)

  **Recommended Agent Profile**:
  > Quick utility functions with clear requirements.
  - **Category**: `quick`
    - Reason: Simple helper functions
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Tasks 3, 9 (restore and document handler use utilities)
  - **Blocked By**: None

  **References**:
  - `utils/markdown_parser.py` - Utility function patterns

  **Acceptance Criteria**:
  - [ ] Utility functions in utils/backup_utils.py
  - [ ] Human-readable file size formatting
  - [ ] Path resolution helpers
  - [ ] All functions have docstrings

  **QA Scenarios**:
  ```
  Scenario: Format file size
    Tool: Python REPL
    Preconditions: None
    Steps:
      1. from utils.backup_utils import format_file_size
      2. assert format_file_size(1024) == "1.0 KB"
      3. assert format_file_size(1048576) == "1.0 MB"
    Expected Result: Correct human-readable format
    Failure Indicators: Incorrect formatting
    Evidence: .sisyphus/evidence/task-4-file-size.txt
  ```

- [ ] 5. **Create BackupValidator class**

  **What to do**:
  - Create new file utils/backup_validator.py
  - Validate ZIP structure (required files exist)
  - Validate YAML frontmatter in each file
  - Validate data integrity (unique IDs, valid dates)
  - Generate statistics (counts of tasks, notes, messages)
  - Return validation result with detailed errors

  **Must NOT do**:
  - Do not modify files during validation
  - Do not skip validation of any file

  **Recommended Agent Profile**:
  > Complex validation logic with multiple checks.
  - **Category**: `unspecified-high`
    - Reason: Multiple validation rules and error reporting
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential)
  - **Blocks**: Tasks 6, 11 (summary and tests depend on this)
  - **Blocked By**: Task 3 (restore method)

  **References**:
  - `bot/db/models.py` - Data model definitions for validation
  - `utils/markdown_parser.py` - YAML parsing patterns

  **Acceptance Criteria**:
  - [ ] BackupValidator class in utils/backup_validator.py
  - [ ] Validates ZIP structure and required files
  - [ ] Validates YAML frontmatter format
  - [ ] Generates statistics (task count, note count, etc.)
  - [ ] Returns detailed validation result

  **QA Scenarios**:
  ```
  Scenario: Validate valid backup
    Tool: Python REPL
    Preconditions: Valid backup ZIP with all required files
    Steps:
      1. from utils.backup_validator import BackupValidator
      2. result = BackupValidator.validate('/tmp/valid_backup.zip')
      3. assert result['valid'] == True
      4. assert 'tasks_count' in result['stats']
    Expected Result: Valid validation result with stats
    Failure Indicators: result['valid'] == False
    Evidence: .sisyphus/evidence/task-5-validate-valid.json

  Scenario: Validate missing files
    Tool: Python REPL
    Preconditions: ZIP missing tasks.md
    Steps:
      1. from utils.backup_validator import BackupValidator
      2. result = BackupValidator.validate('/tmp/invalid_backup.zip')
      3. assert result['valid'] == False
      4. assert 'missing_files' in result['errors']
    Expected Result: Invalid result with error details
    Failure Indicators: result['valid'] == True
    Evidence: .sisyphus/evidence/task-5-validate-missing.json
  ```

- [ ] 6. **Implement restore summary generation**

  **What to do**:
  - Add method to generate summary text for user
  - Include counts: tasks, notes, inbox messages, archive entries
  - Show archive dates and task counts per date
  - Format nicely for Telegram display
  - Include warning about data replacement

  **Must NOT do**:
  - Do not show sensitive data (message content, etc.)
  - Do not include file checksums (user doesn't need them)

  **Recommended Agent Profile**:
  > Quick formatting task with clear output requirements.
  - **Category**: `quick`
    - Reason: Simple text formatting
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 7)
  - **Blocks**: Tasks 12 (integration tests)
  - **Blocked By**: Task 5 (validator)

  **References**:
  - `handlers/commands.py` - Message formatting patterns
  - `tests/integration/test_commands_archive.py` - Test message patterns

  **Acceptance Criteria**:
  - [ ] Summary includes all required statistics
  - [ ] Properly formatted for Telegram (emojis, line breaks)
  - [ ] Includes warning message
  - [ ] No sensitive data shown

  **QA Scenarios**:
  ```
  Scenario: Generate summary text
    Tool: Python REPL
    Preconditions: Valid validation result with stats
    Steps:
      1. from utils.backup_utils import generate_restore_summary
      2. summary = generate_restore_summary(validation_result)
      3. assert "Задач:" in summary
      4. assert "Заметки:" in summary
      5. assert "ВНИМАНИЕ" in summary
    Expected Result: Formatted summary string
    Failure Indicators: Missing required sections
    Evidence: .sisyphus/evidence/task-6-summary.txt
  ```

- [ ] 7. **Implement rollback manager**

  **What to do**:
  - Create RollbackManager class in utils/rollback_manager.py
  - Create backup of current data before restore
  - Store backup in temp location with timestamp
  - Implement rollback to backup function
  - Cleanup temp files after successful restore
  - Handle rollback errors gracefully

  **Must NOT do**:
  - Do not skip rollback creation
  - Do not delete backup until restore is confirmed successful

  **Recommended Agent Profile**:
  > Complex error handling with multiple failure modes.
  - **Category**: `unspecified-high`
    - Reason: Critical error recovery logic
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential)
  - **Blocks**: Tasks 11 (tests depend on this)
  - **Blocked By**: Task 3 (restore method)

  **References**:
  - `bot/db/file_manager.py` - File operations patterns
  - `tests/integration/test_commands_archive.py` - Error handling patterns

  **Acceptance Criteria**:
  - [ ] RollbackManager class exists
  - [ ] Creates backup before restore
  - [ ] Can rollback to backup
  - [ ] Cleans up temp files
  - [ ] Handles rollback errors

  **QA Scenarios**:
  ```
  Scenario: Create and rollback backup
    Tool: Python REPL
    Preconditions: data/{user_id}/ with test data
    Steps:
      1. from utils.rollback_manager import RollbackManager
      2. rm = RollbackManager(123456)
      3. rm.create_backup()
      4. # Modify some files
      5. rm.rollback()
      6. # Verify files restored
    Expected Result: Files restored to original state
    Failure Indicators: Files not restored correctly
    Evidence: .sisyphus/evidence/task-7-rollback.json
  ```

- [ ] 8. **Add /backup command handler**

  **What to do**:
  - Add handler to handlers/commands.py
  - Check for user authentication
  - Call FileManager.create_backup()
  - Send ZIP file using InputFile
  - Handle errors with user-friendly messages
  - Log backup creation

  **Must NOT do**:
  - Do not send ZIP as text (must be document)
  - Do not include file size in response (Telegram shows it)

  **Recommended Agent Profile**:
  > Quick task following existing command patterns.
  - **Category**: `quick`
    - Reason: Straightforward handler implementation
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 9)
  - **Blocks**: None
  - **Blocked By**: Tasks 1, 2 (command registration and create_backup)

  **References**:
  - `handlers/commands.py:50-80` - Existing command handler pattern
  - `handlers/commands.py:help_handler` - Example of sending response

  **Acceptance Criteria**:
  - [ ] /backup handler exists in handlers/commands.py
  - [ ] Uses InputFile to send ZIP
  - [ ] Handles errors gracefully
  - [ ] Logs backup creation

  **QA Scenarios**:
  ```
  Scenario: Execute /backup command
    Tool: Bash (curl to bot API)
    Preconditions: Bot running, user data exists
    Steps:
      1. curl -X POST "https://api.telegram.org/bot<TOKEN>/getMe"
      2. Send /backup command to bot
      3. Wait for response
      4. Check if document received
    Expected Result: ZIP file received by user
    Failure Indicators: Error message or no response
    Evidence: .sisyphus/evidence/task-8-backup-command.txt

  Scenario: /backup with no user data
    Tool: Bash (curl to bot API)
    Preconditions: Bot running, no user data
    Steps:
      1. Send /backup command to bot
    Expected Result: Error message "Нет данных для бэкапа"
    Failure Indicators: ZIP sent with no files
    Evidence: .sisyphus/evidence/task-8-backup-no-data.txt
  ```

- [ ] 9. **Add document handler for /restore**

  **What to do**:
  - Add document handler to handlers/messages.py
  - Check for F.document filter
  - Verify file extension is .zip
  - Download file to temp location
  - Call FileManager.restore_from_backup()
  - Show confirmation or error
  - Cleanup temp files

  **Must NOT do**:
  - Do not process non-ZIP files
  - Do not skip file type validation

  **Recommended Agent Profile**:
  > Quick task following existing message handler patterns.
  - **Category**: `quick`
    - Reason: Straightforward handler implementation
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11)
  - **Blocks**: None
  - **Blocked By**: Tasks 1, 3, 4 (command registration, restore method, utilities)

  **References**:
  - `handlers/messages.py` - Existing message handler pattern
  - `handlers/messages.py:message_handler` - Example of processing message

  **Acceptance Criteria**:
  - [ ] Document handler exists in handlers/messages.py
  - [ ] Validates ZIP file extension
  - [ ] Downloads file correctly
  - [ ] Calls restore method
  - [ ] Handles errors gracefully

  **QA Scenarios**:
  ```
  Scenario: Upload valid ZIP for restore
    Tool: Telegram (manual)
    Preconditions: Bot running, valid backup ZIP
    Steps:
      1. Send /restore command to bot
      2. Wait for confirmation request
      3. Send ZIP file
      4. Wait for response
    Expected Result: Success message with restored data
    Failure Indicators: Error message
    Evidence: .sisyphus/evidence/task-9-restore-success.txt

  Scenario: Upload non-ZIP file
    Tool: Telegram (manual)
    Preconditions: Bot running
    Steps:
      1. Send non-ZIP file to bot
    Expected Result: Error "Пожалуйста, загрузите ZIP-файл"
    Failure Indicators: File processed as backup
    Evidence: .sisyphus/evidence/task-9-restore-invalid.txt
  ```

- [ ] 10. **Add tests for backup methods**

  **What to do**:
  - Create tests/unit/db/test_backup.py
  - Test create_backup() with various scenarios
  - Test file inclusion/exclusion
  - Test error cases (no user data, empty directories)
  - Test ZIP file creation and structure

  **Must NOT do**:
  - Do not skip error case tests
  - Do not skip edge cases

  **Recommended Agent Profile**:
  > Quick test writing task following existing patterns.
  - **Category**: `quick`
    - Reason: Straightforward test implementation
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11, 12)
  - **Blocks**: None
  - **Blocked By**: Task 2 (create_backup method)

  **References**:
  - `tests/integration/test_commands_archive.py` - Test patterns
  - `tests/unit/bot/timers/` - Unit test structure

  **Acceptance Criteria**:
  - [ ] Test file created: tests/unit/db/test_backup.py
  - [ ] All backup methods tested
  - [ ] Error cases covered
  - [ ] ZIP structure verified

  **QA Scenarios**:
  ```
  Scenario: Run backup tests
    Tool: Bash
    Preconditions: tests/unit/db/test_backup.py exists
    Steps:
      1. pytest tests/unit/db/test_backup.py -v
    Expected Result: All tests pass
    Failure Indicators: Any test failures
    Evidence: .sisyphus/evidence/task-10-backup-tests.txt
  ```

- [ ] 11. **Add tests for restore methods**

  **What to do**:
  - Add tests to tests/unit/db/test_backup.py
  - Test restore_from_backup() with valid and invalid backups
  - Test rollback functionality
  - Test validation errors
  - Test user_settings.json handling

  **Must NOT do**:
  - Do not skip rollback tests
  - Do not skip validation error tests

  **Recommended Agent Profile**:
  > Complex test scenarios with multiple failure modes.
  - **Category**: `unspecified-high`
    - Reason: Multiple test scenarios and error handling
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 12)
  - **Blocks**: None
  - **Blocked By**: Tasks 3, 5, 7 (restore, validator, rollback)

  **References**:
  - `tests/unit/db/test_backup.py` - Backup test patterns
  - `tests/integration/test_commands_archive.py` - Integration test patterns

  **Acceptance Criteria**:
  - [ ] Restore methods tested
  - [ ] Rollback tested
  - [ ] Validation errors tested
  - [ ] All scenarios covered

  **QA Scenarios**:
  ```
  Scenario: Run restore tests
    Tool: Bash
    Preconditions: tests/unit/db/test_backup.py exists
    Steps:
      1. pytest tests/unit/db/test_backup.py::test_restore -v
    Expected Result: All restore tests pass
    Failure Indicators: Any test failures
    Evidence: .sisyphus/evidence/task-11-restore-tests.txt
  ```

- [ ] 12. **Add integration tests for commands**

  **What to do**:
  - Create tests/integration/test_backup_restore.py
  - Test /backup command end-to-end
  - Test /restore command end-to-end
  - Test user confirmation flow
  - Test error scenarios

  **Must NOT do**:
  - Do not skip end-to-end tests
  - Do not skip error scenario tests

  **Recommended Agent Profile**:
  > Complex integration test scenarios.
  - **Category**: `unspecified-high`
    - Reason: End-to-end testing with multiple steps
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11)
  - **Blocks**: None
  - **Blocked By**: Tasks 8, 9 (command handlers)

  **References**:
  - `tests/integration/test_commands_archive.py` - Integration test patterns
  - `tests/integration/test_command_order.py` - Command testing patterns

  **Acceptance Criteria**:
  - [ ] Integration tests created
  - [ ] /backup tested end-to-end
  - [ ] /restore tested end-to-end
  - [ ] Error scenarios tested

  **QA Scenarios**:
  ```
  Scenario: Run integration tests
    Tool: Bash
    Preconditions: tests/integration/test_backup_restore.py exists
    Steps:
      1. pytest tests/integration/test_backup_restore.py -v
    Expected Result: All integration tests pass
    Failure Indicators: Any test failures
    Evidence: .sisyphus/evidence/task-12-integration-tests.txt
  ```

- [ ] 13. **Update README.md with documentation**

  **What to do**:
  - Add /backup and /restore to commands table
  - Add backup/restore section with usage examples
  - Add troubleshooting section
  - Update features list

  **Must NOT do**:
  - Do not change existing documentation
  - Do not add untested features

  **Recommended Agent Profile**:
  > Quick documentation task.
  - **Category**: `quick`
    - Reason: Simple documentation update
  - **Skills**: []
    - None needed
  - **Skills Evaluated but Omitted**:
    - `git`: Not needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12)
  - **Blocks**: None
  - **Blocked By**: None

  **References**:
  - `README.md:Commands section` - Existing command documentation format
  - `README.md:Features section` - Existing features format

  **Acceptance Criteria**:
  - [ ] Commands table updated
  - [ ] Usage examples added
  - [ ] Troubleshooting section added
  - [ ] All changes reviewed

  **QA Scenarios**:
  ```
  Scenario: Verify documentation
    Tool: Bash
    Preconditions: README.md updated
    Steps:
      1. grep -A 5 "/backup" README.md
      2. grep -A 5 "/restore" README.md
    Expected Result: Commands documented with examples
    Failure Indicators: Missing documentation
    Evidence: .sisyphus/evidence/task-13-docs.txt
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

- **1**: `feat(backup): add backup/restore commands to bot` — bot/main.py, npm test
- **2**: `feat(backup): add FileManager.create_backup()` — bot/db/file_manager.py, npm test
- **3**: `feat(backup): add FileManager.restore_from_backup()` — bot/db/file_manager.py, npm test
- **4**: `feat(backup): add ZIP utilities` — utils/backup_utils.py, npm test
- **5**: `feat(backup): add BackupValidator` — utils/backup_validator.py, npm test
- **6**: `feat(backup): add restore summary generation` — utils/backup_utils.py, npm test
- **7**: `feat(backup): add RollbackManager` — utils/rollback_manager.py, npm test
- **8**: `feat(backup): add /backup command handler` — handlers/commands.py, npm test
- **9**: `feat(backup): add document handler for /restore` — handlers/messages.py, npm test
- **10**: `test(backup): add unit tests for backup methods` — tests/unit/db/test_backup.py
- **11**: `test(backup): add unit tests for restore methods` — tests/unit/db/test_backup.py
- **12**: `test(backup): add integration tests` — tests/integration/test_backup_restore.py
- **13**: `docs: update README.md with backup/restore docs` — README.md

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest

# Run backup-specific tests
pytest tests/unit/db/test_backup.py -v
pytest tests/integration/test_backup_restore.py -v

# Check that commands are registered
python3 -c "from bot.main import bot; print([cmd.command for cmd in bot.get_my_commands()])"

# Manual test
# 1. Send /backup to bot
# 2. Receive ZIP file
# 3. Send /restore to bot
# 4. Upload ZIP file
# 5. Verify data restored
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Manual testing completed
