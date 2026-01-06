# JobFlow Backend Deployment Guide (Render)

This guide will help you deploy the JobFlow backend (FastAPI + Celery) to Render.

## Prerequisites

- GitHub repository with your backend code
- Upstash Redis instance (already configured)
- Supabase database (already configured)
- Render account (free tier works)

## Architecture

- **Web Service**: FastAPI API server
- **Background Worker**: Celery worker for scraping tasks
- **Redis**: Upstash (managed, already configured)
- **Database**: Supabase (managed, already configured)

## Deployment Options

### Option 1: Using render.yaml (Recommended)

The `render.yaml` file is included in the backend directory and will automatically create both services.

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your backend
   - Render will detect `render.yaml` automatically

3. **Set Environment Variables**

   Render will prompt you to set these environment variables for both services:

   ```bash
   # Frontend
   ALLOWED_ORIGINS=https://jobflow-ten.vercel.app

   # Upstash Redis
   UPSTASH_REDIS_REST_URL=https://premium-termite-25457.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your_actual_token
   UPSTASH_REDIS_PORT=6379

   # Supabase
   SUPABASE_URL=https://inbplkdyaohzgjvyiksm.supabase.co
   SUPABASE_KEY=your_actual_key
   ```

4. **Deploy**
   - Click "Apply" to create both services
   - Render will build and deploy automatically

### Option 2: Manual Setup via Dashboard

If you prefer to create services manually:

#### A. Create Web Service (API)

1. Go to Render Dashboard → "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `jobflow-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend` (if backend is in a subdirectory)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `fastapi run app/main.py --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Add Environment Variables (same as above)
5. Click "Create Web Service"

#### B. Create Background Worker (Celery)

1. Go to Render Dashboard → "New +" → "Background Worker"
2. Connect same GitHub repository
3. Configure:
   - **Name**: `jobflow-celery-worker`
   - **Region**: Same as API
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A worker.celery_app worker --loglevel=info --concurrency=1`
   - **Plan**: Free
4. Add Environment Variables (same as API, except ALLOWED_ORIGINS not needed)
5. Click "Create Background Worker"

## Health Check

Once deployed, verify the API is working:

```bash
curl https://your-api-url.onrender.com/health
```

Expected response:
```json
{"status": "healthy"}
```

## Important Notes

### Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30-60 seconds
- 750 hours/month free compute (shared across services)

### Celery Worker Configuration

- `--concurrency=1`: Optimized for free tier (limited CPU/memory)
- Worker will process scraping tasks sequentially
- Adjust concurrency if you upgrade to paid plan

### Environment Variables

- Never commit `.env` file to git
- Use Render's environment variable dashboard to manage secrets
- Variables are encrypted at rest

### Auto-Deploy

Render automatically deploys when you push to the connected branch:
```bash
git push origin main  # Triggers automatic deployment
```

## Monitoring

- **Logs**: Available in Render dashboard for each service
- **Metrics**: View CPU, memory, and request metrics
- **Alerts**: Set up email notifications for service failures

## Troubleshooting

### Service Won't Start

1. Check logs in Render dashboard
2. Verify all environment variables are set
3. Check that dependencies in `requirements.txt` are compatible
4. Ensure Python version matches (3.14)

### Redis Connection Errors

1. Verify Upstash credentials in environment variables
2. Check that `UPSTASH_REDIS_PORT` is set to `6379`
3. Test connection from local environment first

### Celery Worker Not Processing Tasks

1. Check worker logs in Render dashboard
2. Verify Redis connection (worker uses same credentials as API)
3. Ensure both API and worker services are running

### CORS Errors

1. Check `ALLOWED_ORIGINS` includes your frontend URL
2. Format: `https://jobflow-ten.vercel.app` (no trailing slash)
3. For multiple origins: `http://localhost:3000,https://jobflow-ten.vercel.app`

## Updating Frontend URL

If your frontend URL changes:

1. Go to Render Dashboard → `jobflow-api` service
2. Click "Environment" tab
3. Update `ALLOWED_ORIGINS` variable
4. Service will automatically redeploy

## Cost Optimization

- Free tier should be sufficient for development/testing
- Monitor usage in Render dashboard
- Consider upgrading if you need:
  - Zero-downtime (no spin-down)
  - More concurrent requests
  - Faster builds
  - More compute resources

## Next Steps

After deployment:

1. Update your frontend to point to the Render API URL
2. Test scraping functionality end-to-end
3. Monitor logs for any errors
4. Set up health check monitoring (optional)

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com/
