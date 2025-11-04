#!/bin/bash
# Deployment script for ImaLink to trollfjell.com
# Usage: ./scripts/deploy.sh

set -e  # Exit on any error

echo "🚀 Deploying ImaLink to trollfjell.com..."
echo ""

# 1. Push changes to GitHub
echo "📤 Pushing changes to GitHub..."
git push
echo "✅ Pushed to GitHub"
echo ""

# 2. Deploy on server
echo "🔗 Connecting to trollfjell..."
ssh -t trollfjell << 'EOF'
    set -e
    cd ~/imalink
    
    echo "📥 Pulling latest changes..."
    git pull
    
    echo "📦 Syncing dependencies..."
    ~/.local/bin/uv sync --python python3.13
    
    echo "�️  Running database migrations..."
    ~/.local/bin/uv run alembic upgrade head
    
    echo "�🔄 Restarting imalink service..."
    sudo systemctl restart imalink
    
    # Wait a moment for service to start
    sleep 2
    
    echo ""
    echo "📊 Service Status:"
    sudo systemctl status imalink --no-pager -l | head -15
    
    echo ""
    echo "📋 Recent Logs:"
    sudo journalctl -u imalink -n 15 --no-pager
    
    echo ""
    echo "🔍 Testing local endpoint..."
    curl -s http://127.0.0.1:8000/health || echo "⚠️  Health check failed"
EOF

echo ""
echo "✅ Deployment complete!"
echo "🌐 API: http://trollfjell.com:8000"
echo "📖 Docs: http://trollfjell.com:8000/docs"
