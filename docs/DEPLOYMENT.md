# ngx-intelligence Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Production Deployment](#production-deployment)
5. [Backup & Recovery](#backup--recovery)
6. [Monitoring](#monitoring)
7. [Upgrading](#upgrading)
8. [Security Hardening](#security-hardening)

---

## Prerequisites

### Required
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Paperless-NGX** running and accessible
- **Ollama** installed (local or remote)
- **2GB+ RAM** for application
- **10GB+ storage** for database and logs

### Recommended
- **4GB+ RAM** for smooth operation
- **SSD storage** for database
- **GPU** for faster AI processing (NVIDIA recommended)
- **Reverse proxy** (nginx, Caddy) for HTTPS

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ngx-intelligence.git
cd ngx-intelligence
```

### 2. Generate Secrets

```bash
# Generate SECRET_KEY for JWT
openssl rand -hex 32

# Generate ENCRYPTION_KEY for database encryption
openssl rand -hex 32
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Required settings:
```bash
# Security
SECRET_KEY=your-generated-secret-key
ENCRYPTION_KEY=your-generated-encryption-key

# Ollama
OLLAMA_URL=http://host.docker.internal:11434  # Mac/Windows
# OLLAMA_URL=http://172.17.0.1:11434          # Linux

# Paperless (default, can be overridden per-user)
PAPERLESS_URL=http://paperless.local:8000
PAPERLESS_API_TOKEN=your-paperless-token
```

### 4. Configure Application

```bash
cp config/config.yaml.example config/config.yaml
nano config/config.yaml
```

Key settings to review:
- AI model selection
- Processing mode (realtime/batch)
- Tag rules
- Naming templates

### 5. Start Services

```bash
# Using Makefile
make setup
make up

# Or using docker-compose directly
docker-compose up -d
```

### 6. Verify Deployment

```bash
# Check service health
make health

# Or manually
curl http://localhost:3000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "ollama": "reachable",
  "version": "1.0.0"
}
```

### 7. Access Application

Open browser to `http://localhost:3000`

Create admin account:
1. Click "Register"
2. Fill in your details
3. Provide Paperless-NGX credentials
4. Click "Register"

---

## Configuration

### Environment Variables

#### Security
```bash
SECRET_KEY=<required>              # JWT signing key (openssl rand -hex 32)
ENCRYPTION_KEY=<required>          # Database encryption key
NGX_APP__JWT_ACCESS_EXPIRY=900    # 15 minutes
NGX_APP__JWT_REFRESH_EXPIRY=604800 # 7 days
```

#### Ollama Integration
```bash
OLLAMA_URL=http://localhost:11434
NGX_AI__OLLAMA__MODEL=llama3.2    # Default model
NGX_AI__OLLAMA__TEMPERATURE=0.3   # 0.0-1.0
NGX_AI__OLLAMA__TIMEOUT=120       # Seconds
```

#### Processing
```bash
NGX_PROCESSING__MODE=realtime      # or 'batch'
NGX_PROCESSING__POLLING_INTERVAL=30
NGX_PROCESSING__CONCURRENT_WORKERS=1
NGX_PROCESSING__RETRY_ATTEMPTS=3
```

#### Logging
```bash
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
NGX_APP__LOG_FILE=/app/logs/app.log
```

### Configuration File (config.yaml)

Located at `/config/config.yaml` (mounted volume).

#### AI Configuration

```yaml
ai:
  provider: ollama
  ollama:
    base_url: ${OLLAMA_URL}
    model: llama3.2
    temperature: 0.3
    timeout: 120
  prompts:
    system: |
      You are an AI assistant specialized in document classification for paperless document management.
      Analyze documents carefully and provide accurate classifications based on content.
    classification: |
      Analyze this document and determine its type. Choose from the available types or suggest a new one if none match.
      Return JSON with: {"document_type": "type_name", "confidence": 0.95}
```

#### Processing Configuration

```yaml
processing:
  mode: realtime
  polling_interval: 30
  concurrent_workers: 1
  retry_attempts: 3
  retry_backoff: 60
  batch_schedule: "0 2 * * *"  # 2 AM daily
```

#### Tag Rules

```yaml
tagging:
  processing_tag:
    enabled: true
    name: "ai-processed"
  rules:
    min_tags: 1
    max_tags: 10
    confidence_threshold: 0.7
    prefix: ""
    excluded_tags: ["important", "archived"]
```

#### Naming Templates

```yaml
naming:
  default_template: "{date}_{correspondent}_{type}_{title}"
  date_format: "YYYY-MM-DD"
  max_title_length: 100
  clean_special_chars: true
```

---

## Production Deployment

### Docker Compose Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: ngx-intelligence/backend:latest
    restart: always
    environment:
      - NGX_APP__DEBUG=false
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: ngx-intelligence/frontend:latest
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Reverse Proxy Setup (nginx)

Create `/etc/nginx/sites-available/ngx-intelligence`:

```nginx
server {
    listen 80;
    server_name intelligence.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name intelligence.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/intelligence.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intelligence.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to application
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:3000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/ngx-intelligence /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d intelligence.yourdomain.com
```

### Database Migration to PostgreSQL

For production, consider migrating from SQLite to PostgreSQL:

1. **Start PostgreSQL**:
```bash
docker run -d \
  --name ngx-intelligence-db \
  -e POSTGRES_DB=ngx_intelligence \
  -e POSTGRES_USER=ngx_user \
  -e POSTGRES_PASSWORD=secure_password \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15
```

2. **Update .env**:
```bash
DATABASE_URL=postgresql+asyncpg://ngx_user:secure_password@ngx-intelligence-db:5432/ngx_intelligence
```

3. **Run migrations**:
```bash
docker-compose exec backend alembic upgrade head
```

---

## Backup & Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/ngx-intelligence"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec backend python -c "
from app.database.session import engine
import asyncio
async def backup():
    # Backup logic here
    pass
asyncio.run(backup())
"

# Backup configuration
cp config/config.yaml $BACKUP_DIR/config_$DATE.yaml
cp .env $BACKUP_DIR/env_$DATE

# Backup logs (last 7 days)
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

Schedule with cron:
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Manual Backup

```bash
# Backup database
make backup

# Or manually
docker-compose exec backend \
  sqlite3 /app/data/ngx_intelligence.db \
  ".backup /app/data/backup_$(date +%Y%m%d).db"
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore database
cp /backups/backup_20240315.db data/ngx_intelligence.db

# Restore configuration
cp /backups/config_20240315.yaml config/config.yaml

# Start services
docker-compose up -d
```

---

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:3000/api/health

# Backend health
curl http://localhost:8000/health

# Ollama health
curl http://localhost:11434/api/tags
```

### Logs

```bash
# View all logs
make logs

# Backend only
make logs-backend

# Frontend only
make logs-frontend

# Follow logs in real-time
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Prometheus Metrics (Future)

If Prometheus integration is enabled:

```bash
# Expose metrics
curl http://localhost:8000/metrics

# Key metrics:
# - ngx_documents_processed_total
# - ngx_processing_duration_seconds
# - ngx_queue_depth
# - ngx_confidence_score_avg
```

### Grafana Dashboard (Future)

Import dashboard from `monitoring/grafana-dashboard.json`

---

## Upgrading

### Minor Version Upgrade

```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d

# Verify
curl http://localhost:3000/api/health
```

### Major Version Upgrade

```bash
# Backup first
make backup

# Read CHANGELOG.md for breaking changes

# Pull new version
docker-compose pull

# Run database migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart

# Verify
make health
```

### Rollback

```bash
# Stop services
docker-compose down

# Restore backup
cp /backups/backup_20240315.db data/ngx_intelligence.db

# Use previous image version
docker-compose up -d ngx-intelligence/backend:v1.0.0
```

---

## Security Hardening

### Docker Security

```yaml
# docker-compose.yml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
```

### Network Isolation

```yaml
networks:
  internal:
    internal: true
  external:
    driver: bridge

services:
  backend:
    networks:
      - internal
      - external

  db:
    networks:
      - internal  # No external access
```

### Firewall Rules (ufw)

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Regular Security Updates

```bash
# Update base images
docker-compose pull
docker-compose up -d

# Update OS packages
sudo apt update && sudo apt upgrade -y

# Review security advisories
# GitHub Dependabot alerts
```

### Secrets Management

Use Docker secrets for production:

```yaml
services:
  backend:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

---

## Troubleshooting

### Common Deployment Issues

#### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing environment variables
# - Invalid configuration
# - Port conflicts

# Verify ports are free
sudo netstat -tulpn | grep :3000
```

#### Database Connection Failed

```bash
# Check database is running
docker-compose ps

# Test connection
docker-compose exec backend python -c "
from app.database.session import engine
import asyncio
asyncio.run(engine.connect())
"
```

#### Ollama Not Reachable

```bash
# Test from host
curl http://localhost:11434/api/tags

# Test from container
docker-compose exec backend curl http://host.docker.internal:11434/api/tags

# Linux users: Use bridge IP
docker network inspect bridge | grep Gateway
```

#### Permission Denied

```bash
# Fix volume permissions
sudo chown -R 1000:1000 data/ logs/ config/

# Or use Docker user remapping
```

---

## Performance Tuning

### Database Optimization

```yaml
# PostgreSQL tuning
services:
  db:
    environment:
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
      - POSTGRES_MAX_CONNECTIONS=100
```

### Backend Optimization

```bash
# Increase workers for multi-core systems
NGX_PROCESSING__CONCURRENT_WORKERS=4

# Use faster model for speed
NGX_AI__OLLAMA__MODEL=mistral-7b

# Reduce timeout for faster failures
NGX_AI__OLLAMA__TIMEOUT=60
```

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

---

**End of Deployment Guide**

For user instructions, see [USER_GUIDE.md](USER_GUIDE.md)
For API documentation, visit `/api/docs` when application is running
