# Qdrant Deployment Guide (Koyeb)

This guide walks you through deploying Qdrant vector database on Koyeb.

## Overview

Qdrant is the vector database used by AskRacha to store and search document embeddings. We deploy our own instance on Koyeb for full control and cost optimization.

## Prerequisites

- Koyeb account
- Basic understanding of vector databases

## Step 1: Deploy Qdrant on Koyeb

### Option A: Deploy via Koyeb Dashboard

1. **Login to Koyeb**
   - Go to [app.koyeb.com](https://app.koyeb.com)
   - Sign in to your account

2. **Create New Service**
   - Click "Create Service"
   - Select "Docker Hub" as the source

3. **Configure Docker Image**
   - **Image**: `qdrant/qdrant:latest`
   - **Tag**: `latest` (or specific version like `v1.7.4`)

4. **Configure Service Settings**
   - **Service name**: `askracha-qdrant`
   - **Region**: Choose same region as backend for lower latency
   - **Instance type**: 
     - Start with: `small` (2GB RAM, 1 vCPU) - Recommended minimum
     - Scale up to `medium` for production with large datasets

5. **Configure Ports**
   - **Port**: `6333`
   - **Protocol**: HTTP
   - **Public exposure**: Enable (for backend to access)

6. **Configure Persistent Storage**
   - **Enable Persistent Volume**: Yes
   - **Mount path**: `/qdrant/storage`
   - **Size**: Start with 10GB (scale as needed)
   - **Important**: This ensures data persists across restarts

7. **Set Environment Variables** (Optional)
   
   For basic setup, no environment variables are required. For advanced configuration:

   ```
   QDRANT__SERVICE__HTTP_PORT=6333
   QDRANT__SERVICE__GRPC_PORT=6334
   ```

8. **Configure Health Check**
   - **Path**: `/` or `/health`
   - **Port**: `6333`
   - **Protocol**: HTTP
   - **Grace period**: 30 seconds
   - **Interval**: 30 seconds
   - **Timeout**: 10 seconds
   - **Retries**: 3

9. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (2-3 minutes)

### Option B: Deploy via Koyeb CLI

```bash
# Create Qdrant service with persistent storage
koyeb service create askracha-qdrant \
  --docker qdrant/qdrant:latest \
  --ports 6333:http \
  --routes /:6333 \
  --instance-type small \
  --regions fra \
  --volumes qdrant-storage:/qdrant/storage:10
```

## Step 2: Verify Deployment

1. **Check Service Status**
   - In Koyeb dashboard, wait for status to show "Healthy"
   - Check logs for successful startup

2. **Get Service URL**
   - Copy the public URL (e.g., `https://askracha-qdrant-yourorg.koyeb.app`)

3. **Test Qdrant API**
   ```bash
   # Test health endpoint
   curl https://askracha-qdrant-yourorg.koyeb.app/
   
   # Expected response:
   # {"title":"qdrant - vector search engine","version":"1.x.x"}
   ```

4. **List Collections**
   ```bash
   curl https://askracha-qdrant-yourorg.koyeb.app/collections
   
   # Expected response (empty initially):
   # {"result":{"collections":[]},"status":"ok","time":0.000123}
   ```

## Step 3: Configure Backend to Use Qdrant

Update your backend environment variables in Koyeb:

```bash
# Set Qdrant URL
koyeb service update askracha-backend \
  --env QDRANT_URL=https://askracha-qdrant-yourorg.koyeb.app
```

**Note**: Since this is your own Qdrant instance, you don't need an API key unless you configure authentication (see Security section below).

## Configuration Details

### Resource Requirements

| Instance Type | RAM  | vCPU | Storage | Recommended For |
|--------------|------|------|---------|-----------------|
| small        | 2GB  | 1.0  | 10GB    | Development     |
| medium       | 4GB  | 2.0  | 20GB    | Small production|
| large        | 8GB  | 4.0  | 50GB    | Large production|

### Storage Sizing

Estimate storage needs:
- **Small dataset** (< 10k documents): 5-10GB
- **Medium dataset** (10k-100k documents): 10-50GB
- **Large dataset** (> 100k documents): 50GB+

Monitor usage and scale as needed.

### Port Configuration

- **6333**: HTTP API (required)
- **6334**: gRPC API (optional, for high-performance clients)

## Security (Optional but Recommended)

### Enable API Key Authentication

1. **Generate API Key**
   ```bash
   # Generate a secure random key
   openssl rand -base64 32
   ```

2. **Update Qdrant Service**
   ```bash
   koyeb service update askracha-qdrant \
     --env QDRANT__SERVICE__API_KEY=your_generated_key
   ```

3. **Update Backend Service**
   ```bash
   koyeb service update askracha-backend \
     --env QDRANT_API_KEY=your_generated_key
   ```

4. **Test with API Key**
   ```bash
   curl https://askracha-qdrant-yourorg.koyeb.app/collections \
     -H "api-key: your_generated_key"
   ```

### Network Security

Since Koyeb services are publicly accessible by default:
- **Enable API key authentication** (recommended)
- **Use HTTPS** (automatic with Koyeb)
- **Monitor access logs** regularly

## Monitoring and Maintenance

### View Logs
```bash
# Via CLI
koyeb service logs askracha-qdrant --follow

# Via Dashboard
Go to Service → Logs tab
```

### Check Metrics
Monitor in Koyeb dashboard:
- CPU usage
- Memory usage
- Storage usage
- Request count

### Backup Data

Qdrant data is stored in persistent volume, but consider regular backups:

1. **Create Snapshot**
   ```bash
   curl -X POST https://askracha-qdrant-yourorg.koyeb.app/collections/askracha_docs/snapshots
   ```

2. **List Snapshots**
   ```bash
   curl https://askracha-qdrant-yourorg.koyeb.app/collections/askracha_docs/snapshots
   ```

3. **Download Snapshot**
   ```bash
   curl https://askracha-qdrant-yourorg.koyeb.app/collections/askracha_docs/snapshots/snapshot_name \
     -o backup.snapshot
   ```

### Scale Storage

If you run out of space:
```bash
# Increase volume size (via Koyeb dashboard)
# Service → Settings → Volumes → Edit → Increase size
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
koyeb service logs askracha-qdrant --tail 50
```

**Common issues:**
- Insufficient memory (upgrade to larger instance)
- Port conflicts (verify port 6333 is configured)
- Volume mount issues (check persistent volume settings)

### Out of Memory

**Symptoms:**
- Service crashes
- OOMKilled in logs

**Solution:**
```bash
# Upgrade instance type
koyeb service update askracha-qdrant --instance-type medium
```

### Storage Full

**Check storage usage:**
```bash
curl https://askracha-qdrant-yourorg.koyeb.app/collections/askracha_docs
```

**Solution:**
- Increase volume size in Koyeb dashboard
- Delete old collections if not needed
- Optimize vector dimensions

### Backend Can't Connect

**Verify:**
1. Qdrant service is running and healthy
2. Backend has correct `QDRANT_URL`
3. API key is set correctly (if using authentication)

**Test connection:**
```bash
# From your local machine
curl https://askracha-qdrant-yourorg.koyeb.app/collections
```

### Slow Queries

**Optimize:**
1. Upgrade instance type for more CPU/RAM
2. Reduce `similarity_top_k` in backend
3. Use HNSW index optimization
4. Consider using gRPC instead of HTTP

## Advanced Configuration

### Enable gRPC

```bash
koyeb service update askracha-qdrant \
  --ports 6333:http,6334:http \
  --env QDRANT__SERVICE__GRPC_PORT=6334
```

### Configure HNSW Index

Optimize for your use case via collection configuration in backend code:

```python
# In backend/storage/vector_store.py
client.create_collection(
    collection_name="askracha_docs",
    vectors_config={
        "size": 768,
        "distance": "Cosine"
    },
    hnsw_config={
        "m": 16,  # Number of edges per node
        "ef_construct": 100  # Construction time/accuracy tradeoff
    }
)
```

### Enable Telemetry (Optional)

```bash
koyeb service update askracha-qdrant \
  --env QDRANT__TELEMETRY_DISABLED=false
```

## Cost Optimization

### Tips to Reduce Costs

1. **Right-size instance**: Start small, scale as needed
2. **Optimize storage**: Delete unused collections
3. **Use efficient embeddings**: Smaller dimensions = less storage
4. **Monitor usage**: Check metrics regularly

### Estimated Costs

| Instance | Storage | Monthly Cost |
|----------|---------|--------------|
| small    | 10GB    | ~$15-20     |
| medium   | 20GB    | ~$30-40     |
| large    | 50GB    | ~$60-80     |

*Prices are approximate. Check Koyeb pricing for exact costs.*

## Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `QDRANT__SERVICE__HTTP_PORT` | No | HTTP API port | `6333` |
| `QDRANT__SERVICE__GRPC_PORT` | No | gRPC API port | `6334` |
| `QDRANT__SERVICE__API_KEY` | No | API key for authentication | None |
| `QDRANT__TELEMETRY_DISABLED` | No | Disable telemetry | `true` |

## Next Steps

After Qdrant is deployed:
1. Save the Qdrant URL
2. Proceed to [Backend Deployment](./backend-deployment.md)
3. Use the Qdrant URL in backend configuration
4. Monitor storage usage as data grows
