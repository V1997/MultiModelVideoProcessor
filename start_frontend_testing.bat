@echo off
REM Frontend Testing - Service Startup Script for Windows
REM This script starts all required services for full MultiModelVideo frontend testing

echo 🚀 Starting MultiModelVideo Services for Frontend Testing
echo =========================================================

setlocal EnableDelayedExpansion

REM Function to check if a service is running
:check_service
set service_name=%1
set port=%2
set url=%3

echo Checking %service_name% on port %port%...

curl -s --max-time 5 "%url%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ %service_name% is running
    exit /b 0
) else (
    echo ❌ %service_name% is not responding
    exit /b 1
)

REM Main execution
if "%1"=="start" goto start_services
if "%1"=="stop" goto stop_services
if "%1"=="status" goto check_status
if "%1"=="restart" goto restart_services
if "%1"=="test" goto test_services
goto show_usage

:start_services
echo Starting all services for frontend testing...
echo.

REM Setup environment
call :setup_environment

echo Starting Backend API Server...
echo.
start /b "Backend API" cmd /c "cd backend && python -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Check if backend started
curl -s --max-time 5 "http://127.0.0.1:8001/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API started successfully
) else (
    echo ❌ Backend API failed to start
)

echo.
echo Starting Frontend HTTP Server...
cd frontend
start /b "Frontend Server" cmd /c "python -m http.server 8080"
cd ..

REM Wait for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo 🎉 All services started successfully!
echo.
echo 📋 Service URLs:
echo 🔗 Backend API: http://127.0.0.1:8001
echo 🔗 API Docs: http://127.0.0.1:8001/docs
echo 🔗 Frontend: http://localhost:8080/phase3_to_5_demo.html
echo 🔗 Health Check: http://127.0.0.1:8001/health
echo.
echo 🧪 Frontend Testing Commands:
echo • Test API connection: curl http://127.0.0.1:8001/health
echo • Open frontend: start http://localhost:8080/phase3_to_5_demo.html
echo • API Documentation: start http://127.0.0.1:8001/docs
echo.
echo 🛑 To stop all services: %0 stop
goto end

:stop_services
echo Stopping all services...

REM Kill processes by window title
taskkill /f /fi "WindowTitle eq Backend API*" >nul 2>&1
taskkill /f /fi "WindowTitle eq Frontend Server*" >nul 2>&1

REM Kill processes by port
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo ✅ All services stopped
goto end

:check_status
echo Checking service status...
echo.

curl -s --max-time 5 "http://127.0.0.1:8001/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is running on port 8001
) else (
    echo ❌ Backend API is not responding on port 8001
)

curl -s --max-time 5 "http://localhost:8080" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend Server is running on port 8080
) else (
    echo ❌ Frontend Server is not responding on port 8080
)

echo.
echo Active processes on ports 8001 and 8080:
netstat -ano | findstr ":8001\|:8080"
goto end

:restart_services
echo Restarting all services...
call :stop_services
timeout /t 2 /nobreak >nul
call :start_services
goto end

:test_services
echo Running quick frontend integration test...
echo.

echo Testing backend health...
curl -s http://127.0.0.1:8001/health
echo.

echo Testing YouTube search endpoint...
curl -s -X POST http://127.0.0.1:8001/api/v1/youtube/search -H "Content-Type: application/json" -d "{\"query\": \"test\", \"max_results\": 2}"
goto end

:setup_environment
echo Setting up environment...

if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env >nul
        echo ✅ .env file created
    ) else (
        echo Creating basic .env file...
        (
            echo # Database Configuration
            echo DATABASE_URL=sqlite:///./multimodal_video.db
            echo DB_HOST=localhost
            echo DB_PORT=5432
            echo.
            echo # Redis Configuration (Optional^)
            echo REDIS_URL=redis://localhost:6379/0
            echo REDIS_HOST=localhost
            echo REDIS_PORT=6379
            echo.
            echo # API Configuration
            echo API_HOST=127.0.0.1
            echo API_PORT=8001
            echo CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080
            echo.
            echo # File Storage
            echo UPLOAD_DIR=./uploads
            echo PROCESSED_DIR=./processed
            echo FRAMES_DIR=./frames
            echo.
            echo # Development
            echo DEBUG=True
            echo LOG_LEVEL=INFO
        ) > .env
        echo ✅ Basic .env file created
    )
) else (
    echo ✅ .env file already exists
)

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "processed" mkdir processed
if not exist "frames" mkdir frames
if not exist "temp" mkdir temp
if not exist "vector_db" mkdir vector_db

echo ✅ Directories created
echo.
exit /b

:show_usage
echo Usage: %0 {start^|stop^|status^|restart^|test}
echo.
echo Commands:
echo   start   - Start all services for frontend testing
echo   stop    - Stop all running services
echo   status  - Check service status
echo   restart - Restart all services
echo   test    - Run quick integration test
echo.
echo For frontend testing, use: %0 start
echo.
echo Quick Start:
echo 1. %0 start
echo 2. Open http://localhost:8080/phase3_to_5_demo.html in your browser
echo 3. Test the YouTube search and chat features

:end
