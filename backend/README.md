# ngx-intelligence Backend

AI-powered document processing backend for Paperless-NGX.

## Architecture Overview

The backend is built with FastAPI and follows a clean, layered architecture:

### Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management (Pydantic Settings)
│   ├── dependencies.py         # FastAPI dependency injection
│   ├── core/
│   │   ├── security.py         # JWT, password hashing
│   │   └── logging.py          # Logging configuration
│   ├── database/
│   │   ├── base.py             # Abstract database interfaces
│   │   ├── session.py          # Database session management
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── providers/
│   │       └── sqlite.py       # SQLite provider implementation
│   ├── repositories/
│   │   ├── base.py             # Base repository pattern
│   │   ├── user.py             # User repository
│   │   ├── document.py         # Document repository
│   │   ├── queue.py            # Queue repository
│   │   └── approval.py         # Approval repository
│   ├── schemas/
│   │   ├── common.py           # Common schemas
│   │   ├── user.py             # User schemas
│   │   ├── document.py         # Document schemas
│   │   ├── queue.py            # Queue schemas
│   │   ├── approval.py         # Approval schemas
│   │   └── config.py           # Configuration schemas
│   ├── api/v1/
│   │   ├── router.py           # Main API router
│   │   └── endpoints/
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── documents.py    # Document endpoints
│   │       ├── queue.py        # Queue endpoints
│   │       └── config.py       # Configuration endpoints
│   ├── services/
│   │   ├── paperless.py        # Paperless API client
│   │   ├── ai/
│   │   │   ├── base.py         # Abstract LLM interface
│   │   │   └── ollama.py       # Ollama implementation
│   │   └── processing/
│   │       ├── pipeline.py     # Document processing pipeline
│   │       └── queue.py        # Queue management
│   └── utils/
│       └── validators.py       # Utility validators
├── config/
│   └── config.yaml             # Default configuration
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   └── unit/
│       ├── test_config.py
│       └── test_security.py
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── pytest.ini                  # Pytest configuration
```

## Key Design Decisions

### 1. Configuration Management
- **Pydantic Settings** for type-safe configuration
- YAML files with environment variable override support
- Centralized settings with validation

### 2. Database Abstraction
- **Repository Pattern** for data access
- Abstract base interfaces supporting multiple database providers
- SQLAlchemy 2.0+ with async support
- SQLite default with PostgreSQL support

### 3. Authentication
- **JWT-based authentication** with access and refresh tokens
- Bcrypt password hashing
- Role-based access control (Admin/User)

### 4. API Structure
- **Versioned API** (v1) with clear endpoint organization
- Pydantic schemas for request/response validation
- Dependency injection for repositories and services
- Comprehensive error handling

### 5. Service Layer
- **Abstract interfaces** for external services (AI, Paperless)
- Stub implementations with TODO markers for future development
- Clear separation between business logic and API layer

## Development Setup

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export DB_PASSWORD="your-db-password"
```

### Configuration

Edit `/config/config.yaml` or set environment variables with `NGX_` prefix:

```bash
export NGX_APP__DEBUG=true
export NGX_DATABASE__PROVIDER=sqlite
export NGX_AI__OLLAMA__BASE_URL=http://localhost:11434
```

### Running the Application

```bash
# Development mode with auto-reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test
pytest tests/unit/test_config.py::test_default_settings
```

## Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Documentation

Once running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Implementation Status

### Ready
- Configuration management
- Database models and repositories
- Authentication and security
- API structure and routing
- Pydantic schemas for validation
- Basic testing infrastructure

### Stub/TODO
- Paperless API integration (service stub created)
- Ollama AI integration (service stub created)
- Document processing pipeline (architecture defined)
- Queue management (stub created)
- Approval workflow
- Learning and pattern analysis

## Code Quality

### Type Checking
```bash
mypy app/
```

### Linting and Formatting
```bash
# Using ruff
ruff check app/
ruff format app/
```

## Security Considerations

- JWT tokens with configurable expiration
- Bcrypt password hashing
- Environment-based secret management
- Rate limiting (TODO)
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy

## Next Steps

1. **Implement Paperless API Client**
   - Complete document fetching
   - Metadata updates
   - Tag/type/correspondent management

2. **Implement Ollama Integration**
   - Complete AI provider methods
   - JSON response parsing
   - Error handling and retries

3. **Build Processing Pipeline**
   - Correspondent identification
   - Document classification
   - Tag suggestion
   - Date extraction
   - Title generation

4. **Queue Management**
   - Background workers
   - Retry logic
   - Priority processing

5. **Database Migrations**
   - Set up Alembic
   - Create initial migration
   - Add migration documentation

## License

MIT License - See LICENSE file for details
