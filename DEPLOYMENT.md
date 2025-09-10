# Sarathi Backend Deployment Guide

## Environment Variables Required

Set these environment variables in your Render dashboard:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=sarathi-deploy
```

## Deployment Steps

1. Push your code to a GitHub repository
2. Connect the repository to Render
3. Create a new Web Service
4. Use the Dockerfile for deployment
5. Set the environment variables above
6. Deploy!

## Health Check

The application includes a health check endpoint at `/health` that Render will use to monitor the service.

## API Endpoints

- `GET /` - Serves the frontend
- `POST /chat` - Chat endpoint
- `GET /feed` - Get feed data
- `GET /health` - Health check

