#!/bin/bash

echo "🚀 Sarathi Backend Deployment Script"
echo "====================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Sarathi backend"
fi

echo "📋 Deployment Checklist:"
echo "1. ✅ Dockerfile created"
echo "2. ✅ render.yaml configuration ready"
echo "3. ✅ Frontend updated with placeholder URL"
echo "4. ✅ Requirements.txt updated"
echo ""
echo "🔧 Next Steps:"
echo "1. Push this code to GitHub:"
echo "   git remote add origin <your-github-repo-url>"
echo "   git push -u origin main"
echo ""
echo "2. Go to https://render.com and:"
echo "   - Create a new Web Service"
echo "   - Connect your GitHub repository"
echo "   - Use Docker deployment"
echo "   - Set environment variables:"
echo "     * AZURE_OPENAI_ENDPOINT"
echo "     * AZURE_OPENAI_API_KEY"
echo "     * AZURE_OPENAI_API_VERSION=2025-01-01-preview"
echo "     * AZURE_OPENAI_DEPLOYMENT=sarathi-deploy"
echo ""
echo "3. After deployment, update sarathi-frontend.html with your Render URL"
echo "4. Upload the updated frontend to your hosting service"
echo ""
echo "🎯 Your backend will be available at: https://<your-service-name>.onrender.com"
