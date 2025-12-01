# ngx-intelligence

**AI-Powered Document Enhancement for Paperless-NGX**

ngx-intelligence is an intelligent document processing companion for [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx) that automatically classifies, tags, and organizes your documents using local AI models.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Docker Build](https://github.com/JohnnyLeek1/ngx-intelligence/actions/workflows/docker-build.yml/badge.svg)](https://github.com/JohnnyLeek1/ngx-intelligence/actions/workflows/docker-build.yml)
[![Backend](https://ghcr-badge.egpl.dev/johnnyleek1/ngx-intelligence-backend/latest_tag?trim=major&label=backend)](https://github.com/JohnnyLeek1/ngx-intelligence/pkgs/container/ngx-intelligence-backend)
[![Frontend](https://ghcr-badge.egpl.dev/johnnyleek1/ngx-intelligence-frontend/latest_tag?trim=major&label=frontend)](https://github.com/JohnnyLeek1/ngx-intelligence/pkgs/container/ngx-intelligence-frontend)

---

## Features

- **Intelligent Classification**: Automatically determine document types using AI
- **Smart Tagging**: Apply relevant tags based on document content
- **Correspondent Identification**: Extract and match senders/recipients
- **Date Extraction**: Find the most relevant date in documents
- **Automatic Renaming**: Generate descriptive filenames using templates
- **Learning System**: Improves accuracy over time from your feedback
- **Privacy-First**: Uses local AI models (Ollama) - your data never leaves your infrastructure
- **Multi-User**: Support for multiple users with role-based access
- **Approval Workflow**: Optional review before applying changes
- **Real-time & Batch**: Process documents as they arrive or on schedule

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Paperless-NGX instance
- Ollama installed

### Installation

#### Option 1: Using Pre-built Images (Recommended)

Use pre-built multi-architecture images from GitHub Container Registry:

```bash
# Clone the repository
git clone https://github.com/JohnnyLeek1/ngx-intelligence.git
cd ngx-intelligence

# Generate secrets
openssl rand -hex 32  # Copy for SECRET_KEY

# Configure environment
cp .env.example .env
nano .env  # Add your SECRET_KEY and Ollama URL

# Start services using pre-built images
docker-compose -f docker-compose.prod.yml up -d

# Access the application
open http://localhost:3000
```

#### Option 2: Build from Source

Build images locally from source:

```bash
# Clone the repository
git clone https://github.com/JohnnyLeek1/ngx-intelligence.git
cd ngx-intelligence

# Generate secrets
openssl rand -hex 32  # Copy for SECRET_KEY

# Configure environment
cp .env.example .env
nano .env  # Add your SECRET_KEY and Ollama URL

# Build and start services
docker-compose up -d

# Access the application
open http://localhost:3000
```

### First-Time Setup

1. Navigate to `http://localhost:3000`
2. Click "Register" to create an account
3. Provide your Paperless-NGX credentials
4. Configure AI settings (Settings → AI Configuration)
5. Start processing documents!

---

## Docker Images

Pre-built multi-architecture Docker images are available on GitHub Container Registry:

```bash
# Pull latest images
docker pull ghcr.io/johnnyleek1/ngx-intelligence-backend:latest
docker pull ghcr.io/johnnyleek1/ngx-intelligence-frontend:latest

# Pull specific version
docker pull ghcr.io/johnnyleek1/ngx-intelligence-backend:v1.0.0
docker pull ghcr.io/johnnyleek1/ngx-intelligence-frontend:v1.0.0
```

**Supported Architectures**:
- linux/amd64 (x86_64)
- linux/arm64 (ARM64/v8)

Images are automatically built and pushed on every commit to `main` and for all tagged releases.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete user documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[API Documentation](http://localhost:3000/api/docs)** - Interactive API docs (when running)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ngx-intelligence                    │
│                                                         │
│  ┌──────────────┐         ┌──────────────────┐          │
│  │   Frontend   │◄───────►│     Backend      │          │
│  │  React + UI  │         │   FastAPI        │          │
│  └──────────────┘         └──────────────────┘          │
│         │                          │                    │
│         │                    ┌─────▼─────┐              │
│         │                    │  SQLite/  │              │
│         │                    │PostgreSQL │              │
│         │                    └───────────┘              │
└─────────┼────────────────────────┼──────────────────────┘
          │                        │
          ▼                        ▼
   ┌─────────────┐         ┌──────────────┐
   │ Paperless-  │         │    Ollama    │
   │     NGX     │         │  (AI Models) │
   └─────────────┘         └──────────────┘
```

### Technology Stack

**Backend**:
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM with async support
- Pydantic - Data validation
- httpx - Async HTTP client
- APScheduler - Task scheduling

**Frontend**:
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- shadcn/ui - Component library
- Jotai - State management
- TanStack Query - Data fetching

**Infrastructure**:
- Docker - Containerization
- nginx - Reverse proxy
- SQLite/PostgreSQL - Database
- Ollama - Local AI inference

---

## Features in Detail

### Document Processing Pipeline

For each document, ngx-intelligence performs:

1. **Correspondent Identification**
   - Extracts sender/recipient from document text
   - Matches against existing correspondents
   - Creates new correspondents if enabled

2. **Document Type Classification**
   - Analyzes content to determine document category
   - Maps to existing Paperless document types
   - Suggests new types when appropriate

3. **Intelligent Tagging**
   - Applies relevant tags based on content and context
   - Enforces configurable tag rules (min/max, confidence)
   - Respects excluded tags and naming conventions

4. **Date Extraction**
   - Identifies the most relevant date (invoice date, letter date, etc.)
   - Validates and formats dates consistently
   - Falls back gracefully when no date is found

5. **Smart Renaming**
   - Generates descriptive filenames using templates
   - Supports variables: {date}, {type}, {correspondent}, {title}
   - Cleans special characters for compatibility

### Learning & Improvement

- **Example Library**: Builds database of correctly classified documents
- **User Feedback**: Learns from corrections and rejected suggestions
- **Pattern Analysis**: Identifies tagging patterns and naming conventions
- **Confidence Scoring**: Tracks accuracy and improves over time

### Processing Modes

**Real-time Processing**:
- Polls Paperless-NGX API for new documents (default: 30s interval)
- Processes documents immediately as they arrive
- Ideal for continuous document flow

**Batch Processing**:
- Processes documents on a schedule (cron-based)
- Supports thresholds (document count, time interval)
- Perfect for large backlogs and off-peak processing

**Manual Processing**:
- On-demand processing of specific documents
- Reprocess after configuration changes
- Filter-based bulk reprocessing

### Approval Workflow

When enabled, allows you to:
- Review AI suggestions before applying
- Provide feedback on incorrect classifications
- Edit suggestions before accepting
- Batch approve multiple documents
- Track improvement over time

---

## Configuration

### AI Models

ngx-intelligence works with any Ollama model. Recommended models:

- **llama3.2** - Best balance of speed and accuracy (default)
- **mistral-7b** - Faster, good for simple documents
- **mixtral-8x7b** - Most accurate, slower

```bash
# Pull a model in Ollama
ollama pull llama3.2
```

### Tag Rules

Configure how tags are applied:

```yaml
tagging:
  rules:
    min_tags: 1
    max_tags: 10
    confidence_threshold: 0.7
    prefix: ""
    excluded_tags: ["important", "archived"]
```

### Naming Templates

Customize document naming:

```yaml
naming:
  default_template: "{date}_{correspondent}_{type}_{title}"
  date_format: "YYYY-MM-DD"
  max_title_length: 100
```

Example output: `2024-03-15_ACME-Corp_Invoice_Monthly-Service-Bill.pdf`

---

## Development

### Project Structure

```
ngx-intelligence/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # REST API endpoints
│   │   ├── core/        # Security, logging
│   │   ├── database/    # ORM models, repositories
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── tests/           # Backend tests (>80% coverage)
│   └── config/          # Configuration files
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── api/         # API client
│   │   ├── hooks/       # Custom hooks
│   │   └── store/       # Jotai state
│   └── tests/           # Frontend tests
├── docs/                # Documentation
├── docker-compose.yml   # Docker orchestration
└── .env                 # Environment configuration
```

### Running Tests

**Backend**:
```bash
cd backend
pytest --cov=app --cov-report=html
```

**Frontend**:
```bash
cd frontend
npm test
npm run test:coverage
```

**E2E**:
```bash
cd frontend
npm run test:e2e
```

### Local Development

#### Option 1: Docker Development (Recommended)

For the best development experience with hot-reloading in Docker:

```bash
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or rebuild and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

**Features**:
- ✅ Hot-reload for frontend (instant browser updates)
- ✅ Hot-reload for backend (automatic server restart)
- ✅ No need to rebuild containers for code changes
- ✅ Consistent environment with production

**Access points**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

**What's mounted**:
- `frontend/src/` → Live updates in browser
- `backend/app/` → Auto-restart on save
- Configuration files → Instant reload

#### Option 2: Native Development

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

---

## Roadmap

### Phase 1: MVP ✅ (Complete)
- [x] Docker deployment
- [x] Backend API (FastAPI)
- [x] Database abstraction (SQLite/PostgreSQL)
- [x] JWT authentication
- [x] Paperless-NGX integration
- [x] Ollama AI integration
- [x] Document processing pipeline
- [x] React frontend with shadcn/ui
- [x] Dashboard, History, Settings pages
- [x] Comprehensive testing (>80% backend, >70% frontend)

### Phase 2: Enhancements (Planned)
- [ ] Approval workflow implementation
- [ ] Learning system with example library
- [ ] Pattern analysis
- [ ] Webhook notifications
- [ ] Advanced tag rules
- [ ] Bulk operations

### Phase 3: Advanced Features (Future)
- [ ] Multiple AI providers (OpenAI, Claude, etc.)
- [ ] Vision support for image analysis
- [ ] Custom field extraction
- [ ] Mobile support
- [ ] Multi-language support
- [ ] Advanced analytics

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features (maintain >70% coverage)
- Update documentation for user-facing changes
- Use conventional commits

---

## Security

- JWT-based authentication with refresh tokens
- Bcrypt password hashing
- Encrypted API tokens at rest (AES-256)
- CORS protection
- Rate limiting
- Input validation on all endpoints
- SQL injection protection (ORM)
- XSS protection

---

## Performance

- Async/await throughout for optimal concurrency
- Database query optimization with proper indexing
- API response caching (5-minute TTL)
- Connection pooling for external services
- Configurable concurrent workers (1-10)
- Resource limits via Docker

**Benchmarks** (single worker, llama3.2):
- Simple document (1 page): ~3-5 seconds
- Complex document (10 pages): ~8-12 seconds
- Queue throughput: ~200-300 documents/hour

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Paperless-NGX** - The amazing document management system this integrates with
- **Ollama** - Local AI model inference
- **shadcn/ui** - Beautiful React component library
- **FastAPI** - Modern Python web framework

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ngx-intelligence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ngx-intelligence/discussions)

---

**Made with ❤️ by [Johnny Leek](https://johnnyleek.dev)**

*Privacy-first AI document management for everyone*
