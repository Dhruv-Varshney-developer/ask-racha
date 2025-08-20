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

Then edit both `.env` files and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here

```

## Vector Store Setup

### Local Development

1. Make sure Docker is installed and running
2. Start Qdrant:

```bash
cd askracha/backend/storage
docker compose up -d
```

3. Verify the setup:

```bash
cd askracha/backend
python -m unittest storage/tests/test_vector_store.py -v
```

### Environment Variables

For local development:

- No additional env vars needed, uses Qdrant Local by default
- Qdrant runs on port 6343 (configurable via QDRANT_PORT)

For production:

```env
QDRANT_HOST=your_qdrant_host
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key
```

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
askracha/
├── backend/           # Python Flask backend
│   ├── app.py        # Main Flask application
│   ├── rag.py        # RAG implementation
│   └── requirements.txt
├── src/              # Frontend source code
├── public/           # Static assets
└── package.json      # Frontend dependencies and scripts
```

## License

This project is licensed under the terms of the license included in the repository.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
