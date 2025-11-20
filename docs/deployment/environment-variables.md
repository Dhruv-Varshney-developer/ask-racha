# Environment Variables Reference

Complete reference for all environment variables used in the AskRacha system.

## Backend Environment Variables

### Required Variables

#### `GEMINI_API_KEY`
- **Required**: Yes
- **Description**: Google Gemini API key for LLM queries
- **Where to get**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Example**: `AIzaSyD...`
- **Notes**: Keep this secret and never commit to version control

#### `QDRANT_URL`
- **Required**: Yes
- **Description**: Qdrant vector database service URL on Koyeb
- **Where to get**: Your Qdrant service URL from Koyeb dashboard
- **Example**: `https://askracha-qdrant-yourorg.koyeb.app`
- **Notes**: Must include `https://` protocol

#### `QDRANT_API_KEY`
- **Required**: No
- **Description**: Qdrant API key for authentication (if enabled)
- **Where to get**: Set when deploying Qdrant with authentication
- **Example**: `eyJ0eXAiOiJKV1Q...`
- **Notes**: Only required if you enabled authentication on your Qdrant service

### Optional Variables

#### `FLASK_ENV`
- **Required**: No
- **Description**: Flask environment mode
- **Default**: `development`
- **Allowed values**: `development`, `production`
- **Example**: `production`
- **Notes**: Set to `production` for deployed environments

#### `PORT`
- **Required**: No
- **Description**: Port for Flask server
- **Default**: `5000`
- **Example**: `5000`
- **Notes**: Koyeb automatically sets this

#### `QDRANT_COLLECTION_NAME`
- **Required**: No
- **Description**: Name of Qdrant collection
- **Default**: `askracha_docs`
- **Example**: `askracha_docs`
- **Notes**: Change if you want separate collections

---

## Bot Environment Variables

### Required Variables

#### `DISCORD_TOKEN`
- **Required**: Yes
- **Description**: Discord bot authentication token
- **Where to get**: [Discord Developer Portal](https://discord.com/developers/applications) → Your App → Bot → Token
- **Example**: `YOUR_DISCORD_BOT_TOKEN`
- **Notes**: 
  - Keep this secret and never commit to version control
  - Treat tokens like passwords—store them only in environment variables or secure secret managers
  - Regenerate if compromised
  - Must enable Message Content Intent in Discord Portal

#### `API_URL`
- **Required**: Yes
- **Description**: Backend API base URL
- **Example**: `https://your-backend.koyeb.app`
- **Notes**: 
  - Must be the full URL including `https://`
  - No trailing slash
  - Must be accessible from bot service

### Optional Variables

#### `API_TIMEOUT`
- **Required**: No
- **Description**: Timeout for API requests in seconds
- **Default**: `30`
- **Example**: `30`
- **Notes**: Increase if backend responses are slow

#### `RETRY_ATTEMPTS`
- **Required**: No
- **Description**: Number of retry attempts for failed API requests
- **Default**: `3`
- **Example**: `3`
- **Notes**: Exponential backoff is used between retries

#### `MAX_RESPONSE_LENGTH`
- **Required**: No
- **Description**: Maximum length of Discord messages
- **Default**: `2000`
- **Example**: `2000`
- **Notes**: Discord limit is 2000 characters

#### `LOG_LEVEL`
- **Required**: No
- **Description**: Logging verbosity level
- **Default**: `INFO`
- **Allowed values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `INFO`
- **Notes**: Use `DEBUG` for troubleshooting

#### `REDIS_URL`
- **Required**: No
- **Description**: Redis connection URL for rate limiting
- **Example**: `redis://default:password@host:port`
- **Notes**: 
  - If not provided, in-memory rate limiting is used
  - Format: `redis://[username]:[password]@[host]:[port]`
  - Supports Redis Cloud, Upstash, etc.

#### `RATE_LIMIT_WINDOW`
- **Required**: No
- **Description**: Rate limit time window in seconds
- **Default**: `60`
- **Example**: `60`
- **Notes**: Users can ask 1 question per this window

#### `RATE_LIMIT_MAX_REQUESTS`
- **Required**: No
- **Description**: Maximum requests per time window
- **Default**: `1`
- **Example**: `1`
- **Notes**: Number of questions allowed per window

---

## Setting Environment Variables

### Koyeb Dashboard

1. Go to your service
2. Click "Settings" tab
3. Scroll to "Environment Variables"
4. Click "Add Variable"
5. Enter name and value
6. Click "Save"
7. Service will redeploy automatically

### Koyeb CLI

```bash
# Add single variable
koyeb service update SERVICE_NAME \
  --env VARIABLE_NAME=value

# Add multiple variables
koyeb service update SERVICE_NAME \
  --env VAR1=value1 \
  --env VAR2=value2 \
  --env VAR3=value3
```

### Local Development (.env file)

Create `.env` file in the respective directory:

**Backend** (`askracha/backend/.env`):
```bash
GEMINI_API_KEY=your_key_here
QDRANT_URL=https://askracha-qdrant-yourorg.koyeb.app
FLASK_ENV=development
# QDRANT_API_KEY=your_key_here  # Only if authentication enabled
```

**Bot** (`askracha/bot/.env`):
```bash
DISCORD_TOKEN=your_token_here
API_URL=http://localhost:5000
API_TIMEOUT=30
RETRY_ATTEMPTS=3
MAX_RESPONSE_LENGTH=2000
LOG_LEVEL=DEBUG
```


## Troubleshooting

### "Environment variable not found"
**Solution**: Set the variable in Koyeb dashboard and redeploy

### "Invalid API key"
**Solution**: Regenerate key and update in Koyeb

### "Connection refused"
**Solution**: Verify URL format and network connectivity

### "Permission denied"
**Solution**: Check API key permissions and scopes

---

## Quick Reference Table

| Variable | Backend | Bot | Required | Default |
|----------|---------|-----|----------|---------|
| `GEMINI_API_KEY` | ✅ | ❌ | Yes | - |
| `QDRANT_URL` | ✅ | ❌ | Yes | - |
| `QDRANT_API_KEY` | ✅ | ❌ | No* | - |
| `FLASK_ENV` | ✅ | ❌ | No | `development` |
| `DISCORD_TOKEN` | ❌ | ✅ | Yes | - |
| `API_URL` | ❌ | ✅ | Yes | - |
| `API_TIMEOUT` | ❌ | ✅ | No | `30` |
| `RETRY_ATTEMPTS` | ❌ | ✅ | No | `3` |
| `MAX_RESPONSE_LENGTH` | ❌ | ✅ | No | `2000` |
| `LOG_LEVEL` | ❌ | ✅ | No | `INFO` |
| `REDIS_URL` | ❌ | ✅ | No | - |

*Only required if Qdrant authentication is enabled
