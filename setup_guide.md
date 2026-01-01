#Project Setup Guide

A complete setup guide for running JobFlow locally.

---

## Prerequisites

Before starting, ensure you have the following installed:

- **Node.js** (v20.9.0 or higher)
- **Python** (3.10+)
- **Docker** (for Redis)
- **npm** or **yarn** or **pnpm** or **bun**

---

## Project Structure

```
JobFlow/
├── frontend/
│   └── masa/          # Next.js frontend application
├── backend/
│   ├── app/           # FastAPI application
│   ├── scraper/       # Scrapy scraper service
│   └── scripts/       # Utility scripts
```

---

## 1. Frontend (Next.js)

The frontend is a Next.js application located in `frontend/masa/`.

### Setup

```bash
# Navigate to frontend directory
cd frontend/masa

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Run Command

```bash
npm run dev
```

**Alternative commands:**
```bash
yarn dev
# or
pnpm dev
# or
bun dev
```

**Access:** Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 2. Backend (FastAPI)

The backend is a FastAPI application located in `backend/`.

### Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment 
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for scraping)
playwright install chromium

# Or install all browsers
playwright install
```

### Environment Variables

Create a `.env` file in the `backend/` directory based on `.env.example`:

```env
# LLMs
OPENAI_API_KEY=""
GEMINI_API_KEY=""

# Database
SUPABASE_URL=""
SUPABASE_KEY=""

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

### Run Command

```bash
fastapi dev app/main.py
```

**Alternative (using uvicorn directly):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:** API available at [http://localhost:8000](http://localhost:8000)  
**Docs:** Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3. Redis (Docker Container)

Redis is used as a message broker for Celery and for pub/sub messaging.

### Run Command

```bash
docker run -d \
  --name jobflow-redis \
  -p 6379:6379 \
  redis:latest
```

**With persistence (recommended for development):**
```bash
docker run -d \
  --name jobflow-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:latest \
  redis-server --appendonly yes
```

### Useful Docker Commands

```bash
# Check if Redis is running
docker ps

# View Redis logs
docker logs jobflow-redis

# Stop Redis
docker stop jobflow-redis

# Start Redis (if stopped)
docker start jobflow-redis

# Remove Redis container
docker rm jobflow-redis
```

### Verify Redis Connection

```bash
# Using redis-cli (if installed)
redis-cli ping
# Expected response: PONG
```

---

## 4. Celery Worker

Celery is used for running background tasks like job scraping.

### Setup

Ensure Redis is running and the `REDIS_URL` environment variable is set.

### Run Command

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Start Celery worker
celery -A worker.celery_app worker --loglevel=info
```

**With concurrency control:**
```bash
celery -A worker.celery_app worker --loglevel=info --concurrency=4
```

**For development (with auto-reload):**
```bash
celery -A worker.celery_app worker --loglevel=info --pool=solo
```

---

## Quick Start Summary

Open **4 terminal windows** and run these commands in order:

### Terminal 1 - Redis
```bash
docker run -d --name jobflow-redis -p 6379:6379 redis:latest
```

### Terminal 2 - Backend
```bash
cd backend
source venv/bin/activate
fastapi dev app/main.py
```

### Terminal 3 - Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A worker.celery_app worker --loglevel=info
```

### Terminal 4 - Frontend
```bash
cd frontend/masa
npm run dev
```

---

## Service Ports

| Service  | Port | URL                          |
|----------|------|------------------------------|
| Frontend | 3000 | http://localhost:3000        |
| Backend  | 8000 | http://localhost:8000        |
| Redis    | 6379 | redis://localhost:6379       |

---

## Health Check Endpoints

**Backend Health:**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01"
}
```

---

## Troubleshooting

### Redis Connection Issues
- Ensure Docker is running
- Verify port 6379 is not in use: `lsof -i :6379`
- Check Redis container status: `docker ps -a`

### Celery Worker Not Starting
- Verify Redis is running and accessible
- Check `REDIS_URL` in your `.env` file
- Ensure virtual environment is activated

### Frontend Build Issues
- Delete `node_modules` and `package-lock.json`, then reinstall
- Ensure Node.js version is 20.9.0 or higher: `node --version`

### Backend Import Errors
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Ensure you're running from the `backend/` directory