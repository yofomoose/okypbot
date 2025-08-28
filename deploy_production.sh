#!/bin/bash
# Production deployment script for okypbot

echo "🚀 Starting okypbot production deployment..."

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo "Please create .env.production file with your production settings"
    exit 1
fi

# Check if bot_model directory exists
if [ ! -d "bot_model" ]; then
    echo "❌ bot_model directory not found!"
    echo "Please ensure bot_model directory with trained models exists"
    exit 1
fi

# Set production environment
export COMPOSE_ENV_FILE=.env.production

echo "📦 Building and starting services..."
cd docker

# Build and start services
docker-compose -f docker-compose.prod.yml --env-file ../.env.production up -d --build

echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Check health endpoints
echo ""
echo "🌡️ Checking health status..."
echo "Bot health:"
curl -s http://localhost:8000/health || echo "❌ Bot health check failed"

echo ""
echo "PostgreSQL health:"
docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U postgres -d okypbot || echo "❌ PostgreSQL health check failed"

echo ""
echo "Nginx health:"
curl -s http://localhost:8080/health || echo "❌ Nginx health check failed"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f bot"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart bot: docker-compose -f docker-compose.prod.yml restart bot"
echo ""
echo "🔗 Service URLs:"
echo "  Bot webhook: http://localhost:8080/okdesk-webhook"
echo "  Health check: http://localhost:8080/health"
echo "  Direct bot: http://localhost:8000"
