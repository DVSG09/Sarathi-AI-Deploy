# 🚀 Render Deployment Guide

## Quick Deploy to Render

### 1. **Connect Repository**
- Go to [Render Dashboard](https://dashboard.render.com)
- Click "New +" → "Web Service"
- Connect your GitHub repository

### 2. **Configure Service**
- **Name**: `sarathi-ai-chatbot`
- **Environment**: `Docker`
- **Dockerfile Path**: `./Dockerfile`
- **Plan**: `Free` (or upgrade as needed)

### 3. **Environment Variables**
Set these in Render dashboard:

```
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=chat-deploy
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=embedding-deploy
APP_NAME=Sarathi
APP_ENV=production
LOG_LEVEL=info
ENABLED_INTENTS=status,faq,billing,appointment,account
```

### 4. **Deploy**
- Click "Create Web Service"
- Render will automatically build and deploy
- Your app will be available at: `https://sarathi-ai-chatbot.onrender.com`

## 🔧 Manual Deployment Steps

### Using render.yaml (Recommended)
1. Push your code to GitHub
2. In Render dashboard, select "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml` and deploy

### Using Docker
1. Ensure Dockerfile is in root directory
2. Set environment variables in Render dashboard
3. Deploy with Docker environment

## 📋 Pre-deployment Checklist

- [ ] ✅ `render.yaml` configured
- [ ] ✅ `Dockerfile` optimized for production
- [ ] ✅ `.dockerignore` excludes unnecessary files
- [ ] ✅ Environment variables set in Render
- [ ] ✅ Azure OpenAI credentials configured
- [ ] ✅ Health check endpoint working (`/health`)

## 🔍 Troubleshooting

### Common Issues:
1. **Build Fails**: Check Dockerfile and requirements.txt
2. **App Crashes**: Check environment variables
3. **Health Check Fails**: Verify `/health` endpoint
4. **Slow Startup**: Free tier has cold starts

### Logs:
- Check Render dashboard → Your Service → Logs
- Look for startup errors or missing environment variables

## 🌐 Post-Deployment

### Access Your App:
- **Web Interface**: `https://your-app-name.onrender.com`
- **API Docs**: `https://your-app-name.onrender.com/docs`
- **Health Check**: `https://your-app-name.onrender.com/health`

### Features Available:
- ✅ Chat interface
- ✅ File upload/download
- ✅ Chat history
- ✅ MyPursu service integration
- ✅ Live support

## 💡 Tips for Production

1. **Upgrade Plan**: Free tier has limitations (sleeps after 15min inactivity)
2. **Environment Variables**: Keep sensitive data in Render dashboard, not in code
3. **Monitoring**: Use Render's built-in monitoring
4. **Custom Domain**: Add your own domain in Render settings
5. **SSL**: Automatically provided by Render

## 🔄 Updates

To update your deployment:
1. Push changes to your GitHub repository
2. Render will automatically rebuild and redeploy
3. Check logs for any issues

---

**Need Help?** Check Render's [documentation](https://render.com/docs) or contact support.
