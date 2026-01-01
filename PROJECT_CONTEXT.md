# JobFlow AI - Project Context Document

**Last Updated:** December 29, 2024
**Status:** MVP In Progress

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [File Structure](#file-structure)
5. [Database Schema](#database-schema)
6. [Component Details](#component-details)
7. [API Endpoints](#api-endpoints)
8. [Key Decisions](#key-decisions)
9. [Issues & Fixes](#issues--fixes)
10. [Current Status](#current-status)
11. [Next Steps](#next-steps)

---

## Project Overview

### What is JobFlow AI?

JobFlow AI is a job application automation platform with three planned modules:

| Module | Description | Status |
|--------|-------------|--------|
| **Job Scraping** | Automated job scraping from job boards | MVP Focus |
| **AI CV/Cover Letter** | AI-powered resume and cover letter optimization | Future |
| **Auto-Apply** | Automated job applications with human approval | Future |

### MVP Scope

- Single user (no multi-tenancy yet)
- Indeed job board only (initially)
- Basic scraping with user preferences
- Real-time status updates via WebSocket
- Email notifications on completion (disabled until domain setup)
- Scheduled scraping via Celery Beat

### MVP Constraints

- Authentication deferred (using test user ID)
- Email notifications disabled (no verified domain)
- Actual scraping logic not implemented (mock data)

---

## Tech Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | REST API + WebSocket |
| Task Queue | Celery | Background job processing |
| Message Broker | Redis | Celery broker + Pub/Sub |
| Database | Supabase (PostgreSQL) | Persistent storage |
| Email | Resend | Email notifications (future) |

### Frontend (Separate Repository)

| Component | Technology |
|-----------|------------|
| Framework | Next.js |
| Language | TypeScript |
| Styling | Tailwind CSS |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Local Redis | Docker container |
| Database | Supabase hosted PostgreSQL |
| Auth | Supabase Auth (future) |

---

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                │
│                         (Next.js)                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                     REST       │       WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          FASTAPI                                 │
│                                                                  │
│  POST /api/scrape ──► Celery Queue ──► Return response          │
│                                                                  │
│  WebSocket /ws/scrape ◄──── Redis Pub/Sub subscriber            │
│                                                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
               ▼                ▼                ▼
┌──────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│     SUPABASE     │  │      REDIS      │  │    CELERY WORKER    │
│    PostgreSQL    │  │                 │  │                     │
│                  │  │  - Task Queue   │  │  - run_scrape       │
│  - jobs          │  │  - Pub/Sub      │  │  - scheduled_scrape │
│  - preferences   │  │                 │  │                     │
└────────▲─────────┘  └────────┬────────┘  └──────────┬──────────┘
         │                     │                      │
         │                     │                      │
         └─────────────────────┴──────────────────────┘
               Celery writes to Supabase
               Celery publishes to Redis (notifications)
```

### Communication Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| REST API | User triggers scrape, fetches jobs | FastAPI routes |
| WebSocket | Real-time status updates | Single connection per session |
| Redis Pub/Sub | Celery → FastAPI notifications | Channel: "scrape_updates" |
| Redis Queue | Task queue for Celery | Managed by Celery internally |

### Why This Architecture?

1. **Celery + Redis Queue**: Celery manages the queue automatically via Redis. When `.delay()` is called, Celery serializes the task and pushes to Redis list. Workers poll and execute.

2. **Redis Pub/Sub (Separate from Queue)**: Used for real-time notifications. Celery publishes status updates, FastAPI subscribes and forwards to WebSocket.

3. **Single WebSocket Connection**: MVP is single user. One global WebSocket connection receives all task updates. Messages include identifying info (query, location) so frontend knows which scrape completed.

4. **Supabase over Custom PostgreSQL**: Managed database with built-in auth system for future use. No DevOps overhead.

---

## File Structure

```
backend/
├── .env                          # Environment variables
├── .env.example                  # Template for env vars
├── requirements.txt              # Python dependencies
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point + lifespan
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic Settings
│   │   ├── redis_client.py       # Async Redis pub/sub client
│   │   └── websocket_manager.py  # WebSocket connection manager
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── websocket.py          # WebSocket endpoint
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py         # Health check endpoint
│   │       └── scrape.py         # Scrape trigger endpoint
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── messages.py           # Pydantic models for pub/sub
│   │   └── database_tables.py    # Pydantic models for DB entities
│   │
│   └── services/
│       ├── __init__.py
│       ├── database_service.py   # Supabase CRUD operations
│       └── email_service.py      # Resend email (disabled)
│
└── worker/
    ├── __init__.py
    ├── celery_app.py             # Celery config + tasks
    └── tasks/                    # (tasks defined in celery_app.py for now)
        └── __init__.py
```

---

## Database Schema

### Supabase Tables

#### Table: `preferences`

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| user_id | UUID | - | PRIMARY KEY, references auth.users |
| job_title | TEXT | NULL | User's desired job title |
| location | TEXT | NULL | Preferred location |
| job_type | TEXT | NULL | Full-time, Part-time, etc. |
| salary | TEXT | NULL | Salary preference |
| created_at | TIMESTAMP | NOW() | Auto-set |
| updated_at | TIMESTAMP | NOW() | Auto-set |

#### Table: `jobs`

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| id | INT8 | IDENTITY | PRIMARY KEY, auto-generated |
| user_id | UUID | - | References auth.users |
| title | TEXT | NULL | Job title |
| company_name | TEXT | NULL | Company name |
| location | TEXT | NULL | Job location |
| job_type | TEXT | NULL | Employment type |
| salary | TEXT | NULL | Salary info |
| url | TEXT | NULL | Application URL |
| posted_date | TEXT | NULL | When job was posted |
| scraped_at | TIMESTAMP | NOW() | When we scraped it |

### Supabase Auth Integration

Users are stored in Supabase's built-in `auth.users` table. A database trigger auto-creates a `preferences` row when a new user signs up:

```sql
-- Function to create preferences row
CREATE OR REPLACE FUNCTION public.create_user_preferences()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.preferences (user_id)
    VALUES (NEW.id);
    RETURN NEW;
END;
$$;

-- Trigger on auth.users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.create_user_preferences();
```

### Foreign Keys

Both `jobs.user_id` and `preferences.user_id` reference `auth.users(id)` with `ON DELETE CASCADE`.

---

## Component Details

### 1. Config (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    scrape_update_channel: str = "scrape_updates"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Email (Resend) - disabled for now
    resend_api_key: str = ""
    from_email: str = ""
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    # Testing
    test_user_id: str  # Temporary until auth implemented

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Redis Client (`app/core/redis_client.py`)

Async Redis client for pub/sub. Singleton pattern.

**Key Methods:**
- `connect()`: Establish Redis connection
- `disconnect()`: Cancel subscriber, close connections
- `subscribe(channel, handler)`: Start background listener
- `_listener(handler)`: Loop calling handler on messages

**Design Notes:**
- Uses `get_message(timeout=1.0)` for clean cancellation (not `listen()`)
- `ignore_subscribe_messages=True` skips Redis confirmation messages
- Handler receives JSON string, validates with Pydantic

### 3. WebSocket Manager (`app/core/websocket_manager.py`)

Single WebSocket connection for MVP.

```python
class WebSocketManager:
    def __init__(self) -> None:
        self.connection: WebSocket | None = None
    
    async def connect(self, websocket: WebSocket) -> None
    def disconnect(self) -> None
    async def broadcast(self, message: dict) -> None
```

**Design Decision:** Single connection, not per-task. MVP is single user. All task updates go to same WebSocket. Message includes `query` and `location` so frontend knows which scrape completed.

### 4. Database Service (`app/services/database_service.py`)

Supabase client + CRUD functions. Singleton client created at module load.

**Functions:**
- `get_jobs(user_id)` → List all user's jobs
- `get_job_by_id(user_id, job_id)` → Single job details (not implemented yet)
- `create_job(user_id, job_data)` → Insert job row
- `get_preferences(user_id)` → Get user preferences
- `update_preference(user_id, update)` → Update preferences
- `get_user_email(user_id)` → Get email from Supabase Auth

**Important:** When inserting jobs, exclude `id` field:
```python
job = {'user_id': user_id, **job_data.model_dump(exclude={'id'})}
```

### 5. Celery App (`worker/celery_app.py`)

Celery configuration and tasks.

**Configuration:**
```python
celery_app = Celery(
    'jobflow', 
    broker=settings.redis_url, 
    backend=settings.redis_url
)
```

**Tasks:**
- `run_scrape(user_id, preferences)` - Main scrape task
- `scheduled_scrape()` - Celery Beat scheduled task (future)

**Beat Schedule:**
```python
celery_app.conf.beat_schedule = {
    "scheduled-scrape": {
        "task": "worker.celery_app.scheduled_scrape",
        "schedule": crontab(hour="*/6"),
    },
}
```

### 6. Messages Schema (`app/schemas/messages.py`)

```python
class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapeUpdateMessage(BaseModel):
    status: Status
    jobs_found: int = 0
    error_message: Optional[str] = None
```

### 7. Database Tables Schema (`app/schemas/database_tables.py`)

```python
class Job(BaseModel):
    id: Optional[int] = None  # int, not str - matches DB
    title: str
    company_name: str
    location: str
    job_type: str
    salary: Optional[str] = None
    url: str
    posted_date: Optional[str] = None

class Preference(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None
```

---

## API Endpoints

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/scrape` | Trigger scrape job |

### WebSocket Endpoints

| Path | Description |
|------|-------------|
| `/ws/scrape` | Real-time scrape status updates |

### Scrape Endpoint Details

**Request:** `POST /api/scrape`

No body required (uses test user ID and their preferences).

**Response:**
```json
{
    "status": "pending",
    "jobs_found": 0,
    "error_message": null
}
```

**WebSocket Messages:**
```json
{"status": "running", "jobs_found": 0, "error_message": null}
{"status": "completed", "jobs_found": 1, "error_message": null}
```

---

## Key Decisions

### 1. No task_id in Messages

**Decision:** Remove `task_id` from pub/sub messages.

**Reason:** End user has no use for Celery's internal task ID. Instead, messages can include `query` and `location` if needed to identify which scrape completed.

### 2. Celery Task Returns Nothing

**Decision:** `run_scrape` returns `None`.

**Reason:** Nobody consumes the return value. Status updates go via Redis pub/sub. Celery result backend not needed.

### 3. Sync Database Functions (Not Async)

**Decision:** Database service functions are synchronous.

**Reason:** 
- Supabase Python SDK is sync
- FastAPI handles sync functions in thread pool automatically
- Celery workers are sync
- No performance issue for MVP

### 4. Single WebSocket Connection

**Decision:** One global WebSocket connection, not per-task.

**Reason:** MVP is single user. Multiple scrapes go to same connection. Frontend tracks by query/location in message.

### 5. Preferences in Database (Not Redis)

**Decision:** Store preferences in Supabase, not Redis.

**Reason:** Need persistence. Scheduled scraper reads preferences from DB.

### 6. Email Disabled

**Decision:** Comment out email service calls.

**Reason:** Resend requires verified domain. Skipped for MVP.

### 7. TEXT Over VARCHAR

**Decision:** Use `TEXT` type in PostgreSQL, not `VARCHAR(n)`.

**Reason:** No performance difference in PostgreSQL. Avoids arbitrary length limits.

### 8. user_id References auth.users

**Decision:** Foreign key to `auth.users`, not custom users table.

**Reason:** Using Supabase Auth. No need for separate users table.

---

## Issues & Fixes

### Issue 1: Trigger Failing on User Signup

**Symptom:** "Database error creating new user"

**Cause:** Trigger tried to insert into preferences, but:
1. `id` column had no default
2. `user_id` had `auth.uid()` default which conflicts with trigger

**Fix:**
1. Removed `id` column from preferences, made `user_id` primary key
2. Dropped `auth.uid()` default from `user_id`
3. Recreated trigger with explicit `public` schema

```sql
ALTER TABLE public.preferences ALTER COLUMN user_id DROP DEFAULT;
```

### Issue 2: 400 Bad Request on Job Insert

**Symptom:** Supabase returned 400 when inserting job

**Cause:** Code sent `id: None` but table expected integer

**Fix:** Exclude `id` when dumping Pydantic model:
```python
job = {'user_id': user_id, **job_data.model_dump(exclude={'id'})}
```

### Issue 3: Pydantic Model in Celery Task

**Symptom:** ValueError when task received arguments

**Cause:** Celery serializes to JSON. Pydantic model type hint expects object, receives dict.

**Fix:** Accept `dict` in task signature:
```python
@celery_app.task
def run_scrape(user_id: str, preferences: dict):  # dict, not Preference
```

### Issue 4: Job Model id Type Mismatch

**Symptom:** Pydantic validation error

**Cause:** Model had `id: Optional[str]`, table has `int8`

**Fix:**
```python
class Job(BaseModel):
    id: Optional[int] = None  # int, not str
```

### Issue 5: Email Send Failure

**Symptom:** "Domain not verified" error from Resend

**Cause:** No verified domain for sending emails

**Fix:** Disabled email for MVP. Comment out email service calls.

---

## Current Status

### Working ✅

- [x] FastAPI app starts with Redis connection
- [x] Redis pub/sub subscription on startup
- [x] WebSocket endpoint accepts connections
- [x] POST /api/scrape triggers Celery task
- [x] Celery worker picks up and executes task
- [x] Task publishes status updates to Redis
- [x] FastAPI forwards updates to WebSocket
- [x] Job inserted into Supabase successfully
- [x] Preferences table populated on user signup (via trigger)

### Disabled/Skipped ⏸️

- [ ] Email notifications (no verified domain)
- [ ] Authentication (using test user ID)
- [ ] Actual scraping logic (mock data only)
- [ ] Scheduled scraping via Celery Beat
- [ ] Frontend WebSocket integration

### Not Started ❌

- [ ] Scrapy spider implementation
- [ ] Indeed scraping
- [ ] Multiple job board support
- [ ] AI CV/Cover Letter module
- [ ] Auto-apply module

---

## Next Steps

### Immediate (MVP Completion)

1. **Test end-to-end flow:**
   - Verify WebSocket receives updates in frontend
   - Confirm job appears in Supabase after scrape

2. **Implement Scrapy spider:**
   - Replace mock data with actual Indeed scraping
   - Handle pagination, rate limiting

3. **Add authentication:**
   - Implement Supabase Auth in frontend
   - Add `get_current_user` dependency in FastAPI
   - Remove `test_user_id` hardcoding

4. **Enable scheduled scraping:**
   - Run Celery Beat
   - Implement `scheduled_scrape` task to read preferences

### Post-MVP

1. **Email notifications:**
   - Set up custom domain
   - Verify with Resend
   - Re-enable email service

2. **Multiple job boards:**
   - LinkedIn, Glassdoor, etc.
   - Abstract scraper interface

3. **AI modules:**
   - CV optimization
   - Cover letter generation
   - Auto-apply workflow

---

## Running the Project

### Prerequisites

- Python 3.11+
- Docker (for Redis)
- Supabase account

### Setup

```bash
cd backend
python -m venv env
source env/bin/activate  # or `env\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
```

### Start Services

**Terminal 1: Redis**
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

**Terminal 2: FastAPI**
```bash
fastapi dev app/main.py
```

**Terminal 3: Celery Worker**
```bash
celery -A worker.celery_app worker --loglevel=info
```

**Terminal 4: Celery Beat (optional)**
```bash
celery -A worker.celery_app beat --loglevel=info
```

### Test

```bash
curl -X POST http://localhost:8000/api/scrape
```

Check:
- Celery terminal shows task execution
- Supabase Table Editor shows new job row
- WebSocket (if connected) receives status updates

---

## Environment Variables

```bash
# .env

# Redis
REDIS_URL=redis://localhost:6379/0

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Email (disabled)
RESEND_API_KEY=re_xxxxx
FROM_EMAIL=notifications@yourdomain.com

# Testing
TEST_USER_ID=your-test-user-uuid-from-supabase
```

---

## Dependencies

```txt
# requirements.txt

# API
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0

# Task Queue
celery>=5.3.0
redis>=5.0.0

# Database
supabase>=2.0.0

# Email (disabled for now)
resend>=0.8.0
```
