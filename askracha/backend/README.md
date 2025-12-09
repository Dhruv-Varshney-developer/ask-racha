# AskRacha Backend

This is the backend API for AskRacha, built with Flask and powered by Google Gemini AI with RAG (Retrieval-Augmented Generation) using Pinecone vector database.

## Prerequisites

- Python 3.8+
- Gemini API key
- Pinecone account and API key
- Redis instance (for rate limiting)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend` folder with the following configuration:

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=ask-racha

# Redis Configuration (for rate limiting)
REDIS_URL=your_redis_url_here

# Flask Configuration
ALLOWED_ORIGINS=http://localhost:3000
FLASK_ENV=development
```

### 3. Run the Backend

```bash
python app.py
```

The backend will:

- Start the Flask server on `http://localhost:5000`
- Automatically create/configure the Pinecone index if it doesn't exist
- Load the knowledge base from the documentation repositories
- Initialize the RAG system

**Note:** First run may take 1-2 minutes while the backend loads documentation and creates embeddings.

## API Endpoints

### Health Check

```bash
curl http://localhost:5000/api/health
```

Response: `{"status": "healthy"}`

### Chat

```bash
POST http://localhost:5000/api/chat
Content-Type: application/json

{
  "message": "Your question here",
  "session_id": "optional-session-id"
}
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Viewing Logs

The application logs to stdout. You can adjust the logging level in `app.py`.

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── rag.py                 # RAG implementation
├── requirements.txt       # Python dependencies
├── rate_limit/           # Rate limiting module
│   └── rate_limiter.py
├── storage/              # Vector store implementation
│   ├── __init__.py
│   └── pinecone_vector_store.py
└── repos/                # Documentation repositories
    └── setup-repos.sh
```

## Troubleshooting

### Pinecone Connection Issues

- Verify your `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT` are correct
- Check that your Pinecone account is active
- Ensure the index name doesn't conflict with existing indexes

### Redis Connection Issues

- Verify your `REDIS_URL` is correct
- For local development, ensure Redis is running: `redis-server`
- For cloud Redis, check your service provider's connection details

### Knowledge Base Not Loading

- Ensure the documentation repositories are cloned in the `repos/` folder
- Check that the repositories contain valid markdown files
- Review the logs for any embedding generation errors
