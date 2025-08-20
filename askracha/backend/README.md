# AskRacha Backend - Quick Start

This README covers only the backend setup (API + Qdrant via Docker Compose).

## 1) Prerequisites
- Docker and Docker Compose
- A valid Gemini API key

## 2) Create .env (in this folder)
Create a file named `.env` in `askracha/backend` with the following contents:

```
GEMINI_API_KEY=your_gemini_key_here
ALLOWED_ORIGINS=http://localhost:3000
FLASK_ENV=development
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

## 3) Build and start (detached)
From `askracha/backend`:

```
docker compose up --build -d
```

- First run may take 1-2 minutes while the backend loads default documentation, loads from the vector store, and creates/loads indexes.

## 4) Check logs (debug)
Stream backend logs:

```
docker compose logs -f askracha-backend
```

Optionally, Qdrant logs:
```
docker compose logs -f qdrant
```

## 5) Health check
Verify the API is up:

```
curl http://localhost:5000/api/health
```

You should see a JSON response with `status: "healthy"`.