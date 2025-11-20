# Quick Start Deployment Guide

Get AskRacha up and running on Koyeb in under 30 minutes.

## Prerequisites Checklist

Before you begin, gather these items:

- [ ] Koyeb account ([sign up here](https://www.koyeb.com))
- [ ] GitHub repository with the code
- [ ] Gemini API key ([get it here](https://aistudio.google.com/app/apikey))
- [ ] Discord bot token ([create bot here](https://discord.com/developers/applications))

## Step 1: Deploy Qdrant (5 minutes)

1. **Login to Koyeb**
   - Go to [app.koyeb.com](https://app.koyeb.com)

2. **Create Service**
   - Click "Create Service" → "Docker Hub"
   - Image: `qdrant/qdrant:latest`

3. **Configure**
   - Name: `askracha-qdrant`
   - Port: `6333`
   - Instance: `small` (2GB RAM minimum)
   - **Enable Persistent Volume**: `/qdrant/storage` (10GB)

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Copy the service URL

5. **Verify**
   ```bash
   curl https://askracha-qdrant-yourorg.koyeb.app/
   ```

## Step 2: Deploy Backend (10 minutes)

1. **Login to Koyeb**
   - Go to [app.koyeb.com](https://app.koyeb.com)

2. **Create Service**
   - Click "Create Service" → "GitHub"
   - Select repository: `MM-ask-racha`
   - Branch: `main`

3. **Configure Build**
   - Builder: Docker
   - Dockerfile: `askracha/backend/Dockerfile`
   - Context: `askracha/backend`

4. **Set Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_key
   QDRANT_URL=https://askracha-qdrant-yourorg.koyeb.app
   FLASK_ENV=production
   ```

5. **Configure Service**
   - Name: `askracha-backend`
   - Port: `5000`
   - Instance: `nano` (upgrade later if needed)
   - Health check path: `/api/health`
   - Grace period: `90` seconds

6. **Deploy**
   - Click "Deploy"
   - Wait 5-10 minutes
   - Copy the service URL

7. **Verify**
   ```bash
   curl https://your-backend.koyeb.app/api/health
   ```

## Step 3: Create Discord Bot (5 minutes)

1. **Go to Discord Developer Portal**
   - Visit [discord.com/developers/applications](https://discord.com/developers/applications)
   - Click "New Application"
   - Name it "AskRacha"

2. **Create Bot**
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the token (save it securely)

3. **Enable Intents**
   - Enable "Message Content Intent"
   - Save changes

4. **Invite to Server**
   - Go to "OAuth2" → "URL Generator"
   - Select: `bot` and `applications.commands`
   - Select permissions: Read Messages, Send Messages, Read Message History
   - Copy URL and open in browser
   - Select your Discord server

## Step 4: Deploy Bot (10 minutes)

1. **Create Service in Koyeb**
   - Click "Create Service" → "GitHub"
   - Select repository: `MM-ask-racha`
   - Branch: `main`

2. **Configure Build**
   - Builder: Docker
   - Dockerfile: `askracha/bot/Dockerfile`
   - Context: `askracha/bot`

3. **Set Environment Variables**
   ```
   DISCORD_TOKEN=your_discord_token
   API_URL=https://your-backend.koyeb.app
   API_TIMEOUT=30
   LOG_LEVEL=INFO
   ```

4. **Configure Service**
   - Name: `askracha-bot`
   - Port: `8000`
   - Instance: `nano`
   - Health check path: `/health`
   - Grace period: `60` seconds

5. **Deploy**
   - Click "Deploy"
   - Wait 3-5 minutes

6. **Verify**
   - Check logs for "Bot is ready!"
   - Bot should show online in Discord

## Step 5: Test (2 minutes)

1. **In Discord**
   - Go to your server
   - Type: `@AskRacha what is Storacha?`
   - Bot should respond with an answer

2. **If it works** 🎉
   - You're done! Bot is live

3. **If it doesn't work** 🔧
   - Check [Troubleshooting Guide](./troubleshooting.md)
   - Review logs in Koyeb dashboard

## Next Steps

- **Monitor**: Check Koyeb dashboard for metrics
- **Scale**: Upgrade instance types if needed
- **Customize**: Modify bot behavior in code
- **Add Features**: Extend functionality

## Quick Reference

### Backend URL Format
```
https://your-backend-name.koyeb.app
```

### Test Backend
```bash
curl -X POST https://your-backend.koyeb.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Storacha?"}'
```

### View Logs
```bash
# Install Koyeb CLI
brew install koyeb/tap/koyeb-cli

# View logs
koyeb service logs askracha-backend --follow
koyeb service logs askracha-bot --follow
```

### Update Deployment
Push changes to GitHub → Koyeb auto-deploys

## Cost Estimate

| Service | Instance | Monthly Cost |
|---------|----------|--------------|
| Qdrant | small | ~$15-20 |
| Backend | nano | ~$5-10 |
| Bot | nano | ~$5-10 |
| **Total** | | **~$25-40** |

*Prices are approximate. Check Koyeb pricing for exact costs.*

## Need Help?

- **Full Guides**: See [Backend](./backend-deployment.md) and [Bot](./bot-deployment.md) deployment guides
- **Environment Variables**: See [complete reference](./environment-variables.md)
- **Issues**: Check [Troubleshooting Guide](./troubleshooting.md)
