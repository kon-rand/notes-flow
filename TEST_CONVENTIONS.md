# Test Conventions

## General Principles

- Write tests that are **readable, isolated, and deterministic**
- Each test should verify **one behavior** (single responsibility)
- Use **descriptive test names** that explain what is being tested
- Keep tests **independent** - no test should rely on another test's execution

## Naming Conventions

### Test Files
- Use `test_*.py` pattern
- Mirror the structure of the source code being tested
- Example: `tests/unit/utils/test_context_analyzer.py`

### Test Functions
- Prefix with `test_`
- Use lowercase with underscores: `test_function_name`
- Include the scenario being tested: `test_parse_json_with_prefix`

### Async Test Functions
- Prefix with `test_` and make them `async def`
- pytest-asyncio will handle execution automatically

## Test Structure

### Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange: Set up test data
    messages = [create_message("msg_1", 0, "Test")]
    client = OllamaClient()
    
    # Act: Execute the code under test
    result = client._format_messages(messages)
    
    # Assert: Verify the outcome
    assert "Test" in result
    assert "2026-03-06 14:00:00" in result
```

## Async Tests

- Use `async def` for async test functions
- pytest-asyncio with `asyncio_mode=auto` in `pytest.ini` handles execution
- Use `await` for async operations

```python
async def test_summarize_group_successful_task():
    messages = [create_message("msg_1", 0, "Task")]
    mock_response = {"response": '{"action": "create_task", "title": "Test"}'}
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OllamaClient()
        result = await client.summarize_group(messages)
        
        assert result["action"] == "create_task"
```

## Mocking

### Use unittest.mock for isolation

```python
from unittest.mock import AsyncMock, patch, MagicMock

@patch('module.function_to_mock')
def test_with_patch(mock_function):
    mock_function.return_value = "mocked_value"
    # Test code here
```

### Mocking Async HTTP Client

```python
with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
    mock_post.return_value = MagicMock(
        json=MagicMock(return_value=expected_json),
        raise_for_status=MagicMock()
    )
```

## Testing Edge Cases

Always test:
- Empty inputs: `[]`, `""`, `None`
- Single elements
- Boundary values
- Error conditions (exceptions, HTTP errors, timeouts)
- Invalid inputs

```python
def test_format_messages_empty():
    client = OllamaClient()
    result = client._format_messages([])
    assert result == ""

async def test_summarize_group_empty_messages():
    client = OllamaClient()
    result = await client.summarize_group([])
    assert result["action"] == "skip"
```

## Helper Functions

Create helper functions for common test setup patterns:

```python
def create_message(id: str, offset_minutes: int, content: str, sender_name: str = None) -> InboxMessage:
    """Helper for creating test messages"""
    return InboxMessage(
        id=id,
        timestamp=datetime(2026, 3, 6, 14, 0, 0) + timedelta(minutes=offset_minutes),
        from_user=123456789,
        sender_id=123456789,
        sender_name=sender_name,
        content=content,
        chat_id=-1001234567890
    )
```

## Assertions

- Use `assert` statements for verification
- Be specific about expected values
- Include meaningful error messages if needed

```python
assert result["action"] == "create_task"
assert result["title"] == "Подготовить отчёт"
assert len(result["tags"]) == 2
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/utils/test_ollama_client.py

# Run with verbose output
pytest -v

# Run specific test function
pytest -v -k test_parse_valid_json

# Run with coverage
pytest --cov=utils
```

## Test Coverage Goals

- Aim for high coverage on critical paths
- Test all public methods
- Test error handling paths
- Test async code paths

## Common Pitfalls

1. **Don't test implementation details** - test behavior
2. **Don't make tests dependent on each other** - each test must be independent
3. **Don't use real external services** - mock HTTP requests, database, etc.
4. **Don't ignore exceptions** - test error handling explicitly
5. **Don't hardcode timestamps** - use relative time or fixtures

## Pytest Fixtures (Optional)

For more complex setups, consider using pytest fixtures:

```python
import pytest

@pytest.fixture
def sample_messages():
    return [
        create_message("msg_1", 0, "First"),
        create_message("msg_2", 5, "Second"),
    ]

def test_example(sample_messages):
    client = OllamaClient()
    result = client._format_messages(sample_messages)
    assert "First" in result
```