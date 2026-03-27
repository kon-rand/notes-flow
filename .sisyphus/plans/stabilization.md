# Stabilization Plan for Telegram Bot Project

## TL;DR
> This plan introduces a robust local Docker‑Compose workflow that enforces test and coverage checks before any new image is promoted to production. It blocks the deployment if the tests fail or coverage falls below 80 %, while keeping the previous image running. The plan also defines a comprehensive regression test suite for end‑to‑end bot interactions and ensures that the pre‑deploy script is executed automatically.

> **Key deliverables**:
> - `pre‑deploy.sh` – runs `pytest` with coverage and enforces 80 % threshold.
> - Docker‑Compose update – a test service that pulls the new image and runs the pre‑deploy script.
> - Regression e2e test suite for bot commands and task management.
> - Updated documentation and CI‑style local pipeline.

> **Estimated effort**: Medium (≈ 5‑7 hours of planning + execution).

## Context

- **Project**: Telegram bot written in Python, using `pytest` for unit and integration tests.
- **Deployment**: Direct‑to‑production via Docker‑Compose on a single machine.
- **Current gaps**: No coverage monitoring, no pre‑deploy checks, no regression e2e suite, no local pipeline to replace the old container only after tests pass.

## Work Objectives

1. **Add coverage instrumentation** and enforce an 80 % threshold via a pre‑deploy script.
2. **Create a Docker‑Compose test service** that pulls the new image, runs the pre‑deploy script, and only replaces the old container if the script succeeds.
3. **Implement a regression e2e test suite** covering critical bot commands and task management flows.
4. **Update documentation** to reflect the new deployment workflow.
5. **Ensure the old container continues running** while tests are executed.

## Verification Strategy

- **Automated**: All tasks must include agent‑executed QA scenarios. No human intervention allowed.
- **Coverage**: `coverage` must report ≥80 % in the console.
- **Pre‑deploy**: Script must exit non‑zero if tests fail or coverage is below threshold.
- **Docker Compose**: The new container should only start the main bot service after the pre‑deploy script succeeds.

## Execution Strategy

- **Parallelism**: Tasks are grouped into waves; each wave can run concurrently as long as dependencies are satisfied.
- **Wave 1**: Set up coverage and pre‑deploy script.
- **Wave 2**: Docker‑Compose and regression tests.
- **Wave 3**: Final verification and documentation.

---

## TODOs

- [ ] 1. **Add coverage.py to requirements.txt**
  
  **What to do**: Add `coverage==7.5.0` (or latest) to `requirements.txt` and commit.
  
  **Must NOT do**: Remove existing test dependencies.
  
  **Recommended Agent Profile**:
  > Category: `quick`
  > Skills: `pip`, `git`
  
  **Parallelization**:
  > Can Run In Parallel: YES (no dependencies)
  > Parallel Group: Wave 1
  > Blocks: None
  > Blocked By: None
  
  **References**:
  - `requirements.txt`
  
  **Acceptance Criteria**:
  - `coverage` appears in `requirements.txt`.
  - `pip install -r requirements.txt` succeeds without errors.
  
  **QA Scenarios**:
  ```
  Scenario: Verify coverage installation
    Tool: Bash
    Steps:
      1. Run `pip install -r requirements.txt` in a clean virtualenv.
      2. Assert that `coverage` package is installed.
    Expected Result: `coverage` is listed in pip list.
    Evidence: .sisyphus/evidence/coverage-install.txt
  ```

- [ ] 2. **Create pre‑deploy.sh script**
  
  **What to do**: Create a bash script that runs `pytest --cov=modules --cov-report=term-missing` and exits with non‑zero if tests fail or coverage < 80%.
  
  **Must NOT do**: Hard‑code coverage thresholds; allow script to be overridden via env.
  
  **Recommended Agent Profile**:
  > Category: `quick`
  > Skills: `bash`, `pytest`
  
  **Parallelization**:
  > Can Run In Parallel: YES
  > Parallel Group: Wave 1
  > Blocks: None
  > Blocked By: None
  
  **References**:
  - `pytest.ini`
  - `tests/`
  
  **Acceptance Criteria**:
  - Script exists at `pre-deploy.sh` and is executable.
  - Running it in a clean environment runs all tests and exits 0 when coverage ≥80%.
  
  **QA Scenarios**:
  ```
 6580%.
  
  **QA Scenarios**:
  ```
  Scenario: Pre‑deploy passes with sufficient coverage
    Tool: Bash
    Steps:
      1. Run `./pre-deploy.sh`.
      2. Assert exit code 0.
    Expected Result: Exit code 0.
    Evidence: .sisyphus/evidence/predeploy-pass.txt
  ```
  ```
  Scenario: Pre‑deploy fails on low coverage
    Tool: Bash
    Steps:
      1. Temporarily modify `pre-deploy.sh` to set threshold 100%.
      2. Run `./pre-deploy.sh`.
      3. Assert exit code non‑zero.
    Expected Result: Exit code non‑zero.
    Evidence: .sisyphus/evidence/predeploy-fail.txt
  ```

- [ ] 3. **Update docker-compose.yml to include test service**
  
  **What to do**: Add a new service `bot-test` that pulls the new image, runs `pre‑deploy.sh`, and only starts the main bot service if the script succeeds.
  
  **Must NOT do**: Stop the old bot container before tests finish.
  
  **Recommended Agent Profile**:
  > Category: `quick`
  > Skills: `docker-compose`
  
  **Parallelization**:
  > Can Run In Parallel: YES
  > Parallel Group: Wave 1
  > Blocks: None
  > Blocked By: None
  
  **References**:
  - `docker-compose.yml`
  - `pre-deploy.sh`
  
  **Acceptance Criteria**:
  - `docker-compose.yml` contains a `bot-test` service.
  - The service runs `pre‑deploy.sh` before launching the bot.
  - If `pre‑deploy.sh` exits non‑zero, the service fails and the old bot remains running.
  
  **QA Scenarios**:
  ```
  Scenario: Docker test service passes
    Tool: Docker Compose
    Steps:
      1. Run `docker compose up --build bot-test`.
      2. Assert the container exits 0.
      3. Verify the main bot service is started.
    Expected Result: Bot service runs.
    Evidence: .sisyphus/evidence/docker-test-pass.txt
  ```
  ```
  Scenario: Docker test service fails
    Tool: Docker Compose
    Steps:
      1. Introduce a failing test.
      2. Run `docker compose up --build bot-test`.
      3. Assert the container exits non‑zero.
      4. Verify old bot container continues.
    Expected Result: Bot service not started.
    Evidence: .sisyphus/evidence/docker-test-fail.txt
  ```

- [ ] 4. **Add coverage threshold config**
  
  **What to do**: Ensure the coverage threshold is configurable via an environment variable `COVERAGE_THRESHOLD`, default 80.
  
  **Must NOT do**: Hard‑code threshold.
  
  **Recommended Agent Profile**:
  > Category: `quick`
  > Skills: `bash`
  
  **Parallelization**:
  > Can Run In Parallel: YES
  > Parallel Group: Wave 1
  > Blocks: None
  > Blocked By: None
  
  **References**:
  - `pre-deploy.sh`
  
  **Acceptance Criteria**:
  - `pre-deploy.sh` reads `COVERAGE_THRESHOLD` from env or defaults to 80.
  - Changing the variable alters the threshold.
  
  **QA Scenarios**:
  ```
  Scenario: Threshold via env
    Tool: Bash
    Steps:
      1. Export `COVERAGE_THRESHOLD=90`.
      2. Run `./pre-deploy.sh`.
      3. Assert exit code based on coverage.
    Expected Result: Exit code reflects 90% threshold.
    Evidence: .sisyphus/evidence/threshold-env.txt
  ```

- [ ] 5. **Implement regression e2e tests**\n  \n  **What to do**: Write tests using `pytest` + `pytest-asyncio` that simulate bot commands (e.g., `/start`, `/add_task`, `/list_tasks`, `/complete_task`) and validate state changes.\n  \n  **Must NOT do**: Hard‑code test data that is not representative of real usage.\n  \n  **Recommended Agent Profile**:\n  > Category: `unspecified-high`\n  > Skills: `pytest`, `asyncio`, `bot`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `tests/`\n  - `bot/app.py`\n  \n  **Acceptance Criteria**:\n  - Tests exist in `tests/test_e2e.py`.\n  - All tests pass with coverage ≥80%.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Bot responds to /start command\n    Tool: Bash (curl)\n    Steps:\n      1. Send POST to `/api/telegram/webhook` with payload for `/start`.\n      2. Assert response contains welcome message.\n    Expected Result: Welcome message returned.\n    Evidence: .sisyphus/evidence/e2e-start.txt\n  ```\n  \n- [ ] 6. **Update README with deployment instructions**\n  \n  **What to do**: Add a new section that explains the pre‑deploy script, Docker‑Compose test workflow, and how to run locally.\n  \n  **Must NOT do**:6580%.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Bot responds to /start command\n    Tool: Bash (curl)\n    Steps:\n      1. Send POST to `/api/telegram/webhook` with payload for `/start`.\n      2. Assert response contains welcome message.\n    Expected Result: Welcome message returned.\n    Evidence: .sisyphus/evidence/e2e-start.txt\n  ```\n  \n- [ ] 6. **Update README with deployment instructions**\n  \n  **What to do**: Add a new section that explains the pre‑deploy script, Docker‑Compose test workflow, and how to run locally.\n  \n  **Must NOT do**: Remove existing README content.\n  \n  **Recommended Agent Profile**:\n  > Category: `writing`\n  > Skills: `markdown`, `documentation`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `README.md`\n  \n  **Acceptance Criteria**:\n  - README contains a section titled `Local Deployment Workflow`.\n  - Instructions are accurate and testable.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Verify README deployment section exists\n    Tool: Bash\n    Steps:\n      26580%.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Bot responds to /start command\n    Tool: Bash (curl)\n    Steps:\n      1. Send POST to `/api/telegram/webhook` with payload for `/start`.\n      2. Assert response contains welcome message.\n    Expected Result: Welcome message returned.\n    Evidence: .sisyphus/evidence/e2e-start.txt\n  ```\n  \n- [ ] 6. **Update README with deployment instructions**\n  \n  **What to do**: Add a new section that explains the pre‑deploy script, Docker‑Compose test workflow, and how to run locally.\n  \n  **Must NOT do**: Remove existing README content.\n  \n  **Recommended Agent Profile**:\n  > Category: `writing`\n  > Skills: `markdown`, `documentation`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `README.md`\n  \n  **Acceptance Criteria**:\n  - README contains a section titled `Local Deployment Workflow`.\n  - Instructions are accurate and testable.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Verify README deployment section exists\n    Tool: Bash\n    Steps:\n      1. Grep `Local Deployment Workflow` in README.md.\n      2. Assert the section is present.\n    Expected Result: Section found.\n    Evidence: .sisyphus/evidence/readme-deploy.txt\n  ```\n  \n- [ ] 7. **Create docker-compose override for local testing**\n  \n  **What to do**: Add `docker-compose.test.yml` that extends the base compose file, setting environment variables for testing and mounting the local source code.\n  \n  **Must NOT do**: Duplicate entire compose configuration.\n  \n  **Recommended Agent Profile**:\n  > Category: `quick`\n  > Skills: `docker-compose`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `docker-compose.yml`\n  \n  **Acceptance Criteria**:\n  - `docker-compose.test.yml` exists.\n  - Running `docker compose -f docker-compose.yml -f docker-compose.test.yml up` mounts source code.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Test compose mounts source\n    Tool: Docker Compose\n    Steps:\n      1. Run `docker compose -f docker-compose.yml -f docker-compose.test.yml up -d`.\n      2. Exec into the test container and check if source files are present.\n    Expected Result: Source files present.\n    Evidence: .sisyphus/evidence/compose-mount.txt\n  ```\n  \n- [ ] 8. **Create test Dockerfile**\n  \n  **What to do**: Build a lightweight image that installs dependencies, copies source, runs `pre‑deploy.sh`, and exits.\n  \n  **Must NOT do**: Include production code not needed for tests.\n  \n  **Recommended Agent Profile**:\n  > Category: `quick`\n  > Skills: `dockerfile`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `Dockerfile`\n  - `pre-deploy.sh`\n  \n  **Acceptance Criteria**:\n  - `Dockerfile.test` exists.\n  - Building it produces a working image that runs `pre‑deploy.sh`.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: Build test image and run pre‑deploy\n    Tool: Docker Build\n    Steps:\n      1. Run `docker build -f Dockerfile.test -t bot-test .`\n      2. Run `docker run --rm bot-test`.\n    Expected Result: Pre‑deploy script runs and exits.\n    Evidence: .sisyphus/evidence/docker-test-build.txt\n  ```\n  \n- [ ] 9. **Update CI config (if applicable)**\n  \n  **What to do**: Add a local CI workflow that triggers the pre‑deploy script and the regression tests.\n  \n  **Must NOT do**: Remove existing CI config.\n  \n  **Recommended Agent Profile**:\n  > Category: `quick`\n  > Skills: `yaml`\n  \n  **Parallelization**:\n  > Can Run In Parallel: YES\n  > Parallel Group: Wave 2\n  > Blocks: None\n  > Blocked By: None\n  \n  **References**:\n  - `.github/workflows/ci.yml` (if exists)\n  \n  **Acceptance Criteria**:\n  - CI config triggers `pre-deploy.sh` and e2e tests on push.\n  \n  **QA Scenarios**:\n  ```\n  Scenario: CI runs pre‑deploy\n    Tool: GitHub Actions\n    Steps:\n      1. Commit a change to a feature branch.\n      2. Observe the CI workflow runs.\n    Expected Result: Workflow completes with success if tests pass.\n    Evidence: .sisyphus/evidence/ci-run.txt\n  ```\n\n---\n
## Final Verification Wave

---

## Commit Strategy

---

## Success Criteria

- All tests pass.
- Coverage ≥80 %.
- `pre‑deploy.sh` blocks deployment on failure.
- Docker‑Compose replaces old container only after successful pre‑deploy.
- Documentation updated.
- Regression e2e tests cover bot commands and task management.

