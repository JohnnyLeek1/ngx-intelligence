# NGX Intelligence Backend Test Suite

Comprehensive test suite for the ngx-intelligence backend application.

## Overview

This test suite provides >80% code coverage across all major backend components:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and API endpoints
- **Configuration**: pytest and coverage configuration for consistent testing

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── pytest.ini               # Pytest configuration (symlinked from ../pytest.ini)
├── unit/                    # Unit tests
│   ├── test_security.py     # Security utilities (password hashing, JWT)
│   ├── test_config.py       # Configuration management
│   ├── test_repositories.py # Repository CRUD operations
│   └── test_schemas.py      # Pydantic schema validation
└── integration/             # Integration tests
    ├── test_api.py          # API endpoint tests
    ├── test_database.py     # Database integration tests
    └── test_services.py     # Service layer tests
```

## Running Tests

### Prerequisites

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_security.py

# Specific test class
pytest tests/unit/test_security.py::TestPasswordHashing

# Specific test function
pytest tests/unit/test_security.py::TestPasswordHashing::test_password_hashing
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run with Markers

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only database tests
pytest -m db

# Run only API tests
pytest -m api

# Run only security tests
pytest -m security
```

### Verbose Output

```bash
# Verbose output with test names
pytest -v

# Very verbose with full output
pytest -vv

# Show local variables in tracebacks
pytest -l

# Show print statements
pytest -s
```

## Test Coverage

### Current Coverage Target: >80%

### Coverage by Module

- **Core Security** (`app/core/security.py`): ~95%
  - Password hashing and verification
  - JWT token creation and validation
  - Token expiration and refresh
  - Encryption/decryption

- **Configuration** (`app/config.py`): ~90%
  - YAML configuration loading
  - Environment variable overrides
  - Validation and defaults
  - Database URL generation

- **Repositories** (`app/repositories/`): ~85%
  - User CRUD operations
  - Document management
  - Queue operations
  - Custom queries and filters

- **Schemas** (`app/schemas/`): ~90%
  - Pydantic validation
  - Custom validators
  - Field constraints
  - Serialization/deserialization

- **API Endpoints** (`app/api/v1/endpoints/`): ~85%
  - Authentication endpoints
  - Document endpoints
  - Queue endpoints
  - Error handling

## Test Fixtures

Comprehensive fixtures available in `conftest.py`:

### Database Fixtures

- `db_session`: Fresh in-memory SQLite database for each test
- `test_user`: Pre-created test user
- `admin_user`: Pre-created admin user

### Authentication Fixtures

- `access_token`: JWT access token for test user
- `auth_headers`: Authorization headers for API requests

### Mock Fixtures

- `mock_paperless_client`: Mocked Paperless API client
- `mock_ollama_provider`: Mocked Ollama AI provider

## Writing Tests

### Unit Test Example

```python
import pytest
from app.core.security import hash_password, verify_password

def test_password_hashing():
    """Test password hashing works correctly."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user):
    """Test user login endpoint."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_auth(client: AsyncClient, auth_headers):
    """Test authenticated endpoint."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Use Fixtures**: Leverage shared fixtures for setup
3. **Mock External Services**: Use mocks for Paperless and Ollama
4. **Test Edge Cases**: Include validation failures and error conditions
5. **Clear Assertions**: Use descriptive assertion messages
6. **Async Tests**: Mark async tests with `@pytest.mark.asyncio`

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```bash
# CI command with coverage and strict settings
pytest --cov=app --cov-report=xml --cov-fail-under=80 -v
```

## Coverage Reports

After running tests with coverage:

- **Terminal Report**: Displayed after test run
- **HTML Report**: `htmlcov/index.html`
- **XML Report**: `coverage.xml` (for CI/CD)
- **JSON Report**: `coverage.json` (detailed data)

## Troubleshooting

### Import Errors

Ensure the app module is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Test Issues

Make sure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Database Errors

Tests use in-memory SQLite by default. If issues occur:
- Check that SQLAlchemy models are properly imported
- Verify Base.metadata.create_all() is called in fixtures

## Configuration Files

- **pytest.ini**: Pytest configuration
- **.coveragerc**: Coverage configuration
- **conftest.py**: Shared fixtures and test setup

## Adding New Tests

1. Create test file in appropriate directory (`unit/` or `integration/`)
2. Import required modules and fixtures
3. Write test functions with descriptive names
4. Use appropriate markers (`@pytest.mark.unit`, etc.)
5. Run tests to verify
6. Check coverage to ensure adequate testing

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
