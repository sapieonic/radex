# Unit Tests

This directory contains unit tests for the RADEX server application. Unit tests are fast, isolated tests that don't require external dependencies like databases or external services.

## Structure

The unit test directory mirrors the application structure:

```
tests/unit/
├── conftest.py              # Shared fixtures and test configuration
├── api/                     # API endpoint tests
│   └── test_auth.py
├── core/                    # Core functionality tests
│   └── test_security.py
├── schemas/                 # Pydantic schema validation tests
│   └── test_rag.py
├── services/                # Business logic tests
│   └── test_permission_service.py
└── utils/                   # Utility function tests
    └── test_text_chunking.py
```

## Running Tests

### Run all unit tests
```bash
cd server
source myenv/bin/activate  # or venv/bin/activate
pytest tests/unit/ -v
```

### Run specific test file
```bash
pytest tests/unit/core/test_security.py -v
```

### Run specific test class or method
```bash
pytest tests/unit/core/test_security.py::TestPasswordHashing -v
pytest tests/unit/core/test_security.py::TestPasswordHashing::test_hash_password -v
```

### Run with coverage
```bash
pytest tests/unit/ --cov=app --cov-report=html --cov-report=term
```

## Test Categories

### 1. Schema Tests (`schemas/`)
- Validates Pydantic models
- Tests data validation rules
- Tests serialization/deserialization
- Example: `test_rag.py` - validates RAG query and chat message schemas

### 2. Core Tests (`core/`)
- Tests security functions (hashing, JWT)
- Tests exception handling
- Tests dependency injection logic
- Example: `test_security.py` - validates password hashing and JWT tokens

### 3. Utils Tests (`utils/`)
- Tests utility functions
- Tests text processing
- Tests file operations
- Example: `test_text_chunking.py` - validates text chunking algorithms

### 4. Service Tests (`services/`)
- Tests business logic
- Uses mocked database sessions
- Tests permission checking
- Example: `test_permission_service.py` - validates RBAC logic

### 5. API Tests (`api/`)
- Tests API route logic
- Tests request/response handling
- Tests error handling
- Example: `test_auth.py` - validates authentication endpoints

## Writing New Tests

### 1. Create test file matching source file
```
app/utils/new_utility.py  →  tests/unit/utils/test_new_utility.py
```

### 2. Use available fixtures
```python
def test_something(mock_db, sample_user):
    # Use fixtures from conftest.py
    assert sample_user.email == "test@example.com"
```

### 3. Follow naming conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### 4. Write descriptive test names
```python
def test_user_with_read_permission_can_access_folder():
    # Good: describes what is being tested
    pass

def test_permission():
    # Bad: too vague
    pass
```

### 5. Use arrange-act-assert pattern
```python
def test_create_user():
    # Arrange
    user_data = {"email": "test@example.com", "username": "test"}

    # Act
    user = create_user(user_data)

    # Assert
    assert user.email == "test@example.com"
```

## Fixtures

Common fixtures available in `conftest.py`:

- `mock_db` - Mock database session
- `in_memory_db` - In-memory SQLite database
- `mock_openai_client` - Mock OpenAI client
- `mock_redis` - Mock Redis client
- `mock_minio` - Mock MinIO client
- `sample_user` - Sample user for testing
- `sample_admin_user` - Sample admin user
- `sample_folder` - Sample folder
- `sample_document` - Sample document
- `sample_permission` - Sample permission

## Best Practices

1. **Keep tests fast** - Unit tests should run in milliseconds
2. **Isolate tests** - Each test should be independent
3. **Mock external dependencies** - Don't call real APIs or databases
4. **Test one thing** - Each test should validate one specific behavior
5. **Use descriptive names** - Test name should describe what is being tested
6. **Test edge cases** - Include tests for error conditions and edge cases
7. **Keep tests simple** - Tests should be easier to understand than the code they test

## Common Issues

### Mock not working
```python
# Bad: Mock created but not used properly
mock_db = Mock()
result = service.method()  # Doesn't use mock

# Good: Pass mock to service
mock_db = Mock()
service = MyService(mock_db)
result = service.method()
```

### Assertion errors
```python
# Bad: Vague assertion
assert result

# Good: Specific assertion
assert result.status == "success"
assert len(result.items) == 3
```

## CI/CD Integration

Unit tests run automatically on:
- Every push to main, develop, or feature branches
- Every pull request

See `.github/workflows/unit-tests.yml` for configuration.

## Coverage Goals

- Overall coverage: 80%+
- New code coverage: 90%+
- Critical paths: 100%

Check coverage report:
```bash
pytest tests/unit/ --cov=app --cov-report=html
open htmlcov/index.html
```
