# JobFlow - Complete Architecture Documentation

## Table of Contents
1. [Authentication Flow](#authentication-flow)
2. [Scraping API Flow](#scraping-api-flow)
3. [Complete Scraper Pipeline](#complete-scraper-pipeline)

---

# Authentication Flow

## Overview
JobFlow uses **Supabase Authentication** with **JWT tokens** for secure user authentication. The frontend authenticates with Supabase, receives a JWT token, and sends it to the FastAPI backend for verification.

## Architecture Diagram
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Frontend  │────────▶│  Supabase   │         │   Backend   │
│  (Next.js)  │         │    Auth     │         │  (FastAPI)  │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       │  1. Sign In           │                       │
       │──────────────────────▶│                       │
       │                       │                       │
       │  2. JWT Token         │                       │
       │◀──────────────────────│                       │
       │                       │                       │
       │  3. API Request + JWT │                       │
       │───────────────────────────────────────────────▶│
       │                       │                       │
       │                       │  4. Fetch JWKS        │
       │                       │◀──────────────────────│
       │                       │                       │
       │                       │  5. Public Keys       │
       │                       │──────────────────────▶│
       │                       │                       │
       │                       │  6. Verify Token      │
       │                       │       (RS256)         │
       │                       │                       │
       │  7. Response (with user_id)                   │
       │◀───────────────────────────────────────────────│
       │                       │                       │
```

---

## Step-by-Step Authentication Flow

### Step 1: User Sign In/Sign Up

**File:** `frontend/masa/src/app/sign-in/page.tsx`

```typescript
const handleSignIn = async (e: React.FormEvent) => {
  e.preventDefault();

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;

  // Redirect to dashboard on success
  router.push('/');
  router.refresh();
};
```

**What happens:**
- User enters email and password
- Frontend sends credentials to Supabase Auth API
- Supabase validates credentials and returns a **JWT access token**
- Token is stored in Supabase client session storage

---

### Step 2: Frontend Checks Authentication

**File:** `frontend/masa/src/app/page.tsx`

```typescript
// Check authentication on mount
useEffect(() => {
  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      router.push('/sign-in');  // Redirect if not authenticated
      return;
    }

    setAuthToken(session.access_token);  // Store JWT token
    setIsLoading(false);
  };

  checkAuth();

  // Listen for auth state changes
  const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    if (!session) {
      router.push('/sign-in');
    } else {
      setAuthToken(session.access_token);
    }
  });

  return () => subscription.unsubscribe();
}, [router]);
```

**What happens:**
- On page load, check if user has an active session
- If session exists, extract JWT token from `session.access_token`
- If no session, redirect to sign-in page
- Monitor auth state for logout/session expiry

---

### Step 3: Frontend Makes API Request with JWT

**File:** `frontend/masa/src/app/page.tsx`

```typescript
// Helper function to get auth headers
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authToken}`,
  'Content-Type': 'application/json',
});

// Example API call
const fetchJobs = async () => {
  if (!authToken) return;

  const response = await fetch(`${API_URL}/api/get_jobs`, {
    headers: getAuthHeaders(),  // Include JWT token
  });

  if (response.ok) {
    const jobsList = await response.json();
    setJobs(jobsList || []);
  }
};
```

**What happens:**
- Every API request includes `Authorization: Bearer <JWT_TOKEN>` header
- JWT token contains user info encrypted by Supabase
- Token is sent to backend for verification

---

### Step 4: Backend Receives Request

**File:** `backend/app/api/routers/get_jobs.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_jobs", response_model=list[Job])
async def get_jobs(user_id: str = Depends(get_current_user_id)) -> list[Job]:
    # user_id is automatically extracted from JWT by get_current_user_id
    try:
        jobs = get_jobs_from_db(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    return jobs
```

**What happens:**
- FastAPI route uses `Depends(get_current_user_id)` dependency
- This dependency automatically extracts and validates JWT token
- If token is valid, `user_id` is passed to the function
- If token is invalid/expired, HTTP 401 Unauthorized is returned

---

### Step 5: Backend Verifies JWT Token

**File:** `backend/app/core/auth.py`

```python
import jwt
import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def get_jwks():
    """
    Fetch JSON Web Key Set (JWKS) from Supabase
    JWKS contains public keys to verify JWT signatures
    """
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"

    response = requests.get(jwks_url, timeout=5)
    return response.json()

def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify Supabase JWT token using RS256 algorithm
    """
    token = credentials.credentials

    # Get JWKS (cached to avoid repeated requests)
    jwks = get_jwks()

    # Decode token header to get key ID
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get('kid')

    # Find matching public key in JWKS
    signing_key = None
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            break

    if not signing_key:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify and decode token using public key
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience="authenticated",
        options={"verify_exp": True}  # Check expiration
    )

    # Extract user info from token payload
    user_id = payload.get("sub")
    user_metadata = payload.get("user_metadata", {})

    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "display_name": user_metadata.get("display_name"),
        "metadata": user_metadata
    }

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    FastAPI dependency to extract user_id from JWT
    """
    user_info = verify_token(credentials)
    return user_info["user_id"]
```

**What happens:**
1. **Fetch JWKS:** Backend fetches public keys from Supabase (cached)
2. **Extract Key ID:** Decode JWT header to find which key was used
3. **Find Public Key:** Match key ID to corresponding public key in JWKS
4. **Verify Signature:** Use public key to verify JWT was signed by Supabase
5. **Validate Claims:** Check token hasn't expired and has correct audience
6. **Extract User Info:** Return user_id and metadata from token payload

---

### Step 6: WebSocket Authentication

**File:** `frontend/masa/src/app/page.tsx`

```typescript
useEffect(() => {
  if (!authToken) return;

  // WebSocket connection with token as query parameter
  const socket = new WebSocket(`${WS_URL}/ws/scrape?token=${authToken}`);

  socket.onopen = () => console.log("WebSocket connected");
  socket.onmessage = (event) => {
    const data: ScrapeUpdate = JSON.parse(event.data);
    setUpdates((prev) => [...prev, data]);
  };

  return () => socket.close();
}, [authToken]);
```

**File:** `backend/app/core/auth.py`

```python
async def get_websocket_user_id(token: str) -> str:
    """
    WebSocket authentication - accepts token from query parameter
    Browser WebSocket can't send custom headers, so we use query param
    """
    class TokenCredentials:
        def __init__(self, token):
            self.credentials = token

    user_info = verify_token(TokenCredentials(token))
    return user_info["user_id"]
```

**File:** `backend/app/api/websocket.py`

```python
@router.websocket("/scrape")
async def scrape_websocket(
    websocket: WebSocket,
    user_id: str = Depends(get_websocket_user_id)  # Token from query param
):
    await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
```

**What happens:**
- Browser WebSocket can't send `Authorization` header
- Token is passed as query parameter: `?token=<JWT>`
- `get_websocket_user_id` extracts and verifies token
- WebSocket manager stores connection with user_id
- User receives real-time scrape updates for their account only

---

## Security Features

### JWT Token Structure
```
eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1In0.eyJzdWIiOiJ1c2VyLWlkIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNjE2MjM5MDIyfQ.signature

Header (Algorithm + Key ID) . Payload (User Data) . Signature
```

### Token Validation Checklist
- ✅ **Signature Verification:** Ensures token was signed by Supabase
- ✅ **Expiration Check:** Rejects expired tokens
- ✅ **Audience Validation:** Confirms token is for our application
- ✅ **Algorithm Check:** Only accepts RS256 (asymmetric encryption)

### Why This is Secure
1. **No Password Storage:** Backend never sees user passwords
2. **Asymmetric Encryption:** Backend only has public key (can verify, not create tokens)
3. **Stateless:** No session storage needed in backend
4. **Short-lived Tokens:** Tokens expire, limiting damage if compromised
5. **JWKS Rotation:** Supabase can rotate keys without code changes

---

# Scraping API Flow

## Overview
JobFlow uses **Celery** with **Redis** for asynchronous job scraping. When a user triggers a scrape, the request is queued in Redis, processed by a Celery worker, and updates are sent via WebSocket.

## Architecture Diagram
```
┌──────────┐      ┌──────────┐      ┌───────┐      ┌────────────┐
│ Frontend │─────▶│ FastAPI  │─────▶│ Redis │─────▶│   Celery   │
│          │      │  /scrape │      │ Queue │      │   Worker   │
└──────────┘      └──────────┘      └───────┘      └────────────┘
     │                                                     │
     │                                                     │
     │                                                     ▼
     │              ┌───────────────────────────────────────────┐
     │              │         run_scrape Task               │
     │              │  1. Get user preferences              │
     │              │  2. Run Scrapy spider                 │
     │              │  3. Send WebSocket updates            │
     │              │  4. Save jobs to database             │
     │              └───────────────────────────────────────────┘
     │                                                     │
     │              ┌──────────────────┐                  │
     └─────────────▶│ WebSocket Manager│◀──────────────────┘
                    │  (Real-time      │
                    │   Updates)       │
                    └──────────────────┘
```

---

## Step-by-Step Scraping Flow

### Step 1: User Triggers Scrape

**File:** `frontend/masa/src/app/page.tsx`

```typescript
const handleStartScrape = async () => {
  if (!authToken || isScraperRunning) return;

  setIsScraperRunning(true);

  const response = await fetch(`${API_URL}/api/scrape`, {
    method: 'POST',
    headers: getAuthHeaders(),  // Include JWT token
  });

  const result = await response.json();
  console.log('Scrape started:', result);
};
```

**What happens:**
- User clicks "Start Scrape" button
- Frontend sends POST request to `/api/scrape` with JWT token
- UI shows scrape is running

---

### Step 2: FastAPI Receives Scrape Request

**File:** `backend/app/api/routers/scrape.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import get_current_user_id
from worker.celery_app import run_scrape

@router.post("/scrape", response_model=ScrapeUpdateMessage)
async def scrape(user_id: str = Depends(get_current_user_id)) -> ScrapeUpdateMessage:
    # Get user's search preferences from database
    preferences = get_preferences(user_id)
    if preferences is None:
        raise HTTPException(status_code=400, detail="No preferences set")

    # Queue the scrape task in Celery/Redis
    run_scrape.delay(user_id, preferences.model_dump())

    # Return immediate response (scrape runs asynchronously)
    update = ScrapeUpdateMessage(status=Status.PENDING, jobs_found=0)
    return update
```

**What happens:**
1. **Authentication:** Extract `user_id` from JWT token
2. **Get Preferences:** Fetch user's job search criteria (title, location, etc.)
3. **Queue Task:** Send scrape task to Celery via `run_scrape.delay()`
4. **Immediate Response:** Return "pending" status (don't wait for scrape to finish)

---

### Step 3: Task Queued in Redis

**File:** `worker/celery_app.py`

```python
from celery import Celery

# Celery app configuration
celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',      # Redis connection for task queue
    backend='redis://localhost:6379/0'      # Redis for storing results
)

@celery_app.task(bind=True)
def run_scrape(self, user_id: str, preferences: dict):
    """
    Celery task - runs asynchronously in background worker
    """
    # This will be executed by Celery worker
    pass
```

**What happens:**
- `run_scrape.delay()` serializes task parameters
- Task is pushed to Redis queue
- FastAPI returns immediately (doesn't wait)
- Celery worker picks up task from Redis

**Redis Queue Structure:**
```
Redis Queue: celery
├── Task 1: run_scrape(user_id="abc123", preferences={...})
├── Task 2: run_scrape(user_id="def456", preferences={...})
└── Task 3: ...
```

---

### Step 4: Celery Worker Processes Task

**File:** `worker/celery_app.py`

```python
from scraper.scraper_service import run_scraper_with_preferences

@celery_app.task(bind=True)
def run_scrape(self, user_id: str, preferences: dict):
    """
    Main Celery task for running web scraper
    """
    task_id = self.request.id  # Celery generates unique task ID

    print(f"Starting scrape for user {user_id} with task {task_id}")

    # Send initial WebSocket update
    send_update(user_id, {
        "task_id": task_id,
        "status": "running",
        "jobs_found": 0
    })

    try:
        # Run the actual scraper
        run_scraper_with_preferences(user_id, preferences, task_id)

        # Send success update
        send_update(user_id, {
            "task_id": task_id,
            "status": "completed",
            "jobs_found": count_jobs(user_id)
        })

    except Exception as e:
        # Send error update
        send_update(user_id, {
            "task_id": task_id,
            "status": "failed",
            "error_message": str(e)
        })
```

**What happens:**
1. **Worker Picks Task:** Celery worker dequeues task from Redis
2. **Send Running Update:** Notify user scrape has started
3. **Execute Scraper:** Call main scraper function
4. **Send Completion:** Notify user when finished
5. **Error Handling:** Catch failures and notify user

---

### Step 5: Send WebSocket Updates via Redis Pub/Sub

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
def publish_update(message):
    """Publish scrape update to Redis for real-time frontend updates"""
    try:
        import redis
        import json

        # Read Redis settings from environment variables
        redis_url = os.environ.get('REDIS_URL')
        scrape_update_channel = os.environ.get('SCRAPE_UPDATE_CHANNEL')

        r = redis.from_url(redis_url)
        message_json = json.dumps(message)
        r.publish(scrape_update_channel, message_json)
        r.close()

    except Exception as e:
        print(f"Redis publishing failed: {e}")
        pass

# Spider publishes updates with user_id
page_update = {
    'user_id': self.user_id,  # CRITICAL: Must include user_id
    'status': 'running',
    'jobs_found': self.jobs_scraped,
    'page_completed': page_num,
}
publish_update(page_update)
```

**File:** `backend/app/main.py`

```python
from app.core.redis_client import redis_client
from app.core.websocket_manager import websocket_manager
from app.schemas.messages import ScrapeUpdateMessage

async def handle_scrape_update(message: dict):
    """
    Handle scrape updates from Redis and forward to WebSocket
    Called when spider publishes to Redis channel
    """
    try:
        # Validate message with Pydantic schema
        update = ScrapeUpdateMessage.model_validate(message)
    except ValidationError as e:
        print(f'Invalid message: {e}')
        return

    # Extract user_id from message (REQUIRED field)
    user_id = message.get('user_id')
    if not user_id:
        print(f'No user_id in scrape update message')
        return

    # Forward to specific user's WebSocket connection
    await websocket_manager.send_to_user(user_id=user_id, message=update.model_dump(mode='json'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP - Subscribe to Redis channel
    await redis_client.connect()
    await redis_client.subscribe(settings.scrape_update_channel, handle_scrape_update)

    yield

    # SHUTDOWN
    await redis_client.disconnect()
```

**File:** `backend/app/schemas/messages.py`

```python
class ScrapeUpdateMessage(BaseModel):
    """
    Message published to Redis when scrape task status changes
    """
    user_id: str  # REQUIRED - identifies which user to send update to
    status: Status
    jobs_found: int = 0
    error_message: Optional[str] = None
    spider_finished: Optional[bool] = None
    page_completed: Optional[int] = None
    jobs_from_page: Optional[int] = None
```

**File:** `backend/app/core/websocket_manager.py`

```python
class WebSocketManager:
    def __init__(self):
        # Store ONE WebSocket connection per user
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection for a user"""
        if user_id in self.connections:
            try:
                self.disconnect(user_id)
            except:
                pass
            print(f"User {user_id} reconnected. Closed old connection.")

        await websocket.accept()
        self.connections[user_id] = websocket

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user's connection"""
        if user_id not in self.connections:
            print(f"User {user_id} is not connected")
            return

        websocket = self.connections[user_id]

        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f'Error sending to user {user_id}: {e}')
            self.disconnect(user_id)

# Global singleton instance
websocket_manager = WebSocketManager()
```

**What happens:**
1. **Spider Publishes to Redis:** Spider calls `publish_update()` with `user_id` included
2. **FastAPI Subscribes:** Main app listens to Redis pub/sub channel via `handle_scrape_update()`
3. **Validate Message:** Parse with Pydantic schema to ensure correct format
4. **Extract user_id:** Get target user from message (REQUIRED field)
5. **Find Connection:** Look up WebSocket in dictionary by `user_id`
6. **Send JSON Message:** Push update through WebSocket to that specific user
7. **Handle Errors:** If connection dropped, clean up dictionary
8. **Singleton Pattern:** One manager instance shared across entire app

**Why Redis Pub/Sub?**
- Spider runs in separate subprocess (can't directly access WebSocket manager)
- Redis acts as message bus between Scrapy spider and FastAPI server
- Allows real-time updates without blocking scraper
- Decouples scraper from web server

---

### Step 6: Frontend Receives Real-time Updates

**File:** `frontend/masa/src/app/page.tsx`

```typescript
socket.onmessage = (event) => {
  const data: ScrapeUpdate = JSON.parse(event.data);
  console.log("Received websocket data:", data);

  // Add update to UI
  setUpdates((prev) => [...prev, {
    ...data,
    timestamp: new Date().toLocaleTimeString()
  }]);

  // If scrape completed, refresh job lists
  if (data.status === 'completed') {
    setIsScraperRunning(false);
    fetchJobs();
    fetchSavedJobs();
    fetchUserStatistics();
  }
};
```

**What happens:**
- WebSocket receives JSON message from backend
- Parse message and add to updates list
- Update UI to show progress
- When completed, refresh all data

---

## Message Flow Timeline

```
Time  │ Component        │ Action
──────┼──────────────────┼────────────────────────────────────
00:00 │ Frontend         │ POST /api/scrape
00:01 │ FastAPI          │ Authenticate user
00:02 │ FastAPI          │ Get preferences from DB
00:03 │ FastAPI          │ Queue task in Redis
00:04 │ FastAPI          │ Return 200 OK {"status": "pending"}
00:05 │ Celery Worker    │ Pick task from Redis
00:06 │ Celery Worker    │ WebSocket: {"status": "running"}
00:07 │ Scraper          │ Start scraping Indeed
00:08 │ Scraper          │ WebSocket: {"page": 1, "jobs": 25}
00:15 │ Scraper          │ WebSocket: {"page": 2, "jobs": 50}
00:22 │ Scraper          │ WebSocket: {"page": 3, "jobs": 75}
01:30 │ Scraper          │ Save to database
01:31 │ Celery Worker    │ WebSocket: {"status": "completed"}
01:32 │ Frontend         │ Refresh jobs list
```

---

# Complete Scraper Pipeline

## Overview
The scraper uses **Scrapy** framework with **Playwright** for browser automation to scrape job listings from Indeed, match them against user preferences, and save to database.

## Architecture Diagram
```
┌────────────────────┐
│  run_scrape Task   │
│   (Celery)         │
└─────────┬──────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  run_scraper_with_preferences                          │
│  1. Configure Scrapy settings                          │
│  2. Set up Playwright browser                          │
│  3. Create spider with user preferences                │
│  4. Run spider via CrawlerProcess                      │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  IndeedSpider (Scrapy Spider)                          │
│  ┌──────────────────────────────────────────────┐     │
│  │  start_requests()                            │     │
│  │  → Generate Indeed search URL                │     │
│  │  → Create initial Playwright request         │     │
│  └──────────────┬───────────────────────────────┘     │
│                 │                                       │
│                 ▼                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │  parse()                                     │     │
│  │  → Extract job cards from page               │     │
│  │  → Parse each job card                       │     │
│  │  → Send to database pipeline                 │     │
│  │  → Follow pagination (next page)             │     │
│  └──────────────┬───────────────────────────────┘     │
│                 │                                       │
│                 ▼                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │  parse_job_card()                            │     │
│  │  → Extract job details (title, company...)  │     │
│  │  → Match against preferences                │     │
│  │  → Create JobItem                           │     │
│  └──────────────┬───────────────────────────────┘     │
└─────────────────┼───────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│  DatabasePipeline                                      │
│  1. Check if job already exists (URL)                  │
│  2. Save job to Supabase                               │
│  3. Send WebSocket update                              │
│  4. Update statistics                                  │
└────────────────────────────────────────────────────────┘
```

---

## Step 1: Initialize Scraper

**File:** `backend/scraper/scraper_service.py`

```python
from scrapy.crawler import CrawlerProcess
from backend.scraper.indeed_scraper.spiders.indeed_spider import IndeedSpider

def run_scraper_with_preferences(user_id: str, preferences: dict, task_id: str):
    """
    Main entry point for running scraper with user preferences
    """

    # Configure Scrapy settings
    settings = {
        # Playwright for JavaScript rendering
        'DOWNLOAD_HANDLERS': {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",

        # Pipelines for data processing
        'ITEM_PIPELINES': {
            'backend.scraper.indeed_scraper.pipelines.DatabasePipeline': 300,
        },

        # Concurrent requests
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,

        # User agent rotation
        'USER_AGENT': get_random_user_agent(),
    }

    # Create crawler process
    process = CrawlerProcess(settings=settings)

    # Start spider with user preferences
    process.crawl(
        IndeedSpider,
        user_id=user_id,
        preferences=preferences,
        task_id=task_id
    )

    # Block until spider finishes
    process.start()
```

**What happens:**
1. **Configure Scrapy:** Set up Playwright, pipelines, concurrency
2. **Create Process:** Initialize Scrapy crawler
3. **Pass Parameters:** Send user_id, preferences, task_id to spider
4. **Start Crawling:** Begin scraping (blocks until complete)

---

## Step 2: Spider Initialization

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
class IndeedSpider(scrapy.Spider):
    name = "indeed"

    def __init__(self, user_id: str, preferences: dict, task_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Store user context
        self.user_id = user_id
        self.task_id = task_id
        self.preferences = preferences

        # Extract search parameters
        self.job_title = preferences.get('title', '')
        self.location = preferences.get('location', '')
        self.max_jobs = preferences.get('scrape_length', 150)

        # Counters
        self.jobs_scraped = 0
        self.page_count = 0

        print(f"Spider initialized for user {user_id}")
        print(f"Searching for: {self.job_title} in {self.location}")
```

**What happens:**
- Spider is initialized with user-specific parameters
- Extract search criteria from preferences
- Set up counters for tracking progress

---

## Step 3: Generate Search URL

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
def start_requests(self):
    """
    Generate initial Indeed search URL and start crawling
    """
    # Build Indeed search URL
    base_url = "https://www.indeed.com/jobs"
    params = {
        'q': self.job_title,           # Job title search
        'l': self.location,            # Location
        'fromage': '7',                # Last 7 days
        'sort': 'date',                # Sort by date
        'start': 0                     # Pagination offset
    }

    search_url = f"{base_url}?{urlencode(params)}"

    print(f"Starting scrape: {search_url}")

    # Send WebSocket update
    send_websocket_update(self.user_id, {
        'task_id': self.task_id,
        'status': 'running',
        'jobs_found': 0,
        'source': 'indeed'
    })

    # Create Playwright request (renders JavaScript)
    yield scrapy.Request(
        url=search_url,
        callback=self.parse,
        meta={
            'playwright': True,
            'playwright_include_page': True,
        }
    )
```

**What happens:**
1. **Build URL:** Construct Indeed search with user's title and location
2. **Send Update:** Notify user scrape is starting
3. **Yield Request:** Create Playwright request (needed for JavaScript rendering)

---

## Step 4: Parse Search Results Page

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
async def parse(self, response):
    """
    Parse Indeed search results page
    Extract job cards and follow pagination
    """
    page = response.meta['playwright_page']

    self.page_count += 1
    print(f"Parsing page {self.page_count}")

    # Wait for job cards to load
    await page.wait_for_selector('.job_seen_beacon', timeout=10000)

    # Extract all job cards on page
    job_cards = response.css('.job_seen_beacon')

    print(f"Found {len(job_cards)} job cards on page {self.page_count}")

    # Parse each job card in parallel
    for card in job_cards:
        # Check if we've reached max jobs
        if self.jobs_scraped >= self.max_jobs:
            print(f"Reached max jobs limit: {self.max_jobs}")
            await page.close()
            return

        # Parse individual job card
        job_item = self.parse_job_card(card)

        if job_item:
            self.jobs_scraped += 1
            yield job_item  # Send to pipeline

    # Send progress update
    send_websocket_update(self.user_id, {
        'task_id': self.task_id,
        'status': 'running',
        'page_completed': self.page_count,
        'jobs_from_page': len(job_cards),
        'jobs_found': self.jobs_scraped
    })

    # Follow pagination to next page
    if self.jobs_scraped < self.max_jobs:
        next_button = response.css('a[data-testid="pagination-page-next"]::attr(href)').get()

        if next_button:
            next_url = response.urljoin(next_button)
            print(f"Following pagination to: {next_url}")

            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={'playwright': True, 'playwright_include_page': True}
            )
        else:
            print("No more pages to scrape")

    await page.close()
```

**What happens:**
1. **Wait for Content:** Ensure job cards loaded via JavaScript
2. **Extract Cards:** Get all job listings from page
3. **Parse Each Card:** Extract details from each listing
4. **Send Progress:** Update user with page completion
5. **Pagination:** Follow "next page" link if needed
6. **Cleanup:** Close Playwright page

---

## Step 5: Parse Individual Job Card

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
def parse_job_card(self, card):
    """
    Extract job details from a single job card
    Match against user preferences
    """
    try:
        # Extract basic info
        title = card.css('h2.jobTitle span::attr(title)').get()
        company = card.css('[data-testid="company-name"]::text').get()
        location = card.css('[data-testid="text-location"]::text').get()

        # Extract job URL
        job_link = card.css('h2.jobTitle a::attr(href)').get()
        job_url = f"https://www.indeed.com{job_link}" if job_link else None

        # Extract salary (if available)
        salary = card.css('[data-testid="attribute_snippet_testid"]::text').get()

        # Extract job type (full-time, part-time, etc.)
        job_type_elements = card.css('.metadata div::text').getall()
        job_type = ', '.join([t.strip() for t in job_type_elements if t.strip()])

        # Extract description snippet
        description = card.css('.job-snippet::text').getall()
        description_text = ' '.join(description).strip()

        # Match against user preferences
        if not self.match_preferences(title, company, location, description_text):
            print(f"Job doesn't match preferences: {title}")
            return None

        # Create job item
        job_item = JobItem(
            user_id=self.user_id,
            title=title,
            company_name=company,
            location=location,
            job_type=job_type,
            salary=salary or "Not specified",
            url=job_url,
            description=description_text,
            benefits="",  # Would need to click into job for full details
            priority=False
        )

        print(f"✓ Scraped: {title} at {company}")

        return job_item

    except Exception as e:
        print(f"Error parsing job card: {e}")
        return None
```

**What happens:**
1. **Extract Fields:** Pull title, company, location, salary, etc. from HTML
2. **Build URL:** Construct full job URL
3. **Match Preferences:** Filter jobs that don't match user criteria
4. **Create Item:** Build JobItem object
5. **Return:** Yield item to pipeline (or None if doesn't match)

---

## Step 6: Match User Preferences

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
def match_preferences(self, title: str, company: str, location: str, description: str) -> bool:
    """
    Check if job matches user's preferences
    """
    prefs = self.preferences

    # Title matching (flexible - contains keywords)
    if prefs.get('title'):
        title_keywords = prefs['title'].lower().split()
        title_lower = title.lower()

        # At least one keyword must match
        if not any(keyword in title_lower for keyword in title_keywords):
            return False

    # Company matching (if specified)
    if prefs.get('company_name'):
        if prefs['company_name'].lower() not in company.lower():
            return False

    # Location matching (if specified)
    if prefs.get('location'):
        pref_location = prefs['location'].lower()
        job_location = location.lower()

        # Check if locations overlap
        if pref_location not in job_location and job_location not in pref_location:
            # Allow "remote" to match anywhere
            if 'remote' not in pref_location and 'remote' not in job_location:
                return False

    # Description keywords (if specified)
    if prefs.get('description'):
        desc_keywords = prefs['description'].lower().split()
        desc_lower = description.lower()

        # At least one keyword must match
        if not any(keyword in desc_lower for keyword in desc_keywords):
            return False

    return True  # All checks passed
```

**What happens:**
- **Title Match:** Check if job title contains search keywords
- **Company Match:** Filter by company name if specified
- **Location Match:** Ensure job location matches (or is remote)
- **Description Match:** Check if description contains required keywords
- Return `True` only if all criteria met

---

## Step 7: Save to Database

**File:** `backend/scraper/indeed_scraper/pipelines.py`

```python
from app.services.database_service import save_job, job_exists

class DatabasePipeline:
    """
    Scrapy pipeline to save jobs to Supabase database
    """

    def process_item(self, item: JobItem, spider):
        """
        Called for each JobItem yielded by spider
        """
        user_id = item['user_id']
        job_url = item['url']

        # Check if job already exists for this user
        if job_exists(user_id, job_url):
            print(f"Job already exists, skipping: {item['title']}")
            return item

        try:
            # Save to Supabase
            job_id = save_job(
                user_id=user_id,
                title=item['title'],
                company_name=item['company_name'],
                location=item['location'],
                job_type=item['job_type'],
                salary=item['salary'],
                url=item['url'],
                description=item['description'],
                benefits=item.get('benefits', ''),
                priority=False
            )

            print(f"✓ Saved to database: ID {job_id}")

            # Send WebSocket update
            send_websocket_update(user_id, {
                'task_id': spider.task_id,
                'status': 'running',
                'jobs_found': spider.jobs_scraped,
                'latest_job': {
                    'title': item['title'],
                    'company': item['company_name']
                }
            })

        except Exception as e:
            print(f"Error saving job: {e}")

        return item
```

**What happens:**
1. **Duplicate Check:** Query database to see if job URL already exists
2. **Save Job:** Insert new job into Supabase `jobs` table
3. **Update Stats:** Increment user's job count
4. **Send Update:** Notify user via WebSocket of new job found

---

## Step 8: Spider Completion

**File:** `backend/scraper/indeed_scraper/spiders/indeed_spider.py`

```python
def closed(self, reason):
    """
    Called when spider finishes
    """
    print(f"Spider closed: {reason}")
    print(f"Total jobs scraped: {self.jobs_scraped}")
    print(f"Total pages visited: {self.page_count}")

    # Send final WebSocket update
    send_websocket_update(self.user_id, {
        'task_id': self.task_id,
        'status': 'completed',
        'jobs_found': self.jobs_scraped,
        'spider_finished': True
    })
```

**What happens:**
- Spider completes all requests
- Send final "completed" status to user
- Celery task finishes
- Frontend refreshes job list

---

## Complete Data Flow Example

### User searches for "Software Engineer" in "San Francisco"

```
1. Frontend → Backend
   POST /api/scrape
   {
     "title": "Software Engineer",
     "location": "San Francisco",
     "scrape_length": 150
   }

2. Backend → Redis
   Queue: run_scrape(user_id="abc123", preferences={...})

3. Celery Worker → Scrapy
   Initialize IndeedSpider with preferences

4. Scrapy → Indeed
   GET https://www.indeed.com/jobs?q=Software+Engineer&l=San+Francisco

5. Indeed → Scrapy
   Returns HTML with 15 job cards

6. Scrapy → Pipeline
   JobItem(title="Senior Software Engineer", company="Google", ...)
   JobItem(title="Software Developer", company="Meta", ...)
   ...

7. Pipeline → Supabase
   INSERT INTO jobs (user_id, title, company, ...) VALUES (...)

8. Pipeline → WebSocket
   {"status": "running", "jobs_found": 15}

9. WebSocket → Frontend
   Update UI: "15 jobs found"

10. Scrapy → Indeed
    Follow pagination: page=2

11. Repeat steps 5-10 until max_jobs reached

12. Spider → WebSocket
    {"status": "completed", "jobs_found": 150}

13. Frontend
    Refresh jobs list, show success message
```

---

## Performance Optimizations

### Concurrent Requests
```python
'CONCURRENT_REQUESTS': 16,
'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
```
- Scrapes multiple pages simultaneously
- Reduces total scrape time

### Playwright Page Pool
```python
'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
'PLAYWRIGHT_MAX_PAGES_PER_CONTEXT': 4,
```
- Reuses browser instances
- Avoids repeated browser launches

### Database Deduplication
```python
def job_exists(user_id: str, job_url: str) -> bool:
    """Check if job URL already exists for user"""
    result = supabase.table('jobs').select('id').eq('user_id', user_id).eq('url', job_url).execute()
    return len(result.data) > 0
```
- Prevents duplicate job entries
- Faster than database constraints

---

## Error Handling

### Network Errors
```python
try:
    await page.wait_for_selector('.job_seen_beacon', timeout=10000)
except TimeoutError:
    print("Timeout waiting for job cards")
    await page.close()
    return
```

### Database Errors
```python
try:
    save_job(...)
except Exception as e:
    print(f"Database error: {e}")
    # Continue scraping, don't crash entire spider
```

### Spider Failures
```python
send_websocket_update(user_id, {
    'task_id': task_id,
    'status': 'failed',
    'error_message': str(e)
})
```

---

## Summary

### Authentication Flow
1. **Frontend** → Sign in with Supabase → Receive JWT token
2. **Frontend** → Send API request with `Authorization: Bearer {token}`
3. **Backend** → Verify JWT using JWKS public keys
4. **Backend** → Extract user_id from token payload
5. **Backend** → Execute request with user_id

### Scraping Flow
1. **Frontend** → POST /api/scrape
2. **Backend** → Queue task in Redis via Celery
3. **Celery** → Pick task and run spider
4. **Spider** → Scrape Indeed, match preferences
5. **Pipeline** → Save jobs to database
6. **WebSocket** → Real-time updates to frontend

### Scraper Pipeline
1. **Initialize** spider with user preferences
2. **Generate** Indeed search URL
3. **Parse** job cards from each page
4. **Match** against user criteria
5. **Save** to Supabase database
6. **Update** user via WebSocket
7. **Paginate** until max jobs reached

---

## File Reference

### Authentication
- `frontend/masa/src/app/sign-in/page.tsx` - User login
- `frontend/masa/src/app/page.tsx` - Auth state management
- `backend/app/core/auth.py` - JWT verification
- `backend/app/api/routers/*.py` - Protected endpoints

### Scraping
- `backend/app/api/routers/scrape.py` - Scrape endpoint
- `worker/celery_app.py` - Celery task queue
- `backend/scraper/scraper_service.py` - Scrapy initialization
- `backend/scraper/indeed_scraper/spiders/indeed_spider.py` - Spider logic
- `backend/scraper/indeed_scraper/pipelines.py` - Database saving
- `backend/app/core/websocket_manager.py` - Real-time updates

---

**Last Updated:** 2026-01-04