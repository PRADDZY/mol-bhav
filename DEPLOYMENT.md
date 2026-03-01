# Deploying Mol-Bhav to Render

This guide walks you through deploying the complete Mol-Bhav stack to [Render](https://render.com/).

## Prerequisites

1. **Render Account** — Free tier available at [render.com](https://render.com/)
2. **GitHub Repository** — Code pushed to [github.com/PRADDZY/mol-bhav](https://github.com/PRADDZY/mol-bhav)
3. **NVIDIA NIM API Key** — Get free key at [build.nvidia.com](https://build.nvidia.com/)

## Deployment Options

### Option 1: Blueprint Deploy (Recommended)

The `render.yaml` blueprint automatically provisions all services (API, MongoDB, Redis).

1. **Connect Repository**
   - Go to [render.com/dashboard](https://dashboard.render.com/)
   - Click **New** → **Blueprint**
   - Connect your GitHub account (if not already)
   - Select `PRADDZY/mol-bhav` repository

2. **Configure Environment**
   - Render will detect `render.yaml`
   - Set required secret: `NIM_API_KEY` (your NVIDIA NIM key)
   - Render auto-generates: `API_ADMIN_KEY`, MongoDB password
   - Review and confirm

3. **Deploy**
   - Click **Apply**
   - Render will:
     - Create MongoDB private service
     - Create Redis instance
     - Build and deploy FastAPI backend
     - Link all services via internal networking

4. **Seed Data**
   - Once deployed, open **Shell** for `mol-bhav-api` service
   - Run: `python -m scripts.seed`

5. **Access**
   - API: `https://mol-bhav-api.onrender.com`
   - Swagger: `https://mol-bhav-api.onrender.com/docs` (disabled if `ENV=production`)
   - Health: `https://mol-bhav-api.onrender.com/health`

### Option 2: Manual Service Creation

If you prefer manual control:

#### 1. Create MongoDB Service

- **New** → **Private Service**
- **Runtime:** Docker
- **Repository:** `https://github.com/PRADDZY/mol-bhav`
- **Dockerfile Path:** `./Dockerfile.mongo`
- **Plan:** Free (1 GB disk)
- **Environment Variables:**
  - `MONGO_INITDB_ROOT_USERNAME=molbhav`
  - `MONGO_INITDB_ROOT_PASSWORD=<strong-password>`
- **Disk:** Mount `/data/db` (1 GB)

Note the internal connection string (e.g., `mongodb://molbhav:<password>@mol-bhav-db:27017`)

#### 2. Create Redis Service

- **New** → **Redis**
- **Name:** `mol-bhav-redis`
- **Plan:** Free (25 MB)
- **Maxmemory Policy:** `allkeys-lru`

Note the internal connection string (e.g., `redis://:password@mol-bhav-redis:6379`)

#### 3. Create FastAPI Backend

- **New** → **Web Service**
- **Runtime:** Python 3
- **Repository:** `https://github.com/PRADDZY/mol-bhav`
- **Build Command:** `pip install -e .`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan:** Free
- **Environment Variables:**
  ```
  PYTHON_VERSION=3.11.0
  NIM_API_KEY=nvapi-...
  NIM_BASE_URL=https://integrate.api.nvidia.com/v1
  NIM_MODEL=z-ai/glm4_7
  MONGODB_URL=<from-step-1>
  MONGODB_DB_NAME=mol_bhav
  REDIS_URL=<from-step-2>
  DEFAULT_BETA=5.0
  DEFAULT_ALPHA=0.6
  DEFAULT_MAX_ROUNDS=15
  DEFAULT_SESSION_TTL_SECONDS=300
  MIN_RESPONSE_DELAY_MS=2000
  ENV=production
  API_ADMIN_KEY=<generate-strong-key>
  CORS_ALLOWED_ORIGINS=["https://mol-bhav.onrender.com"]
  ```
- **Health Check Path:** `/health`

#### 4. Seed Data

- Open **Shell** tab for `mol-bhav-api`
- Run: `python -m scripts.seed`

## Frontend Deployment

**Recommended:** Deploy frontend to Vercel/Netlify for better performance.

### Vercel Deployment

```bash
cd frontend
vercel --prod
```

Set environment variable:
```
NEXT_PUBLIC_API_URL=https://mol-bhav-api.onrender.com
```

### Render Frontend (Alternative)

If deploying to Render:

1. **New** → **Web Service**
2. **Runtime:** Node
3. **Root Directory:** `frontend`
4. **Build Command:** `npm install && npm run build`
5. **Start Command:** `npm start`
6. **Environment:**
   - `NEXT_PUBLIC_API_URL=https://mol-bhav-api.onrender.com`

Then update backend `CORS_ALLOWED_ORIGINS` to include frontend URL.

## Post-Deployment

### 1. Update CORS

If frontend is on different domain:

```bash
# In Render dashboard → mol-bhav-api → Environment
CORS_ALLOWED_ORIGINS=["https://mol-bhav.onrender.com","https://your-frontend.vercel.app"]
```

### 2. Test API

```bash
# Health check
curl https://mol-bhav-api.onrender.com/health

# List products
curl https://mol-bhav-api.onrender.com/api/v1/products

# Start negotiation
curl -X POST https://mol-bhav-api.onrender.com/api/v1/negotiate/start \
  -H "Content-Type: application/json" \
  -d '{"product_id":"phone-001","buyer_name":"Test"}'
```

### 3. Monitor Logs

- Render Dashboard → Service → **Logs** tab
- JSON-formatted logs with `X-Request-ID` tracing

### 4. Scale (Optional)

Free tier limitations:
- **Backend:** Spins down after 15 mins inactivity (750 hrs/month free)
- **MongoDB:** 1 GB disk
- **Redis:** 25 MB memory

Upgrade to paid plans for:
- No spin-down
- More disk/memory
- Multiple regions
- Custom domains

## Troubleshooting

### Service Won't Start

**Check logs for:**
- Missing `NIM_API_KEY` — set in Environment Variables
- MongoDB connection failed — verify `MONGODB_URL` internal address
- Redis connection failed — verify `REDIS_URL` internal address

### Database Connection Errors

Render services use **internal hostnames** (e.g., `mol-bhav-db:27017`), not `localhost`.

Fix:
```
MONGODB_URL=mongodb://molbhav:password@mol-bhav-db:27017
REDIS_URL=redis://:password@mol-bhav-redis:6379
```

### CORS Errors

Add frontend domain to `CORS_ALLOWED_ORIGINS`:
```json
["https://mol-bhav-api.onrender.com","https://your-frontend.vercel.app"]
```

### Free Tier Spin-Down

First request after spin-down takes ~30s. Solutions:
- Upgrade to paid plan (no spin-down)
- Use cron job to ping `/health` every 10 mins
- Add loading state in frontend

## Cost Estimate

**Free Tier:**
- Backend: Free (750 hrs/month)
- MongoDB: Free (1 GB)
- Redis: Free (25 MB)
- **Total: $0/month**

**Production Tier:**
- Backend Starter: $7/month (always-on, 0.5 GB RAM)
- MongoDB: $7/month (1 GB disk, always-on)
- Redis Starter: $10/month (100 MB)
- **Total: ~$24/month**

## Security Checklist

- [x] `ENV=production` set (disables Swagger docs)
- [x] Strong `API_ADMIN_KEY` generated
- [x] Strong MongoDB password generated
- [x] CORS restricted to frontend domains only
- [ ] Enable Render's built-in DDoS protection
- [ ] Set up custom domain with HTTPS (auto via Let's Encrypt)
- [ ] Configure log retention (paid plans)

## Next Steps

1. Set up monitoring (Render has built-in metrics)
2. Configure custom domain
3. Set up CI/CD via GitHub Actions (auto-deploy on push)
4. Add environment-specific configs (staging/prod)

## Support

- **Render Docs:** [render.com/docs](https://render.com/docs)
- **Mol-Bhav Issues:** [github.com/PRADDZY/mol-bhav/issues](https://github.com/PRADDZY/mol-bhav/issues)
