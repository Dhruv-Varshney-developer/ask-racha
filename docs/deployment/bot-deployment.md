# Discord Bot Deployment Guide (Koyeb)

This guide walks you through deploying the AskRacha Discord bot on Koyeb.

## Prerequisites

- Koyeb account
- Backend API deployed and running (see [Backend Deployment](./backend-deployment.md))
- Discord Bot Token
- Discord Application configured

## Step 1: Create Discord Bot

### 1.1 Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "AskRacha" (or your preferred name)
4. Click "Create"

### 1.2 Create Bot User

1. Go to "Bot" section in left sidebar
2. Click "Add Bot"
3. Confirm by clicking "Yes, do it!"
4. **Save the Bot Token** (you'll need this for deployment)

### 1.3 Configure Bot Settings

1. **Privileged Gateway Intents** - Enable:
   - ✅ Message Content Intent
   - ✅ Server Members Intent (optional)
   - ✅ Presence Intent (optional)

2. **Bot Permissions** - Required:
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Use Slash Commands

### 1.4 Invite Bot to Server

1. Go to "OAuth2" → "URL Generator"
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions (same as above)
4. Copy the generated URL
5. Open URL in browser and select your server
6. Authorize the bot

## Step 2: Prepare Redis (Optional)

The bot uses Redis for rate limiting. Koyeb doesn't provide managed Redis, so you have two options:

### Option A: Use External Redis (Recommended)

1. **Upstash Redis** (Free tier available)
   - Go to [upstash.com](https://upstash.com)
   - Create a Redis database
   - Get connection URL: `redis://default:password@host:port`

2. **Redis Labs** (Free tier available)
   - Go to [redis.com](https://redis.com)
   - Create a free database
   - Get connection URL

### Option B: Deploy Without Redis

The bot can work without Redis, but rate limiting will be in-memory only (resets on restart).

## Step 3: Deploy on Koyeb

### Option A: Deploy via Koyeb Dashboard

1. **Login to Koyeb**
   - Go to [app.koyeb.com](https://app.koyeb.com)
   - Sign in to your account

2. **Create New Service**
   - Click "Create Service"
   - Select "GitHub" as the source

3. **Connect GitHub Repository**
   - Authorize Koyeb to access your GitHub
   - Select your repository: `MM-ask-racha`
   - Select branch: `main` (or your deployment branch)

4. **Configure Build Settings**
   - **Builder**: Docker
   - **Dockerfile path**: `askracha/bot/Dockerfile`
   - **Build context**: `askracha/bot`

5. **Configure Service Settings**
   - **Service name**: `askracha-bot` (or your preferred name)
   - **Region**: Same as backend for lower latency
   - **Instance type**: 
     - Start with: `nano` (512MB RAM, 0.1 vCPU)
     - Upgrade to `micro` if needed

6. **Configure Ports**
   - **Port**: `8000`
   - **Protocol**: HTTP
   - **Public exposure**: Enable (for health checks)

7. **Set Environment Variables**

   Click "Add Environment Variable" for each:

   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   API_URL=https://your-backend-service.koyeb.app
   API_TIMEOUT=30
   RETRY_ATTEMPTS=3
   MAX_RESPONSE_LENGTH=2000
   LOG_LEVEL=INFO
   ```

   **Optional (if using Redis):**
   ```
   REDIS_URL=redis://default:password@host:port
   ```

8. **Configure Health Check**
   - **Path**: `/health`
   - **Port**: `8000`
   - **Protocol**: HTTP
   - **Grace period**: 60 seconds
   - **Interval**: 30 seconds
   - **Timeout**: 10 seconds
   - **Retries**: 3

9. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (3-5 minutes)

### Option B: Deploy via Koyeb CLI

1. **Install Koyeb CLI** (if not already installed)
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
   koyeb service create askracha-bot \
     --git github.com/YOUR_USERNAME/MM-ask-racha \
     --git-branch main \
     --git-build-command "docker build -f askracha/bot/Dockerfile askracha/bot" \
     --ports 8000:http \
     --routes /:8000 \
     --env DISCORD_TOKEN=your_token \
     --env API_URL=https://your-backend.koyeb.app \
     --env API_TIMEOUT=30 \
     --env RETRY_ATTEMPTS=3 \
     --env MAX_RESPONSE_LENGTH=2000 \
     --env LOG_LEVEL=INFO \
     --instance-type nano \
     --regions fra
   ```

## Step 4: Verify Deployment

1. **Check Service Status**
   - In Koyeb dashboard, wait for status to show "Healthy"
   - Check logs for "Bot is ready!" message

2. **Check Logs**
   ```bash
   koyeb service logs askracha-bot --follow
   ```

   Look for:
   ```json
   {"message": "✅ Bot is ready! Logged in as AskRacha#1234"}
   {"message": "Connected to X guild(s)"}
   ```

3. **Test in Discord**
   - Go to your Discord server
   - Mention the bot: `@AskRacha what is Storacha?`
   - Bot should respond with an answer

## Step 5: Monitor and Maintain

### View Logs
```bash
# Via CLI
koyeb service logs askracha-bot --follow

# Via Dashboard
Go to Service → Logs tab
```

### Check Bot Status
- Discord bot should show as "Online"
- Health endpoint should return 200 OK

### Update Deployment
When you push changes to GitHub:
1. Koyeb automatically detects changes
2. Builds new Docker image
3. Deploys with zero downtime

## Configuration Details

### Dockerfile Location
```
askracha/bot/Dockerfile
```

### Key Files
- `askracha/bot/main.py` - Entry point
- `askracha/bot/bot.py` - Discord bot implementation
- `askracha/bot/api_client.py` - Backend API client
- `askracha/bot/requirements.txt` - Python dependencies

### Resource Requirements

| Instance Type | RAM    | vCPU | Recommended For |
|--------------|--------|------|-----------------|
| nano         | 512MB  | 0.1  | Small servers   |
| micro        | 1GB    | 0.5  | Production      |

## Troubleshooting

### Bot Won't Start

**Check logs for:**
```bash
koyeb service logs askracha-bot --tail 100
```

**Common issues:**
- Invalid Discord token
- Backend API URL incorrect
- Missing environment variables

**Solution:**
```bash
# Verify environment variables
koyeb service get askracha-bot

# Update if needed
koyeb service update askracha-bot \
  --env DISCORD_TOKEN=new_token
```

### Bot Shows Offline in Discord

**Possible causes:**
1. Service crashed - check logs
2. Discord token invalid - regenerate token
3. Intents not enabled - check Discord Developer Portal

### Bot Not Responding to Messages

**Check:**
1. Message Content Intent is enabled in Discord Developer Portal
2. Bot has proper permissions in Discord server
3. Backend API is responding (test with curl)

**Test backend:**
```bash
curl -X POST https://your-backend.koyeb.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

### Rate Limiting Issues

**If using Redis:**
- Verify Redis URL is correct
- Check Redis connection in logs

**If not using Redis:**
- Rate limits reset on bot restart
- Consider using external Redis for production

### Health Check Failing

**Verify:**
1. Port 8000 is exposed
2. Health server is starting
3. Grace period is sufficient (60s)

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DISCORD_TOKEN` | Yes | Discord bot token | `MTIzNDU2...` |
| `API_URL` | Yes | Backend API URL | `https://backend.koyeb.app` |
| `API_TIMEOUT` | No | API request timeout (seconds) | `30` |
| `RETRY_ATTEMPTS` | No | Number of retry attempts | `3` |
| `MAX_RESPONSE_LENGTH` | No | Max Discord message length | `2000` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `REDIS_URL` | No | Redis connection URL | `redis://...` |

## Advanced Configuration

### Custom Commands

The bot supports these interactions:
- **Mentions**: `@AskRacha your question here`
- **Direct Messages**: Send DM to bot
- **Replies**: Reply to bot's message with follow-up

### Rate Limiting

Default rate limits:
- 1 question per 60 seconds per user
- Configurable via Redis or in-memory

### Logging

Logs are in JSON format for easy parsing:
```json
{
  "timestamp": "2025-10-20T08:00:00.000000Z",
  "level": "INFO",
  "logger": "bot",
  "message": "Processing question from User",
  "module": "bot",
  "function": "handle_mention",
  "line": 257
}
```

## Next Steps

After bot is deployed:
1. Test all functionality in Discord
2. Monitor logs for errors
3. Set up alerts in Koyeb dashboard
4. Review [Troubleshooting Guide](./troubleshooting.md)
