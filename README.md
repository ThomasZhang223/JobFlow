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
- **Containerization**: Docker Compose

## Quick Setup

### Prerequisites

- Docker & Docker Compose

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Email
EMAIL_PASSWORD=your_email_password

# Proxies (for scraping, optional)
PROXY_STR=["proxy1:port","proxy2:port"]
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

> **Note**: Do NOT use quotes around values. Docker's `env_file` includes quotes literally.

### 2. Run with Docker Compose

```bash
docker compose up --build
```

This starts all services:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **Redis**: Internal container (not exposed to host)
- **Celery Worker**: Background job processing

### Other Docker Commands

```bash
# Run in background
docker compose up -d --build

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f api

# Rebuild a specific service
docker compose up -d --build api
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │
│   (Next.js)     │     │   (API)         │
│   :3000         │◀────│   :8000         │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │     Redis       │
                        │   (Pub/Sub)     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Celery Worker  │
                        │  (Scraping)     │
                        └─────────────────┘
```

## Deployment

The project is configured for Railway deployment with separate services for the API and worker. See [DEPLOY.md](backend/DEPLOY.md) for production deployment instructions.

---

For detailed documentation, see [Project_explained.md](Project_explained.md) and [setup_guide.md](setup_guide.md).
