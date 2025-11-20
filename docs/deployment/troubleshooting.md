# Troubleshooting Guide

Common issues and solutions for AskRacha deployment on Koyeb.

## Table of Contents

- [Backend Issues](#backend-issues)
- [Bot Issues](#bot-issues)
- [Integration Issues](#integration-issues)
- [Performance Issues](#performance-issues)
- [Debugging Tips](#debugging-tips)

---

## Backend Issues

### Issue: Backend Service Won't Start

**Symptoms:**
- Service status shows "Unhealthy" or "Error"
- Health checks failing
- Service keeps restarting

**Possible Causes & Solutions:**

#### 1. Missing Environment Variables
```bash
# Check logs
koyeb service logs askracha-backend --tail 50

# Look for: "GEMINI_API_KEY not found" or similar
```

**Solution:**
```bash
# Set missing variables
koyeb service update askracha-backend \
  --env GEMINI_API_KEY=your_key \
  --env QDRANT_URL=your_url \
  --env QDRANT_API_KEY=your_key
```

#### 2. Qdrant Connection Failed
```bash
# Error in logs: "Failed to connect to Qdrant"
```

**Solution:**
- Verify Qdrant service is running on Koyeb
- Check Qdrant URL includes `https://`
- Verify API key is correct (if authentication enabled)
- Ensure both services are in the same region (recommended)
- Test connection manually:
```bash
# Without authentication
curl https://askracha-qdrant-yourorg.koyeb.app/collections

# With authentication
curl https://askracha-qdrant-yourorg.koyeb.app/collections \
  -H "api-key: your_api_key"
```

#### 3. Invalid Gemini API Key
```bash
# Error in logs: "Invalid API key" or "Authentication failed"
```

**Solution:**
- Regenerate API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
- Update in Koyeb dashboard
- Redeploy service

#### 4. Out of Memory
```bash
# Error in logs: "Killed" or "OOMKilled"
```

**Solution:**
```bash
# Upgrade instance type
koyeb service update askracha-backend --instance-type micro
```

### Issue: Health Check Failing

**Symptoms:**
- Service shows "Unhealthy"
- `/api/health` endpoint not responding

**Solutions:**

#### 1. Increase Grace Period
- Backend needs time to load documents on startup
- Set grace period to 90-120 seconds in Koyeb dashboard

#### 2. Check Port Configuration
- Verify port `5000` is exposed
- Check health check path is `/api/health`

#### 3. Check Logs
```bash
koyeb service logs askracha-backend --follow
```

### Issue: API Returns 400 "No question provided"

**Symptoms:**
- Bot can't get responses
- Direct API calls fail with validation error

**Solution:**
- Ensure request uses `"question"` parameter, not `"query"`
```bash
# Correct format
curl -X POST https://your-backend.koyeb.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here"}'
```

### Issue: Slow Response Times

**Symptoms:**
- API takes >30 seconds to respond
- Timeout errors

**Solutions:**

#### 1. Check Vector Store
```bash
# Get stats
curl https://your-backend.koyeb.app/api/vector-store/stats
```

#### 2. Optimize Query Engine
- Reduce `similarity_top_k` in `rag.py`
- Use faster response mode

#### 3. Upgrade Instance
```bash
koyeb service update askracha-backend --instance-type small
```

---

## Bot Issues

### Issue: Bot Shows Offline in Discord

**Symptoms:**
- Bot appears offline in Discord
- No response to mentions

**Possible Causes & Solutions:**

#### 1. Service Not Running
```bash
# Check service status
koyeb service get askracha-bot

# Check logs
koyeb service logs askracha-bot --tail 50
```

**Solution:**
- If crashed, check logs for errors
- Redeploy if needed

#### 2. Invalid Discord Token
```bash
# Error in logs: "Improper token" or "401 Unauthorized"
```

**Solution:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Navigate to your app → Bot
3. Click "Reset Token"
4. Copy new token
5. Update in Koyeb:
```bash
koyeb service update askracha-bot --env DISCORD_TOKEN=new_token
```

#### 3. Missing Intents
```bash
# Error in logs: "Privileged intent provided is not enabled"
```

**Solution:**
1. Go to Discord Developer Portal → Your App → Bot
2. Enable "Message Content Intent"
3. Enable "Server Members Intent" (if needed)
4. Save changes
5. Restart bot service

### Issue: Bot Not Responding to Messages

**Symptoms:**
- Bot is online but doesn't respond
- No errors in logs

**Solutions:**

#### 1. Check Permissions
- Bot needs "Read Messages" permission
- Bot needs "Send Messages" permission
- Check channel-specific permissions

#### 2. Verify Message Content Intent
- Must be enabled in Discord Developer Portal
- Bot → Privileged Gateway Intents → Message Content Intent

#### 3. Check Backend Connection
```bash
# Test backend from bot
curl -X POST https://your-backend.koyeb.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

#### 4. Check Logs for Errors
```bash
koyeb service logs askracha-bot --follow

# Look for:
# - "Processing question from..."
# - API errors
# - Rate limit messages
```

### Issue: Bot Responds with Error Message

**Symptoms:**
- Bot replies with "Sorry, I encountered an error..."
- API errors in logs

**Solutions:**

#### 1. Backend API Down
```bash
# Check backend status
curl https://your-backend.koyeb.app/api/health
```

**Solution:**
- Check backend service status
- Review backend logs
- Verify backend environment variables

#### 2. API Timeout
```bash
# Error in logs: "Request timed out"
```

**Solution:**
```bash
# Increase timeout
koyeb service update askracha-bot --env API_TIMEOUT=60
```

#### 3. Rate Limited by Backend
```bash
# Error in logs: "Rate limit exceeded"
```

**Solution:**
- Wait for rate limit to reset
- Check rate limit configuration
- Consider upgrading backend instance

### Issue: Rate Limiting Not Working

**Symptoms:**
- Users can spam questions
- No rate limit messages

**Solutions:**

#### 1. Redis Not Connected (if using Redis)
```bash
# Check logs for Redis connection errors
koyeb service logs askracha-bot | grep -i redis
```

**Solution:**
- Verify `REDIS_URL` is correct
- Test Redis connection:
```bash
redis-cli -u redis://your-redis-url ping
```

#### 2. In-Memory Rate Limiting (without Redis)
- Rate limits reset on bot restart
- This is expected behavior without Redis

**Solution:**
- Use external Redis service (Upstash, Redis Labs)
- Set `REDIS_URL` environment variable

---

## Qdrant Issues

### Issue: Qdrant Service Won't Start

**Symptoms:**
- Qdrant service shows "Unhealthy" or "Error"
- Backend can't connect to Qdrant

**Solutions:**

#### 1. Insufficient Memory
```bash
# Check logs
koyeb service logs askracha-qdrant --tail 50
```

**Solution:**
```bash
# Upgrade to at least 'small' instance (2GB RAM)
koyeb service update askracha-qdrant --instance-type small
```

#### 2. Persistent Volume Not Mounted
**Solution:**
- Check volume configuration in Koyeb dashboard
- Ensure mount path is `/qdrant/storage`
- Verify volume size is sufficient

### Issue: Qdrant Storage Full

**Symptoms:**
- Write operations fail
- "No space left on device" errors

**Solution:**
```bash
# Check current storage usage via API
curl https://askracha-qdrant-yourorg.koyeb.app/collections/askracha_docs

# Increase volume size in Koyeb dashboard:
# Service → Settings → Volumes → Edit → Increase size
```

### Issue: Qdrant Performance Slow

**Symptoms:**
- Slow query responses
- Backend timeouts

**Solutions:**

#### 1. Upgrade Instance
```bash
koyeb service update askracha-qdrant --instance-type medium
```

#### 2. Optimize Collection Settings
- Reduce vector dimensions in backend code
- Adjust HNSW parameters
- Use gRPC instead of HTTP for better performance

### Issue: Data Loss After Restart

**Symptoms:**
- Collections disappear after restart
- Need to reload documents

**Solution:**
- Ensure persistent volume is properly configured
- Check volume mount path: `/qdrant/storage`
- Verify volume is not ephemeral

---

## Integration Issues

### Issue: Bot Can't Reach Backend

**Symptoms:**
- Connection refused errors
- Timeout errors
- 404 Not Found

**Solutions:**

#### 1. Verify Backend URL
```bash
# Check bot configuration
koyeb service get askracha-bot

# Verify API_URL is correct
# Should be: https://your-backend.koyeb.app (no trailing slash)
```

#### 2. Test Backend Accessibility
```bash
# From your local machine
curl https://your-backend.koyeb.app/api/health

# Should return:
# {"status": "healthy", ...}
```

#### 3. Check Network/Firewall
- Ensure backend service is publicly accessible
- Check Koyeb service exposure settings

### Issue: CORS Errors (if using web frontend)

**Symptoms:**
- Browser console shows CORS errors
- Requests blocked by browser

**Solution:**
- Backend already has CORS enabled for all origins
- If issues persist, check backend logs
- Verify request headers

---

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- Service restarts frequently
- OOMKilled in logs
- Slow performance

**Solutions:**

#### 1. Monitor Memory
```bash
# Check metrics in Koyeb dashboard
# Service → Metrics tab
```

#### 2. Upgrade Instance
```bash
# Backend
koyeb service update askracha-backend --instance-type micro

# Bot
koyeb service update askracha-bot --instance-type micro
```

#### 3. Optimize Code
- Reduce document chunk size
- Limit concurrent requests
- Clear unused cache

### Issue: High CPU Usage

**Symptoms:**
- Slow response times
- Service throttling

**Solutions:**

#### 1. Check Logs for Loops
```bash
koyeb service logs SERVICE_NAME --follow
```

#### 2. Upgrade vCPU
```bash
koyeb service update SERVICE_NAME --instance-type small
```

### Issue: Slow Document Loading

**Symptoms:**
- Backend takes >2 minutes to start
- Health checks timeout

**Solutions:**

#### 1. Reduce Default Documents
- Edit `backend/app.py`
- Reduce number of URLs in `default_urls`

#### 2. Increase Health Check Grace Period
- Set to 120 seconds in Koyeb dashboard

#### 3. Use Persistent Storage
- Documents are loaded on every restart
- Consider caching strategy

---

## Debugging Tips

### View Real-Time Logs

```bash
# Backend
koyeb service logs askracha-backend --follow

# Bot
koyeb service logs askracha-bot --follow
```

### Filter Logs

```bash
# Show only errors
koyeb service logs SERVICE_NAME | grep -i error

# Show only warnings
koyeb service logs SERVICE_NAME | grep -i warning

# Show specific module
koyeb service logs SERVICE_NAME | grep "api_client"
```

### Test API Endpoints

```bash
# Health check
curl https://your-backend.koyeb.app/api/health

# Status
curl https://your-backend.koyeb.app/api/status

# Query
curl -X POST https://your-backend.koyeb.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Storacha?"}'

# Vector store stats
curl https://your-backend.koyeb.app/api/vector-store/stats
```

### Check Service Configuration

```bash
# Get full service details
koyeb service get SERVICE_NAME

# Check environment variables
koyeb service get SERVICE_NAME | grep -A 20 "Environment"

# Check instance type
koyeb service get SERVICE_NAME | grep "instance_type"
```

### Enable Debug Logging

```bash
# Bot
koyeb service update askracha-bot --env LOG_LEVEL=DEBUG

# Check logs
koyeb service logs askracha-bot --follow
```

### Test Discord Bot Locally

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/MM-ask-racha.git
cd MM-ask-racha/askracha/bot

# Create .env file
cat > .env << EOF
DISCORD_TOKEN=your_token
API_URL=https://your-backend.koyeb.app
LOG_LEVEL=DEBUG
EOF

# Run locally
python main.py
```

### Verify Environment Variables

```bash
# List all variables
koyeb service get SERVICE_NAME --output json | jq '.env'

# Check specific variable
koyeb service get SERVICE_NAME --output json | jq '.env[] | select(.key=="API_URL")'
```

---

## Common Error Messages

### Backend

| Error | Cause | Solution |
|-------|-------|----------|
| `GEMINI_API_KEY not found` | Missing env var | Set `GEMINI_API_KEY` |
| `Failed to connect to Qdrant` | Invalid Qdrant config | Check `QDRANT_URL` and `QDRANT_API_KEY` |
| `No question provided` | Wrong parameter name | Use `"question"` not `"query"` |
| `Rate limit exceeded` | Too many requests | Wait or upgrade plan |
| `OOMKilled` | Out of memory | Upgrade instance type |

### Bot

| Error | Cause | Solution |
|-------|-------|----------|
| `Improper token` | Invalid Discord token | Regenerate token |
| `Privileged intent` | Intent not enabled | Enable in Discord Portal |
| `Connection refused` | Backend down | Check backend service |
| `Request timed out` | Backend slow | Increase `API_TIMEOUT` |
| `403 Forbidden` | Missing permissions | Check bot permissions |

---

## Getting Help

If you're still experiencing issues:

1. **Check Logs First**
   ```bash
   koyeb service logs SERVICE_NAME --tail 100
   ```

2. **Verify Configuration**
   - Review [Environment Variables](./environment-variables.md)
   - Check all required variables are set

3. **Test Components Individually**
   - Test backend API directly
   - Test bot locally
   - Test Discord bot permissions

4. **Review Documentation**
   - [Backend Deployment](./backend-deployment.md)
   - [Bot Deployment](./bot-deployment.md)

5. **Contact Support**
   - Koyeb Support: [support.koyeb.com](https://support.koyeb.com)
   - Discord Developer Support: [discord.gg/discord-developers](https://discord.gg/discord-developers)
