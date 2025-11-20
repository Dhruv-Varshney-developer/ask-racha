# AskRacha Deployment Documentation

This directory contains comprehensive guides for deploying the AskRacha system on Koyeb.

## Documentation Structure

- **[Quick Start](./quick-start.md)** - Get started in 30 minutes
- **[Deployment Checklist](./deployment-checklist.md)** - Step-by-step deployment checklist
- **[Qdrant Deployment](./qdrant-deployment.md)** - Guide for deploying Qdrant vector database
- **[Backend Deployment](./backend-deployment.md)** - Guide for deploying the RAG API backend
- **[Bot Deployment](./bot-deployment.md)** - Guide for deploying the Discord bot
- **[Environment Variables](./environment-variables.md)** - Complete reference for all environment variables
- **[Troubleshooting](./troubleshooting.md)** - Common issues and solutions

## Quick Start

### Prerequisites

1. **Koyeb Account** - Sign up at [koyeb.com](https://www.koyeb.com)
2. **GitHub Repository** - Your code should be in a GitHub repository
3. **API Keys**:
   - Gemini API key (for backend)
   - Discord Bot Token (for bot)

### Deployment Order

Deploy in this order to ensure proper functionality:

1. **Qdrant First** - Deploy the vector database
2. **Backend Second** - Deploy the RAG API backend (requires Qdrant URL)
3. **Bot Third** - Deploy the Discord bot (requires backend URL)

### Architecture Overview

```
┌─────────────────┐
│  Discord Users  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Discord Bot    │ (Koyeb Service)
│  Port: 8000     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend API    │ (Koyeb Service)
│  Port: 5000     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Qdrant Vector  │ (Koyeb Service)
│  Database       │
│  Port: 6333     │
└─────────────────┘
```

## Support

For issues or questions:
- Check the [Troubleshooting Guide](./troubleshooting.md)
- Review Koyeb logs in the dashboard
- Verify all environment variables are set correctly
