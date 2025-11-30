# Development Guide

This guide covers local development setup for ngx-intelligence.

## Quick Start

### Docker Development (Recommended)

The easiest way to develop with hot-reloading:

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Access your app**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

**Changes are live**:
- Edit files in `frontend/src/` → Browser auto-refreshes
- Edit files in `backend/app/` → Server auto-restarts
- No rebuilding needed!

### Stopping Development

```bash
# Stop all containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## What's Different in Development Mode?

The `docker-compose.dev.yml` override provides:

### Frontend
- Runs Vite dev server (not nginx production build)
- Source code mounted as volumes for hot-reload
- Port 5173 exposed (Vite default)
- File watching with polling for cross-platform compatibility
- Node modules persisted in container

### Backend
- Source code mounted for hot-reload
- Port 8001 exposed for direct API access (avoiding port conflicts)
- `RELOAD=true` environment variable for Uvicorn
- Live code changes trigger server restart

### Configuration Files
Development mode mounts:
- `frontend/src/` - React components
- `frontend/public/` - Static assets
- `frontend/index.html` - Entry point
- `frontend/vite.config.ts` - Build config
- `frontend/tsconfig.json` - TypeScript config
- `frontend/tailwind.config.js` - Tailwind config
- `backend/app/` - Python application code

## Development Workflow

### Making Changes

1. **Start development environment**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **Edit code**:
   - Frontend: Edit files in `frontend/src/`
   - Backend: Edit files in `backend/app/`

3. **See changes automatically**:
   - Frontend: Browser refreshes
   - Backend: Server restarts

4. **Check logs**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
   ```

### Adding Dependencies

**Frontend**:
```bash
# Access container shell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend sh

# Install package
npm install package-name

# Exit shell
exit

# Restart to apply
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart frontend
```

**Backend**:
```bash
# Add to requirements.txt, then:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build backend
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Debugging

**View container logs**:
```bash
# All services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Frontend only
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f frontend

# Backend only
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend
```

**Access container shell**:
```bash
# Frontend
docker exec -it ngx-intelligence-frontend sh

# Backend
docker exec -it ngx-intelligence-backend bash
```

**Check container status**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

## Port Reference

### Development Ports
- **5173** - Frontend (Vite dev server)
- **8001** - Backend API (direct access)

### Production Ports
- **3000** - Frontend (nginx)
- **8000** - Backend (internal only, proxied via nginx)

Note: Development uses different ports to avoid conflicts with other services (like paperless-ngx on 8000).

## Common Issues

### Port Already in Use

If you see "port is already allocated":

**Port 5173 conflict**:
```yaml
# Edit docker-compose.dev.yml
ports:
  - "5174:3000"  # Change host port
```

**Port 8001 conflict**:
```yaml
# Edit docker-compose.dev.yml
ports:
  - "8002:8000"  # Change host port
```

### Changes Not Reflecting

**Frontend not updating**:
1. Check if Vite dev server is running: `docker logs ngx-intelligence-frontend`
2. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
3. Clear browser cache

**Backend not reloading**:
1. Check logs: `docker logs ngx-intelligence-backend`
2. Verify `RELOAD=true` in environment
3. Restart container: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart backend`

### Cannot Connect to Backend

Check that containers are on the same network:
```bash
docker network ls
docker network inspect ngx-intelligence_ngx-intelligence-network
```

## Native Development (Without Docker)

If you prefer to run services natively:

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Access at http://localhost:3000

## Testing

### Frontend Tests

```bash
# Run tests
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm test

# Run with coverage
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm run test:coverage

# Run E2E tests
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm run test:e2e
```

### Backend Tests

```bash
# Run tests
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest

# Run with coverage
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest --cov=app --cov-report=html
```

## Production Build

When ready to test production build:

```bash
# Stop development containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build and start production
docker-compose up -d --build

# Access at http://localhost:3000
```

## Tips

1. **Use development mode** for active coding
2. **Use production mode** to test final builds
3. **Keep containers running** - stopping/starting is fast with volumes
4. **Check logs often** - they show compilation errors and runtime issues
5. **Use container shells** for debugging and exploring

## Next Steps

- Review [README.md](README.md) for general information
- Check [SETUP_COMPLETE.md](SETUP_COMPLETE.md) for deployment details
- Read [SPECIFICATION.md](SPECIFICATION.md) for architecture details
