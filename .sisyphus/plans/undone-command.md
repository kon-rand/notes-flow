# /undone_XXX команда для возврата задач

## TL;DR

> **Quick Summary**: Добавить команду `/undone_XXX` для возврата задач в статус "pending", включая архивные задачи (перемещение из archive в active)
> 
> **Deliverables**:
> - Методы file_manager.py для поиска и перемещения задач из архива
> - Хендлер команды /undone_XXX
> - Unit-тесты и integration-тесты
> - Обновленная документация

**Estimated Effort**: Medium  
**Parallel Execution**: YES - 3 waves  
**Critical Path**: T1 → T2 → T7 → T11 → T15 → user okay

---

## Context

### Original Request
"Создать команду /undone_XXX для возврата задач в невыполненное состояние, включая архивные задачи"

### Interview Summary
**Key Discussions**:
- Архивные задачи должны перемещаться обратно в active tasks.md (не просто обновлять статус в архиве)
- Полная валидация: проверять существование задачи в active и archive
- Тестирование: unit-тесты + integration-тесты

**Research Findings**:
- Существующий `/done_XXX` хендлер в commands.py:254-275
- Структура архива: archive/YYYY-MM-DD.md с YAML metadata
- Методы file_manager: archive_completed_tasks(), get_tasks_by_archive_dates(), get_tasks_by_archive_date()

---

## Work Objectives

### Core Objective
Реализовать команду `/undone_XXX` для возврата задач в статус "pending" с поддержкой архивных задач.

### Concrete Deliverables
- Методы file_manager.py: `find_task_in_tasks()`, `find_task_in_archive()`, `restore_task_from_archive()`, `remove_task_from_archive()`
- Хендлер `/undone_XXX` в commands.py
- Unit-тесты для file_manager
- Integration-тесты для хендлера
- Обновленная документация

### Definition of Done
- [ ] Все тесты проходят: `pytest tests/unit/test_file_manager.py tests/integration/test_restore_handler.py`
- [ ] Команда работает для active задач: `/undone_123` возвращает задачу в pending
- [ ] Команда работает для archive задач: `/undone_456` перемещает задачу из archive в active
- [ ] Валидация работает: ошибка при несуществующей задаче

### Must Have
- [x] Возврат active задач в pending
- [x] Перемещение archive задач в active с status="pending"
- [x] Валидация существования задачи
- [x] Unit + integration тесты

### Must NOT Have (Guardrails)
- [ ] Не создавать новые методы для notes (только tasks)
- [ ] Не добавлять поддержку других статусов (только pending)
- [ ] Не усложнять архитектуру - использовать существующие паттерны file_manager
- [ ] Не удалять completed_at при возврате в pending

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: YES (TDD)
- **Framework**: pytest
- **If TDD**: Each task follows RED → GREEN → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: N/A (backend)
- **TUI/CLI**: N/A
- **API/Backend**: Use Bash (python -c) - import modules, call methods, verify results
- **Library/Module**: Use pytest - run unit/integration tests

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - file manager methods):
├── Task 1: Add find_task_in_tasks() method [quick]
├── Task 2: Add find_task_in_archive() method [quick]
├── Task 3: Add restore_task_from_archive() method [deep]
├── Task 4: Add remove_task_from_archive() method [quick]
└── Task 5: Write unit tests for file_manager methods [unspecified-high]

Wave 2 (Handler implementation):
├── Task 6: Add /undone_XXX handler skeleton [quick]
├── Task 7: Implement task lookup logic (active + archive) [deep]
├── Task 8: Implement error handling and messages [quick]
└── Task 9: Write integration tests for handler [unspecified-high]

Wave 3 (Documentation + Final):
├── Task 10: Update README.md with new command [quick]
├── Task 11: Update help_handler with /undone_XXX [quick]
├── Task F1: Plan compliance audit [oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real manual QA [unspecified-high]
└── Task F4: Scope fidelity check [deep]

Critical Path: Task 1 → Task 3 → Task 7 → Task 11 → F1-F4 → user okay
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 5 (Wave 1)
```

### Dependency Matrix

- **1**: — — 3, 6, 5
- **2**: — — 3, 5
- **3**: 1, 2 — 7, 5
- **4**: 2 — 5
- **5**: 1, 2, 3, 4 — 7, 9
- **6**: — — 7, 9
- **7**: 3, 5, 6 — 9, 11
- **8**: 7 — 9
- **9**: 5, 6, 7, 8 — 11
- **10**: — — 11
- **11**: 9, 10 — F1-F4, user okay

### Agent Dispatch Summary

- **1**: **5** — T1-T4 → `quick`, T5 → `unspecified-high`
- **2**: **4** — T6 → `quick`, T7 → `deep`, T8 → `quick`, T9 → `unspecified-high`
- **3**: **4** — T10 → `quick`, T11 → `quick`, F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. Add `find_task_in_tasks()` method to file_manager.py

  **What to do**:
  - Implement method to search for task by ID in active tasks.md
  - Return Task object if found, None otherwise
  - Follow existing pattern from `read_tasks()` (file_manager.py:407-426)

  **Must NOT do**:
  - Don't modify task data, only search and return

  **Recommended Agent Profile**:
  > Simple file search operation
  - **Category**: `quick`
    - Reason: Single method implementation, straightforward logic
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find similar search patterns in file_manager
  - **Skills Evaluated but Omitted**:
    - `ast_grep_search`: Not needed - direct file edit is simpler

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential with T2)
  - **Blocks**: T3 (restore_task_from_archive depends on this)
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `bot/db/file_manager.py:407-426` - read_tasks() pattern for loading tasks
  - `bot/db/file_manager.py:428-438` - update_task_status() for file writing pattern

  **API/Type References**:
  - `bot/db/models.py:Task` - Task model structure and fields

  **WHY Each Reference Matters**:
  - file_manager.py:407-426 - Shows how to load and parse tasks from file
  - models.py:Task - Ensures correct Task object creation

  **Acceptance Criteria**:

  - [ ] Method signature: `def find_task_in_tasks(self, user_id: int, task_id: str) -> Task | None`
  - [ ] Returns Task object when found
  - [ ] Returns None when task not found
  - [ ] Method documented with docstring

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Find existing task in active tasks
    Tool: Bash (python -c)
    Preconditions: User has task_001 in tasks.md with status="completed"
    Steps:
      1. Create test user directory: mkdir -p data/123
      2. Create tasks.md with task_001
      3. Import file_manager and call find_task_in_tasks(123, "task_001")
      4. Verify returned task has id="task_001" and status="completed"
    Expected Result: Task object returned with correct data
    Failure Indicators: Returns None, wrong task, or raises exception
    Evidence: .sisyphus/evidence/task-1-find-existing-task.py-output.txt

  Scenario: Task not found in active tasks
    Tool: Bash (python -c)
    Preconditions: User has tasks.md but no task_999
    Steps:
      1. Create tasks.md with task_001
      2. Call find_task_in_tasks(123, "task_999")
      3. Verify return value is None
    Expected Result: Returns None
    Failure Indicators: Returns task, raises exception
    Evidence: .sisyphus/evidence/task-1-task-not-found.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Python script output showing method calls and results
  - [ ] Test execution logs

  **Commit**: YES | NO (groups with N)
  - Message: `feat(file-manager): add find_task_in_tasks method`
  - Files: `bot/db/file_manager.py`
  - Pre-commit: `pytest tests/unit/test_file_manager.py::test_find_task_in_tasks`

- [ ] 2. Add `find_task_in_archive()` method to file_manager.py

  **What to do**:
  - Implement method to search for task across all archive/*.md files
  - Return tuple (archive_date, Task) if found, None otherwise
  - Iterate through all dates from `get_archive_dates()`

  **Must NOT do**:
  - Don't modify task data, only search

  **Recommended Agent Profile**:
  > File iteration and search pattern
  - **Category**: `quick`
    - Reason: Follows existing archive iteration pattern
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find get_archive_dates() usage pattern

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: T3 (restore_task_from_archive depends on this)
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `bot/db/file_manager.py:581-607` - get_tasks_by_archive_date() for reading archive file
  - `bot/db/file_manager.py:569-579` - get_archive_dates() for listing archive dates

  **WHY Each Reference Matters**:
  - file_manager.py:581-607 - Shows how to read and parse archive task
  - file_manager.py:569-579 - Shows how to iterate through archive dates

  **Acceptance Criteria**:

  - [ ] Method signature: `def find_task_in_archive(self, user_id: int, task_id: str) -> tuple[str, Task] | None`
  - [ ] Returns (archive_date, Task) when found
  - [ ] Returns None when task not found in any archive
  - [ ] Method documented with docstring

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Find task in archive
    Tool: Bash (python -c)
    Preconditions: User has archive/2026-03-28.md with task_002 (completed)
    Steps:
      1. Create archive directory and file with task_002
      2. Call find_task_in_archive(123, "task_002")
      3. Verify returns (date, Task) tuple
      4. Verify Task has correct data
    Expected Result: Tuple with date and Task object
    Failure Indicators: Returns None, wrong date, or raises exception
    Evidence: .sisyphus/evidence/task-2-find-in-archive.py-output.txt

  Scenario: Task not found in any archive
    Tool: Bash (python -c)
    Preconditions: Archive exists but no task_999
    Steps:
      1. Create archive with task_001
      2. Call find_task_in_archive(123, "task_999")
      3. Verify return value is None
    Expected Result: Returns None
    Failure Indicators: Returns tuple, raises exception
    Evidence: .sisyphus/evidence/task-2-not-in-archive.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Python script output showing method calls and results
  - [ ] Archive file contents before/after

  **Commit**: YES | NO (groups with N)
  - Message: `feat(file-manager): add find_task_in_archive method`
  - Files: `bot/db/file_manager.py`
  - Pre-commit: `pytest tests/unit/test_file_manager.py::test_find_task_in_archive`

- [ ] 3. Add `restore_task_from_archive()` method to file_manager.py

  **What to do**:
  - Move task from archive to active tasks.md
  - Update status to "pending"
  - Clear archived_at field
  - Remove task from archive file
  - Return True on success, False on failure

  **Must NOT do**:
  - Don't clear other fields (created_at, content, tags, etc.)
  - Don't delete archive file if other tasks exist

  **Recommended Agent Profile**:
  > Complex file manipulation with multiple operations
  - **Category**: `deep`
    - Reason: Multiple file operations, data transformation, error handling
  - **Skills**: [`lsp_find_references`, `ast_grep_search`]
    - lsp_find_references: Find archive_completed_tasks() for archive writing pattern
    - ast_grep_search: Find all archive file writing patterns
  - **Skills Evaluated but Omitted**:
    - `lsp_rename`: Not needed - no symbol renaming

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (depends on T1, T2)
  - **Blocks**: T7 (handler depends on this)
  - **Blocked By**: T1 (find_task_in_tasks), T2 (find_task_in_archive)

  **References**:

  **Pattern References**:
  - `bot/db/file_manager.py:547-567` - archive_completed_tasks() for archive writing
  - `bot/db/file_manager.py:440-456` - delete_task() for task removal pattern
  - `bot/db/file_manager.py:428-438` - update_task_status() for status update pattern

  **WHY Each Reference Matters**:
  - archive_completed_tasks(): Shows how to append to archive file
  - delete_task(): Shows how to remove task from file
  - update_task_status(): Shows how to update task status

  **Acceptance Criteria**:

  - [ ] Method signature: `def restore_task_from_archive(self, user_id: int, task_id: str) -> bool`
  - [ ] Moves task from archive to active tasks.md
  - [ ] Updates status to "pending"
  - [ ] Clears archived_at field
  - [ ] Removes task from archive file (or removes date entry if last task)
  - [ ] Returns True on success, False if task not found

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Restore task from archive to active
    Tool: Bash (python -c)
    Preconditions: 
      - Archive has task_001 with status="completed", archived_at="2026-03-28"
      - Active tasks.md has no task_001
    Steps:
      1. Call restore_task_from_archive(123, "task_001")
      2. Verify return value is True
      3. Read active tasks.md - verify task_001 exists with status="pending"
      4. Verify archived_at is cleared
      5. Read archive file - verify task_001 removed
    Expected Result: Task moved to active with status="pending", archived_at cleared
    Failure Indicators: Returns False, task not moved, wrong status
    Evidence: .sisyphus/evidence/task-3-restore-from-archive.py-output.txt

  Scenario: Task not found in archive
    Tool: Bash (python -c)
    Preconditions: Archive exists but no task_999
    Steps:
      1. Call restore_task_from_archive(123, "task_999")
      2. Verify return value is False
      3. Verify no files modified
    Expected Result: Returns False, no changes
    Failure Indicators: Returns True, modifies files
    Evidence: .sisyphus/evidence/task-3-not-found.py-output.txt

  Scenario: Restore task that exists in both archive and active
    Tool: Bash (python -c)
    Preconditions:
      - Archive has task_001
      - Active tasks.md also has task_001 (duplicate)
    Steps:
      1. Call restore_task_from_archive(123, "task_001")
      2. Verify returns True
      3. Verify archive task removed
      4. Verify active task unchanged
    Expected Result: Archive task removed, active task stays
    Failure Indicators: Active task modified, archive task stays
    Evidence: .sisyphus/evidence/task-3-duplicate.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Archive file before/after comparison
  - [ ] Active tasks.md before/after comparison
  - [ ] Python script output

  **Commit**: YES | NO (groups with N)
  - Message: `feat(file-manager): add restore_task_from_archive method`
  - Files: `bot/db/file_manager.py`
  - Pre-commit: `pytest tests/unit/test_file_manager.py::test_restore_task_from_archive`

- [ ] 4. Add `remove_task_from_archive()` method to file_manager.py

  **What to do**:
  - Remove task from specific archive file
  - If archive file becomes empty, remove the file
  - Return True on success, False on failure

  **Must NOT do**:
  - Don't modify active tasks.md

  **Recommended Agent Profile**:
  > Simple file deletion pattern
  - **Category**: `quick`
    - Reason: Straightforward file operation
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find archive file deletion patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2)
  - **Blocks**: T3 (called from restore_task_from_archive)
  - **Blocked By**: T2 (find_task_in_archive)

  **References**:

  **Pattern References**:
  - `bot/db/file_manager.py:440-456` - delete_task() for file empty check
  - `bot/db/file_manager.py:518-535` - _write_file_with_metadata() for writing archive

  **WHY Each Reference Matters**:
  - delete_task(): Shows how to check if file is empty and delete
  - _write_file_with_metadata(): Shows how to write archive file

  **Acceptance Criteria**:

  - [ ] Method signature: `def remove_task_from_archive(self, user_id: int, archive_date: str, task_id: str) -> bool`
  - [ ] Removes task from archive file
  - [ ] Deletes archive file if empty
  - [ ] Returns True on success, False on failure

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Remove task from archive (file not empty)
    Tool: Bash (python -c)
    Preconditions: Archive has task_001 and task_002
    Steps:
      1. Call remove_task_from_archive(123, "2026-03-28", "task_001")
      2. Verify return value is True
      3. Read archive file - verify task_001 removed, task_002 remains
    Expected Result: Task removed, file remains with other tasks
    Failure Indicators: Returns False, task not removed, file deleted
    Evidence: .sisyphus/evidence/task-4-remove-not-empty.py-output.txt

  Scenario: Remove last task from archive (delete file)
    Tool: Bash (python -c)
    Preconditions: Archive has only task_001
    Steps:
      1. Call remove_task_from_archive(123, "2026-03-28", "task_001")
      2. Verify return value is True
      3. Verify archive file deleted
    Expected Result: File deleted
    Failure Indicators: Returns False, file not deleted
    Evidence: .sisyphus/evidence/task-4-remove-last.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Archive file before/after
  - [ ] File system check for deletion

  **Commit**: YES | NO (groups with N)
  - Message: `feat(file-manager): add remove_task_from_archive method`
  - Files: `bot/db/file_manager.py`
  - Pre-commit: `pytest tests/unit/test_file_manager.py::test_remove_task_from_archive`

- [ ] 5. Write unit tests for file_manager methods

  **What to do**:
  - Create test file: tests/unit/test_file_manager_restore.py
  - Test all new methods: find_task_in_tasks, find_task_in_archive, restore_task_from_archive, remove_task_from_archive
  - Test edge cases: task not found, duplicate tasks, empty archives

  **Must NOT do**:
  - Don't test archive_date_handler (that's integration test)
  - Don't modify existing tests

  **Recommended Agent Profile**:
  > Test writing for file operations
  - **Category**: `unspecified-high`
    - Reason: Test infrastructure, mocking, edge cases
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find existing file_manager tests pattern

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1-T4)
  - **Blocks**: Wave 2 (integration tests depend on unit tests passing)
  - **Blocked By**: T1, T2, T3, T4 (implementation must exist)

  **References**:

  **Pattern References**:
  - `tests/unit/test_file_manager.py` - Existing file_manager test patterns
  - `tests/unit/handlers/test_restore_handler.py` - Restore handler test template

  **WHY Each Reference Matters**:
  - test_file_manager.py: Shows test structure and fixtures
  - test_restore_handler.py: Shows restore-related test patterns

  **Acceptance Criteria**:

  - [ ] Test file created: tests/unit/test_file_manager_restore.py
  - [ ] All new methods have unit tests
  - [ ] Edge cases covered: not found, duplicates, empty archives
  - [ ] All tests pass: `pytest tests/unit/test_file_manager_restore.py`

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Run unit tests
    Tool: Bash (pytest)
    Preconditions: All file_manager methods implemented
    Steps:
      1. Run: pytest tests/unit/test_file_manager_restore.py -v
      2. Verify all tests PASS
      3. Verify no errors or warnings
    Expected Result: All tests pass
    Failure Indicators: Any test fails, errors, warnings
    Evidence: .sisyphus/evidence/task-5-unit-tests-pytest-output.txt

  Scenario: Test edge cases
    Tool: Bash (pytest)
    Preconditions: Test file with edge case tests
    Steps:
      1. Run: pytest tests/unit/test_file_manager_restore.py::test_task_not_found -v
      2. Run: pytest tests/unit/test_file_manager_restore.py::test_duplicate_task -v
      3. Run: pytest tests/unit/test_file_manager_restore.py::test_empty_archive -v
      4. Verify all edge case tests PASS
    Expected Result: All edge case tests pass
    Failure Indicators: Edge case tests fail
    Evidence: .sisyphus/evidence/task-5-edge-cases-pytest-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Pytest output with all tests passing
  - [ ] Coverage report for new methods

  **Commit**: YES | NO (groups with N)
  - Message: `test(file-manager): add unit tests for restore methods`
  - Files: `tests/unit/test_file_manager_restore.py`
  - Pre-commit: `pytest tests/unit/test_file_manager_restore.py`

- [ ] 6. Add `/undone_XXX` handler skeleton to commands.py

  **What to do**:
  - Create basic handler structure similar to `/done_XXX` (commands.py:254-275)
  - Extract task number from message text
  - Validate format (only digits)
  - Call file_manager methods

  **Must NOT do**:
  - Don't implement full logic yet (T7)
  - Don't add to help text yet (T11)

  **Recommended Agent Profile**:
  > Basic handler skeleton
  - **Category**: `quick`
    - Reason: Simple pattern copy from /done_XXX
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find /done_XXX handler

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (independent of T7 logic)
  - **Blocks**: T8, T9
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `handlers/commands.py:254-275` - /done_XXX handler
  - `handlers/commands.py:277-297` - /del_XXX handler

  **WHY Each Reference Matters**:
  - /done_XXX handler: Shows exact pattern for task number extraction and file_manager call

  **Acceptance Criteria**:

  - [ ] Handler decorated with `@router.message(F.text.startswith("/undone_"))`
  - [ ] Task number extracted and validated
  - [ ] Calls file_manager methods (placeholder for T7)
  - [ ] Basic success/error messages

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Handler registered and parses command
    Tool: Bash (python -c)
    Preconditions: commands.py with /undone_XXX handler
    Steps:
      1. Import router and verify handler registered
      2. Simulate message with text="/undone_123"
      3. Verify task_number extracted as "123"
      4. Verify task_id created as "task_123"
    Expected Result: Handler parses command correctly
    Failure Indicators: Handler not registered, wrong parsing
    Evidence: .sisyphus/evidence/task-6-handler-registered.py-output.txt

  Scenario: Invalid command format rejected
    Tool: Bash (python -c)
    Preconditions: Handler registered
    Steps:
      1. Simulate message with text="/undone_abc"
      2. Verify handler rejects (returns early or error)
    Expected Result: Invalid format rejected
    Failure Indicators: No rejection, exception raised
    Evidence: .sisyphus/evidence/task-6-invalid-format.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Handler registration verification
  - [ ] Command parsing output

  **Commit**: YES | NO (groups with N)
  - Message: `feat(commands): add /undone_XXX handler skeleton`
  - Files: `handlers/commands.py`
  - Pre-commit: `pytest tests/unit/handlers/test_commands.py`

- [ ] 7. Implement task lookup logic (active + archive)

  **What to do**:
  - In /undone_XXX handler, call find_task_in_tasks() first
  - If not found, call find_task_in_archive()
  - If found in archive, call restore_task_from_archive()
  - If not found anywhere, return error message

  **Must NOT do**:
  - Don't change handler structure (T6)
  - Don't add new error types

  **Recommended Agent Profile**:
  > Business logic integration
  - **Category**: `deep`
    - Reason: Combines multiple file_manager methods, error handling
  - **Skills**: [`lsp_find_references`, `ast_grep_search`]
    - lsp_find_references: Find error handling patterns in commands.py
    - ast_grep_search: Find all file_manager method calls

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (depends on T3, T6)
  - **Blocks**: T8, T9, T11
  - **Blocked By**: T3 (restore_task_from_archive), T6 (handler skeleton)

  **References**:

  **Pattern References**:
  - `handlers/commands.py:254-275` - /done_XXX for error message pattern
  - `bot/db/file_manager.py:581-607` - get_tasks_by_archive_date() for archive iteration

  **WHY Each Reference Matters**:
  - /done_XXX: Shows how to format error/success messages
  - file_manager archive methods: Shows how to handle archive data

  **Acceptance Criteria**:

  - [ ] Handler checks active tasks first
  - [ ] If not found, checks archive
  - [ ] Calls restore_task_from_archive() when found in archive
  - [ ] Returns appropriate success/error messages
  - [ ] Handles all error cases gracefully

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Restore active task (not in archive)
    Tool: Bash (python -c)
    Preconditions:
      - Active tasks.md has task_001 (completed)
      - Archive has no task_001
    Steps:
      1. Simulate /undone_1 message
      2. Verify handler calls find_task_in_tasks()
      3. Verify status updated to "pending"
      4. Verify success message shown
    Expected Result: Task status changed to pending
    Failure Indicators: Status not changed, error message shown
    Evidence: .sisyphus/evidence/task-7-restore-active.py-output.txt

  Scenario: Restore archive task
    Tool: Bash (python -c)
    Preconditions:
      - Active tasks.md has no task_002
      - Archive has task_002 (completed, archived_at="2026-03-28")
    Steps:
      1. Simulate /undone_2 message
      2. Verify handler calls find_task_in_archive()
      3. Verify restore_task_from_archive() called
      4. Verify task moved to active with status="pending"
      5. Verify success message shown
    Expected Result: Task moved from archive to active
    Failure Indicators: Task not moved, wrong status
    Evidence: .sisyphus/evidence/task-7-restore-archive.py-output.txt

  Scenario: Task not found anywhere
    Tool: Bash (python -c)
    Preconditions: No task_999 in active or archive
    Steps:
      1. Simulate /undone_999 message
      2. Verify handler searches both locations
      3. Verify error message shown "Задача не найдена"
    Expected Result: Error message shown, no changes
    Failure Indicators: No error, silent failure
    Evidence: .sisyphus/evidence/task-7-not-found.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Handler execution trace
  - [ ] File changes before/after
  - [ ] Success/error messages

  **Commit**: YES | NO (groups with N)
  - Message: `feat(commands): implement /undone_XXX logic`
  - Files: `handlers/commands.py`, `bot/db/file_manager.py`
  - Pre-commit: `pytest tests/integration/test_restore_handler.py`

- [ ] 8. Implement error handling and messages

  **What to do**:
  - Add specific error messages for different failure cases
  - Format success messages consistently with /done_XXX
  - Handle exceptions gracefully

  **Must NOT do**:
  - Don't change core logic (T7)
  - Don't add new error types

  **Recommended Agent Profile**:
  > Error handling and messaging
  - **Category**: `quick`
    - Reason: Simple message formatting
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find error message patterns in commands.py

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T7)
  - **Blocks**: T9, T11
  - **Blocked By**: T7 (logic must exist)

  **References**:

  **Pattern References**:
  - `handlers/commands.py:254-275` - /done_XXX error messages
  - `handlers/commands.py:277-297` - /del_XXX error messages

  **WHY Each Reference Matters**:
  - /done_XXX and /del_XXX: Shows consistent error message format

  **Acceptance Criteria**:

  - [ ] Error message for task not found: "Задача не найдена"
  - [ ] Error message for invalid format: "Неверный формат команды. Используйте: /undone_123"
  - [ ] Success message: "✅ Задача {number} возвращена в невыполненное состояние"
  - [ ] Exceptions caught and handled gracefully

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Error messages displayed correctly
    Tool: Bash (python -c)
    Preconditions: Handler with error handling
    Steps:
      1. Simulate /undone_123 for non-existent task
      2. Verify message: "Задача не найдена"
      3. Simulate /undone_abc for invalid format
      4. Verify message: "Неверный формат команды. Используйте: /undone_123"
    Expected Result: Correct error messages shown
    Failure Indicators: Wrong messages, no messages
    Evidence: .sisyphus/evidence/task-8-error-messages.py-output.txt

  Scenario: Success message displayed correctly
    Tool: Bash (python -c)
    Preconditions: Task exists and can be restored
    Steps:
      1. Simulate /undone_123 for existing task
      2. Verify message: "✅ Задача 123 возвращена в невыполненное состояние"
    Expected Result: Success message shown with correct number
    Failure Indicators: Wrong message, no message
    Evidence: .sisyphus/evidence/task-8-success-message.py-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Message output screenshots/prints

  **Commit**: YES | NO (groups with N)
  - Message: `feat(commands): add error handling and messages for /undone_XXX`
  - Files: `handlers/commands.py`
  - Pre-commit: `pytest tests/integration/test_restore_handler.py`

- [ ] 9. Write integration tests for handler

  **What to do**:
  - Create tests for /undone_XXX handler
  - Mock Telegram API (aiogram Message)
  - Test all scenarios: active task, archive task, not found, invalid format

  **Must NOT do**:
  - Don't test file_manager methods (unit tests cover that)
  - Don't add manual test scenarios

  **Recommended Agent Profile**:
  > Integration testing with mocks
  - **Category**: `unspecified-high`
    - Reason: Mocking Telegram API, integration scenarios
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find existing integration test patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T8)
  - **Blocks**: Wave 3 (documentation depends on tests passing)
  - **Blocked By**: T7 (logic must be implemented)

  **References**:

  **Pattern References**:
  - `tests/integration/test_restore_handler.py` - Existing restore handler tests
  - `tests/unit/handlers/test_commands.py` - Command handler test patterns

  **WHY Each Reference Matters**:
  - test_restore_handler.py: Shows archive-related integration tests
  - test_commands.py: Shows command handler test structure

  **Acceptance Criteria**:

  - [ ] Test file created: tests/integration/test_restore_handler.py (or updated)
  - [ ] Tests for all scenarios: active, archive, not found, invalid format
  - [ ] All tests pass: `pytest tests/integration/test_restore_handler.py`

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Run integration tests
    Tool: Bash (pytest)
    Preconditions: Handler implemented with all scenarios
    Steps:
      1. Run: pytest tests/integration/test_restore_handler.py -v
      2. Verify all tests PASS
      3. Verify no errors or warnings
    Expected Result: All integration tests pass
    Failure Indicators: Any test fails, errors, warnings
    Evidence: .sisyphus/evidence/task-9-integration-tests-pytest-output.txt

  Scenario: Test all integration scenarios
    Tool: Bash (pytest)
    Preconditions: Test file with all scenarios
    Steps:
      1. Run: pytest tests/integration/test_restore_handler.py::test_restore_active_task -v
      2. Run: pytest tests/integration/test_restore_handler.py::test_restore_archive_task -v
      3. Run: pytest tests/integration/test_restore_handler.py::test_task_not_found -v
      4. Run: pytest tests/integration/test_restore_handler.py::test_invalid_format -v
      5. Verify all scenario tests PASS
    Expected Result: All scenarios tested and passing
    Failure Indicators: Any scenario test fails
    Evidence: .sisyphus/evidence/task-9-scenarios-pytest-output.txt
  ```

  **Evidence to Capture**:
  - [ ] Pytest output with all tests passing
  - [ ] Mock verification logs

  **Commit**: YES | NO (groups with N)
  - Message: `test(integration): add integration tests for /undone_XXX handler`
  - Files: `tests/integration/test_restore_handler.py`
  - Pre-commit: `pytest tests/integration/test_restore_handler.py`

- [ ] 10. Update README.md with new command

  **What to do**:
  - Add /undone_XXX to commands table in README.md
  - Add description: "Вернуть задачу в невыполненное состояние"
  - Add example usage

  **Must NOT do**:
  - Don't change other sections
  - Don't add unnecessary details

  **Recommended Agent Profile**:
  > Documentation update
  - **Category**: `quick`
    - Reason: Simple text addition
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find commands table in README

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (independent of T11)
  - **Blocks**: None
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `README.md:100-120` - Commands table section

  **WHY Each Reference Matters**:
  - README.md commands table: Shows exact format and structure

  **Acceptance Criteria**:

  - [ ] /undone_XXX added to commands table
  - [ ] Description: "Вернуть задачу в невыполненное состояние"
  - [ ] Example usage shown
  - [ ] README.md still valid markdown

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: README.md updated correctly
    Tool: Bash (grep)
    Preconditions: README.md with /undone_XXX
    Steps:
      1. Run: grep "/undone_XXX" README.md
      2. Verify command appears in table
      3. Verify description present
    Expected Result: Command documented in README
    Failure Indicators: Command not found, wrong format
    Evidence: .sisyphus/evidence/task-10-readme-grep-output.txt

  Scenario: Markdown validation
    Tool: Bash (python -m markdown)
    Preconditions: README.md updated
    Steps:
      1. Run: python -m markdown README.md > /dev/null
      2. Verify no errors
    Expected Result: Valid markdown
    Failure Indicators: Markdown errors
    Evidence: .sisyphus/evidence/task-10-markdown-validation-output.txt
  ```

  **Evidence to Capture**:
  - [ ] grep output showing /undone_XXX in README
  - [ ] Markdown validation output

  **Commit**: YES | NO (groups with N)
  - Message: `docs(readme): add /undone_XXX command documentation`
  - Files: `README.md`
  - Pre-commit: `python -m markdown README.md > /dev/null`

- [ ] 11. Update help_handler with /undone_XXX

  **What to do**:
  - Add /undone_XXX to help_handler text (commands.py:59-87)
  - Add to "Управление задачами" section
  - Format: `/undone_XXX - вернуть задачу в невыполненное состояние`

  **Must NOT do**:
  - Don't change other commands
  - Don't add to /start handler (T5 already covers that)

  **Recommended Agent Profile**:
  > Documentation update
  - **Category**: `quick`
    - Reason: Simple text addition
  - **Skills**: [`lsp_find_references`]
    - lsp_find_references: Find help_handler text section

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T10)
  - **Blocks**: None
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `handlers/commands.py:74-78` - Help text section for task management

  **WHY Each Reference Matters**:
  - commands.py:74-78: Shows exact format for task management commands

  **Acceptance Criteria**:

  - [ ] /undone_XXX added to help_handler text
  - [ ] Description: "вернуть задачу в невыполненное состояние"
  - [ ] Added to "Управление задачами" section
  - [ ] Help text still valid and readable

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Help text updated correctly
    Tool: Bash (grep)
    Preconditions: commands.py with updated help
    Steps:
      1. Run: grep "/undone_XXX" handlers/commands.py
      2. Verify command appears in help text
      3. Verify description present
    Expected Result: Command documented in help
    Failure Indicators: Command not found, wrong format
    Evidence: .sisyphus/evidence/task-11-help-grep-output.txt

  Scenario: Help handler works
    Tool: Bash (python -c)
    Preconditions: help_handler with /undone_XXX
    Steps:
      1. Simulate /help command
      2. Verify response includes /undone_XXX
      3. Verify description correct
    Expected Result: Help shows /undone_XXX
    Failure Indicators: Command not in help, wrong description
    Evidence: .sisyphus/evidence/task-11-help-handler-output.txt
  ```

  **Evidence to Capture**:
  - [ ] grep output showing /undone_XXX in commands.py
  - [ ] Help command output

  **Commit**: YES | NO (groups with N)
  - Message: `docs(help): add /undone_XXX to help text`
  - Files: `handlers/commands.py`
  - Pre-commit: `pytest tests/unit/handlers/test_commands.py::test_help_handler`

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

- **1**: `feat(file-manager): add find_task_in_tasks method` — bot/db/file_manager.py, pytest tests/unit/test_file_manager.py::test_find_task_in_tasks
- **2**: `feat(file-manager): add find_task_in_archive method` — bot/db/file_manager.py, pytest tests/unit/test_file_manager.py::test_find_task_in_archive
- **3**: `feat(file-manager): add restore_task_from_archive method` — bot/db/file_manager.py, pytest tests/unit/test_file_manager.py::test_restore_task_from_archive
- **4**: `feat(file-manager): add remove_task_from_archive method` — bot/db/file_manager.py, pytest tests/unit/test_file_manager.py::test_remove_task_from_archive
- **5**: `test(file-manager): add unit tests for restore methods` — tests/unit/test_file_manager_restore.py, pytest tests/unit/test_file_manager_restore.py
- **6**: `feat(commands): add /undone_XXX handler skeleton` — handlers/commands.py, pytest tests/unit/handlers/test_commands.py
- **7**: `feat(commands): implement /undone_XXX logic` — handlers/commands.py, bot/db/file_manager.py, pytest tests/integration/test_restore_handler.py
- **8**: `feat(commands): add error handling and messages for /undone_XXX` — handlers/commands.py, pytest tests/integration/test_restore_handler.py
- **9**: `test(integration): add integration tests for /undone_XXX handler` — tests/integration/test_restore_handler.py, pytest tests/integration/test_restore_handler.py
- **10**: `docs(readme): add /undone_XXX command documentation` — README.md
- **11**: `docs(help): add /undone_XXX to help text` — handlers/commands.py, pytest tests/unit/handlers/test_commands.py::test_help_handler

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest tests/unit/test_file_manager_restore.py tests/integration/test_restore_handler.py

# Test /undone_XXX command manually
# (Send /undone_123 to bot and verify task restored)
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Documentation updated (README.md, help)
- [ ] No type errors (mypy)
- [ ] No lint errors (ruff)
