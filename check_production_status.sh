#!/bin/bash
# Production status check script

echo "📊 Okypbot Production Status Check"
echo "=================================="

# Check if services are running
echo "🐳 Docker Services Status:"
docker-compose -f docker/docker-compose.prod.yml ps

echo ""
echo "🔍 Detailed Service Information:"

# Check bot container
if docker ps | grep -q okypbot_app; then
    echo "✅ Bot container is running"

    # Check bot logs for errors
    echo ""
    echo "📝 Recent bot logs:"
    docker-compose -f docker/docker-compose.prod.yml logs --tail=10 bot

    # Check if bot is responding
    echo ""
    echo "🌡️ Bot health check:"
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "✅ Bot health endpoint is responding"
    else
        echo "❌ Bot health endpoint is not responding"
    fi
else
    echo "❌ Bot container is not running"
fi

# Check PostgreSQL
if docker ps | grep -q okypbot_postgres; then
    echo ""
    echo "✅ PostgreSQL container is running"

    # Check database connectivity
    echo "🗄️ Database connectivity:"
    if docker-compose -f docker/docker-compose.prod.yml exec -T postgres pg_isready -U postgres -d okypbot > /dev/null; then
        echo "✅ Database is ready"
    else
        echo "❌ Database is not ready"
    fi
else
    echo "❌ PostgreSQL container is not running"
fi

# Check nginx
if docker ps | grep -q okypbot_nginx; then
    echo ""
    echo "✅ Nginx container is running"

    # Check nginx health
    echo "🌐 Nginx health check:"
    if curl -s -f http://localhost:8080/health > /dev/null; then
        echo "✅ Nginx is responding"
    else
        echo "❌ Nginx is not responding"
    fi
else
    echo "❌ Nginx container is not running"
fi

echo ""
echo "💡 Troubleshooting commands:"
echo "  View all logs: docker-compose -f docker/docker-compose.prod.yml logs -f"
echo "  Restart all: docker-compose -f docker/docker-compose.prod.yml restart"
echo "  Rebuild: docker-compose -f docker/docker-compose.prod.yml up -d --build"
echo "  Stop all: docker-compose -f docker/docker-compose.prod.yml down"
