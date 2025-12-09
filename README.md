# Ask Racha

A web application that provides an AI-powered interface to interact with Storacha's documentation. The application uses advanced language models and RAG (Retrieval-Augmented Generation) to provide accurate and contextual responses.

## Features

- Interactive chat interface
- Integration with Google's Gemini AI model
- Web-based documentation retrieval
- Real-time response generation
- Modern UI built with Next.js and Tailwind CSS

## Tech Stack

### Frontend

- Next.js 15.3.3
- React 19
- TypeScript
- Tailwind CSS
- Lucide React (for icons)

### Backend

- Python Flask
- LlamaIndex
- Google Gemini AI
- BeautifulSoup4 (for web scraping)

## Prerequisites

- Node.js (Latest LTS version)
- Python 3.8+
- Gemini API key
- Pinecone account and API key
- Redis instance (for rate limiting)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Dhruv-Varshney-developer/ask-racha.git
cd ask-racha
```

2. Install frontend dependencies:

```bash
cd askracha
npm install
```

3. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables:

For the frontend:

```bash
cd askracha
cp .env.example .env
```

For the backend:

```bash
cd askracha/backend
cp .env.example .env
```

Then edit the backend `.env` file and add your configuration:

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=ask-racha

# Redis Configuration (for rate limiting)
REDIS_URL=your_redis_url_here
# Example: redis://localhost:6379 for local development
# Or use a cloud Redis service like Upstash, Redis Cloud, etc.
```

## Vector Store Setup

This application uses Pinecone as the vector database for storing and retrieving document embeddings.

### Setting up Pinecone

1. **Create a Pinecone Account:**

   - Go to [Pinecone.io](https://www.pinecone.io/) and sign up for a free account
   - Navigate to the API Keys section in your dashboard

2. **Get Your API Key:**

   - Copy your API key from the Pinecone dashboard
   - Note your environment (e.g., `us-east-1-aws`, `gcp-starter`)

3. **Configure Environment Variables:**

Add the following to your backend `.env` file:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=ask-racha
```

### Index Configuration

The application automatically creates and configures the Pinecone index on startup with the following settings:

- **Dimension:** 768 (matches the embedding model)
- **Metric:** Cosine similarity
- **Index Name:** `ask-racha` (configurable via `PINECONE_INDEX_NAME`)

The knowledge base is loaded automatically when the backend starts, so there's no need for manual indexing.

## Running the Application

### Development Mode

To run both frontend and backend concurrently:

```bash
npm run dev:full
```

Or run them separately:

Frontend:

```bash
npm run dev
```

Backend:

```bash
npm run backend
```

### Production Build

1. Build the frontend:

```bash
npm run build
```

2. Start the production server:

```bash
npm run start
```

## Available Scripts

- `npm run dev` - Start the Next.js development server with Turbopack
- `npm run build` - Build the application for production
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint for code linting
- `npm run backend` - Start the Python backend server
- `npm run dev:full` - Run both frontend and backend concurrently

## Project Structure

```
ask-racha/
├── askracha/                    # Main application directory
│   ├── backend/                 # Python Flask backend
│   │   ├── app.py              # Main Flask application
│   │   ├── rag.py              # RAG implementation with Pinecone
│   │   ├── chat_context.py     # Chat context management
│   │   ├── document_scheduler.py # Document update scheduler
│   │   ├── requirements.txt    # Python dependencies
│   │   ├── storage/            # Vector store implementation
│   │   │   ├── __init__.py
│   │   │   └── pinecone_vector_store.py
│   │   ├── rate_limit/         # Rate limiting module
│   │   │   └── rate_limiter.py
│   │   ├── repos/              # Documentation repositories
│   │   │   └── setup-repos.sh # Script to clone docs
│   │   └── .env.example        # Backend environment template
│   │
│   ├── bot/                    # Discord bot (optional)
│   │   ├── bot.py             # Discord bot implementation
│   │   ├── api_client.py      # API client for backend
│   │   ├── config.py          # Bot configuration
│   │   ├── requirements.txt   # Bot dependencies
│   │   └── .env.example       # Bot environment template
│   │
│   ├── src/                   # Frontend source code
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── types/            # TypeScript type definitions
│   │   └── middleware.ts     # Next.js middleware
│   │
│   ├── package.json          # Frontend dependencies
│   ├── next.config.ts        # Next.js configuration
│   ├── tailwind.config.ts    # Tailwind CSS configuration
│   ├── tsconfig.json         # TypeScript configuration
│   └── .env.example          # Frontend environment template
│
├── README.md                 # This file
├── LICENSE                   # Project license
└── .gitignore               # Git ignore rules
```

## License

This project is licensed under the terms of the license included in the repository.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
