#!/bin/bash

# 🚀 Qwen UI Permanent Startup Fix
# This script ensures all components are properly configured and running

echo "🚀 Starting Qwen UI Permanent Fix..."

# 1. Install backend dependencies
echo "📦 Installing backend dependencies..."
cd /app/backend
pip install -r requirements.txt > /dev/null 2>&1

# 2. Install frontend dependencies  
echo "📦 Installing frontend dependencies..."
cd /app/frontend
yarn install > /dev/null 2>&1

# 3. Build React frontend
echo "🔨 Building React frontend..."
yarn build > /dev/null 2>&1

# 4. Restart all services
echo "🔄 Restarting services..."
sudo supervisorctl restart all

# 5. Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 5

# 6. Test backend connectivity
echo "🧪 Testing backend connectivity..."
if curl -s http://localhost:8001/api/model > /dev/null; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: Failed"
fi

# 7. Test frontend accessibility  
echo "🧪 Testing frontend accessibility..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: Failed"
fi

# 8. Show final status
echo ""
echo "📊 Final Status:"
sudo supervisorctl status

echo ""
echo "🎉 Startup fix completed!"
echo "🌐 Frontend URL: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8001/api"
echo ""
echo "✨ System is ready for E1 to continue working!"