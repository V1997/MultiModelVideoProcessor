#!/bin/bash
# Frontend Testing - Service Startup Script
# This script starts all required services for full MultiModelVideo frontend testing

echo "🚀 Starting MultiModelVideo Services for Frontend Testing"
echo "========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo -e "${YELLOW}Checking $service_name on port $port...${NC}"
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not responding${NC}"
        return 1
    fi
}

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    local check_url=$4
    
    echo -e "${YELLOW}Starting $service_name...${NC}"
    
    # Start service in background
    eval "$command" &
    local pid=$!
    echo "Started $service_name with PID: $pid"
    
    # Wait a moment for service to start
    sleep 3
    
    # Check if service is running
    if check_service "$service_name" "$port" "$check_url"; then
        echo -e "${GREEN}✅ $service_name started successfully${NC}"
        echo "$pid" > ".${service_name,,}_pid"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        kill $pid 2>/dev/null
    fi
    
    echo ""
}

# Function to create .env file if it doesn't exist
setup_environment() {
    echo -e "${YELLOW}Setting up environment...${NC}"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo "Creating .env from .env.example..."
            cp .env.example .env
            echo -e "${GREEN}✅ .env file created${NC}"
        else
            echo "Creating basic .env file..."
            cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./multimodal_video.db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multimodelovideo
DB_USER=postgres
DB_PASSWORD=

# Redis Configuration (Optional - system will work without Redis)
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Configuration
API_HOST=127.0.0.1
API_PORT=8001
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080

# File Storage
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed
FRAMES_DIR=./frames

# Development
DEBUG=True
LOG_LEVEL=INFO
EOF
            echo -e "${GREEN}✅ Basic .env file created${NC}"
        fi
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
    
    # Create necessary directories
    mkdir -p uploads processed frames temp vector_db
    echo -e "${GREEN}✅ Directories created${NC}"
    echo ""
}

# Function to start HTTP server for frontend
start_frontend_server() {
    echo -e "${YELLOW}Starting Frontend HTTP Server...${NC}"
    
    cd frontend
    
    # Try to start a simple HTTP server
    if command -v python &> /dev/null; then
        if python --version 2>&1 | grep -q "Python 3"; then
            python -m http.server 8080 &
            frontend_pid=$!
        else
            python -m SimpleHTTPServer 8080 &
            frontend_pid=$!
        fi
        echo "Frontend server started with PID: $frontend_pid"
        echo "$frontend_pid" > "../.frontend_pid"
        sleep 2
        echo -e "${GREEN}✅ Frontend server running at http://localhost:8080${NC}"
    elif command -v node &> /dev/null; then
        if command -v npx &> /dev/null; then
            npx http-server -p 8080 &
            frontend_pid=$!
            echo "Frontend server started with PID: $frontend_pid"
            echo "$frontend_pid" > "../.frontend_pid"
            sleep 2
            echo -e "${GREEN}✅ Frontend server running at http://localhost:8080${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No HTTP server available. You can open frontend/phase3_to_5_demo.html directly in browser${NC}"
    fi
    
    cd ..
    echo ""
}

# Function to stop all services
stop_services() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    
    # Stop services by reading PID files
    for pidfile in .*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid | sed 's/^.//')
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            rm "$pidfile"
        fi
    done
    
    # Kill any remaining processes on our ports
    pkill -f "uvicorn.*8001" 2>/dev/null
    pkill -f "python.*http.server.*8080" 2>/dev/null
    pkill -f "http-server.*8080" 2>/dev/null
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Main execution
case "$1" in
    "start")
        echo "Starting all services for frontend testing..."
        echo ""
        
        # Setup environment
        setup_environment
        
        # Start Backend API Server
        start_service "Backend API" \
                     "cd backend && python -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload" \
                     "8001" \
                     "http://127.0.0.1:8001/health"
        
        # Start Frontend Server
        start_frontend_server
        
        echo -e "${GREEN}🎉 All services started successfully!${NC}"
        echo ""
        echo -e "${YELLOW}📋 Service URLs:${NC}"
        echo "🔗 Backend API: http://127.0.0.1:8001"
        echo "🔗 API Docs: http://127.0.0.1:8001/docs"
        echo "🔗 Frontend: http://localhost:8080/phase3_to_5_demo.html"
        echo "🔗 Health Check: http://127.0.0.1:8001/health"
        echo ""
        echo -e "${YELLOW}🧪 Frontend Testing Commands:${NC}"
        echo "• Test API connection: curl http://127.0.0.1:8001/health"
        echo "• Test YouTube search: curl -X POST http://127.0.0.1:8001/api/v1/youtube/search \\"
        echo "    -H 'Content-Type: application/json' \\"
        echo "    -d '{\"query\": \"test video\", \"max_results\": 5}'"
        echo "• Monitor logs: tail -f backend/logs/*.log (if logging enabled)"
        echo ""
        echo -e "${YELLOW}🛑 To stop all services: $0 stop${NC}"
        ;;
        
    "stop")
        stop_services
        ;;
        
    "status")
        echo "Checking service status..."
        echo ""
        
        check_service "Backend API" "8001" "http://127.0.0.1:8001/health"
        check_service "Frontend Server" "8080" "http://localhost:8080"
        
        echo ""
        echo "Active processes:"
        ps aux | grep -E "(uvicorn|http.server|http-server)" | grep -v grep || echo "No active services found"
        ;;
        
    "restart")
        echo "Restarting all services..."
        stop_services
        sleep 2
        $0 start
        ;;
        
    "logs")
        echo "Showing recent logs..."
        echo ""
        
        # Show backend logs if available
        if [ -f "backend/logs/app.log" ]; then
            echo -e "${YELLOW}Backend logs:${NC}"
            tail -20 backend/logs/app.log
        fi
        
        # Show any error logs
        if [ -f "error.log" ]; then
            echo -e "${YELLOW}Error logs:${NC}"
            tail -20 error.log
        fi
        ;;
        
    "test")
        echo "Running quick frontend integration test..."
        echo ""
        
        # Test backend health
        echo "Testing backend health..."
        curl -s http://127.0.0.1:8001/health | python -m json.tool || echo "Backend not responding"
        
        echo ""
        echo "Testing YouTube search endpoint..."
        curl -s -X POST http://127.0.0.1:8001/api/v1/youtube/search \
             -H "Content-Type: application/json" \
             -d '{"query": "test", "max_results": 2}' | python -m json.tool || echo "YouTube search failed"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|restart|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services for frontend testing"
        echo "  stop    - Stop all running services"
        echo "  status  - Check service status"
        echo "  restart - Restart all services"
        echo "  logs    - Show recent logs"
        echo "  test    - Run quick integration test"
        echo ""
        echo "For frontend testing, use: $0 start"
        exit 1
        ;;
esac
