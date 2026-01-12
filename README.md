# JobFlow

A full-stack job application tracker with automated job scraping capabilities. JobFlow helps you manage your job search by automatically scraping job listings from Indeed, tracking applications, and organizing opportunities with priority flags and statistics.

## What It Does

- **Automated Job Scraping**: Scrapes job listings from Indeed based on your preferences (job title, location, experience level)
- **Real-time Updates**: WebSocket connections for live progress updates during scraping
- **Job Management**: Track, prioritize, and organize job applications in one place
- **Smart Filtering**: Search and filter jobs by title, company, location, and status
- **Analytics**: View statistics on your job search progress
- **Secure Authentication**: JWT-based authentication with Supabase

## Tech Stack

- **Frontend**: Next.js (TypeScript), TailwindCSS
- **Backend**: FastAPI (Python)
- **Scraper**: Scrapy with Playwright for dynamic content
- **Database**: Supabase (PostgreSQL)
- **Task Queue**: Celery with Redis
- **Auth**: Supabase Authentication (JWT)

## Quick Setup

### Prerequisites

- Node.js (v20.9.0+)
- Python (3.10+)
- Docker (for Redis)

### 1. Frontend

```bash
cd frontend/masa
npm install
npm run dev
# Access at http://localhost:3000
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your credentials
fastapi dev app/main.py
# Access API at http://localhost:8000
```

### 3. Redis

```bash
docker run -d --name jobflow-redis -p 6379:6379 redis:latest
```

### 4. Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A worker.celery_app worker --loglevel=info
```

## Environment Variables

Create a `.env` file in `backend/`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## Deployment

The project is configured for Railway deployment with separate services for the API and worker. See [DEPLOY.md](backend/DEPLOY.md) for production deployment instructions.

---

For detailed documentation, see [Project_explained.md](Project_explained.md) and [setup_guide.md](setup_guide.md).
