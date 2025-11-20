# Backend Deployment Guide (Koyeb)

This guide walks you through deploying the AskRacha RAG API backend on Koyeb.

## Prerequisites

- Koyeb account
- GitHub repository with the code
- Gemini API key
- Qdrant deployed on Koyeb (see [Qdrant Deployment Guide](./qdrant-deployment.md))

## Step 1: Deploy Qdrant

Before deploying the backend, ensure Qdrant is deployed on Koyeb.

See the **[Qdrant Deployment Guide](./qdrant-deployment.md)** for detailed instructions.

You'll need:
- Qdrant service URL (e.g., `https://askracha-qdrant-yourorg.koyeb.app`)
- API key (if you enabled authentication)

## Step 2: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Save it securely

## Step 3: Deploy Backend on Koyeb

### Option A: Deploy via Koyeb Dashboard

1. **Login to Koyeb**
   - Go to [app.koyeb.com](https://app.koyeb.com)
   - Sign in to your account

2. **Create New Service**
   - Click "Create Service"
   - Select "GitHub" as the source

3. **Connect GitHub Repository**
   - Authorize Koyeb to access your GitHub
   - Select your repository: `ask-racha`
   - Select branch: `main` (or your deployment branch)

4. **Configure Build Settings**
   - **Builder**: Docker
   - **Dockerfile path**: `askracha/backend/Dockerfile`
   - **Build context**: `askracha/backend`

5. **Configure Service Settings**
   - **Service name**: `askracha-backend` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Instance type**: 
     - Start with: `nano` (512MB RAM, 0.1 vCPU)
     - Upgrade to `micro` or `small` if needed

6. **Configure Ports**
   - **Port**: `5000`
   - **Protocol**: HTTP
   - **Public exposure**: Enable

7. **Set Environment Variables**

   Click "Add Environment Variable" for each:

   ```
   QDRANT_URL=https://askracha-qdrant-yourorg.koyeb.app
   FLASK_ENV=production
   GEMINI_API_KEY=your_api_key
   ALLOWED_ORGINS=http://localhost:3000,any_other_allowed_origin
   REDIS_HOST=redis
   REDIS_PORT=6379
   RATE_LIMIT_SECONDS=5
   ```

   **Optional** (if you enabled Qdrant authentication):
   ```
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

8. **Configure Health Check**
   - **Path**: `/api/health`
   - **Port**: `5000`
   - **Protocol**: HTTP
   - **Grace period**: 90 seconds (initial startup takes time)
   - **Interval**: 30 seconds
   - **Timeout**: 10 seconds
   - **Retries**: 3

9. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (5-10 minutes for first deployment)

### Option B: Deploy via Koyeb CLI

1. **Install Koyeb CLI**
   ```bash
   # macOS
   brew install koyeb/tap/koyeb-cli
   
   # Linux
   curl -fsSL https://cli.koyeb.com/install.sh | sh
   ```

2. **Login**
   ```bash
   koyeb login
   ```

3. **Create Service**
   ```bash
   koyeb service create askracha-backend \
     --git github.com/YOUR_USERNAME/MM-ask-racha \
     --git-branch main \
     --git-build-command "docker build -f askracha/backend/Dockerfile askracha/backend" \
     --ports 5000:http \
     --routes /:5000 \
     --env GEMINI_API_KEY=your_key \
     --env QDRANT_URL=https://askracha-qdrant-yourorg.koyeb.app \
     --env FLASK_ENV=production \
     --instance-type nano \
     --regions fra
   
   # Add QDRANT_API_KEY only if you enabled authentication:
   # --env QDRANT_API_KEY=your_key \
   ```

## Step 4: Verify Deployment

1. **Check Service Status**
   - In Koyeb dashboard, wait for status to show "Healthy"
   - Check logs for any errors

2. **Get Service URL**
   - Copy the public URL (e.g., `https://your-service.koyeb.app`)

3. **Test Health Endpoint**
   ```bash
   curl https://your-service.koyeb.app/api/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2025-10-20T08:00:00.000000",
     "service": "AskRacha RAG API",
     "version": "2.0"
   }
   ```

4. **Test Query Endpoint**
   ```bash
   curl -X POST https://your-service.koyeb.app/api/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What is Storacha?"}'
   ```

## Step 5: Monitor and Maintain

### View Logs
```bash
# Via CLI
koyeb service logs askracha-backend --follow

# Via Dashboard
Go to Service → Logs tab
```

### Check Metrics
- CPU usage
- Memory usage
- Request count
- Response times

### Update Deployment
When you push changes to GitHub:
1. Koyeb automatically detects changes
2. Builds new Docker image
3. Deploys with zero downtime

## Configuration Details

### Dockerfile Location
```
askracha/backend/Dockerfile
```

### Key Files
- `askracha/backend/app.py` - Main Flask application
- `askracha/backend/rag.py` - RAG system implementation
- `askracha/backend/requirements.txt` - Python dependencies

### Resource Requirements

| Instance Type | RAM    | vCPU | Recommended For |
|--------------|--------|------|-----------------|
| nano         | 512MB  | 0.1  | Testing         |
| micro        | 1GB    | 0.5  | Light usage     |
| small        | 2GB    | 1.0  | Production      |

## Troubleshooting

### Service Won't Start

**Check logs for:**
- Missing environment variables
- Qdrant connection issues
- Gemini API key issues

**Solution:**
```bash
# View logs
koyeb service logs askracha-backend --tail 100

# Verify environment variables
koyeb service get askracha-backend
```

### Health Check Failing

**Increase grace period:**
- Backend needs time to load documents on startup
- Set grace period to 90-120 seconds

### Out of Memory

**Upgrade instance:**
```bash
koyeb service update askracha-backend --instance-type micro
```

### Qdrant Connection Failed

**Verify:**
1. Qdrant service is running on Koyeb
2. Qdrant URL is correct (include `https://`)
3. API key is valid (if using authentication)
4. Both services are in the same region (recommended)

**Test Qdrant:**
```bash
curl https://askracha-qdrant-yourorg.koyeb.app/
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key | `AIza...` |
| `QDRANT_URL` | Yes | Qdrant service URL on Koyeb | `https://askracha-qdrant-yourorg.koyeb.app` |
| `QDRANT_API_KEY` | No | Qdrant API key (if auth enabled) | `abc123...` |
| `FLASK_ENV` | No | Flask environment | `production` |

## Next Steps

After backend is deployed:
1. Save the backend URL
2. Proceed to [Bot Deployment](./bot-deployment.md)
3. Use the backend URL in bot configuration
