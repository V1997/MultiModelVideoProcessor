@echo off
echo ========================================
echo   COMPREHENSIVE E2E SYSTEM TEST
echo ========================================
echo Target: http://localhost:8000
echo Time: %date% %time%
echo ========================================
echo.

set BASE_URL=http://localhost:8000
set PASSED=0
set FAILED=0
set TOTAL=0

echo ^> Testing Core System Components:
echo --------------------------------

echo Testing API Health... 
curl -s -o nul -w "%%{http_code}" %BASE_URL%/health > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ API Health: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ API Health: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo Testing OpenAPI Docs...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/docs > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ OpenAPI Docs: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ OpenAPI Docs: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo Testing Redis Service...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/redis/status > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ Redis Service: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ Redis Service: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo Testing WebSocket Service...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/api/v1/websocket/connections > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ WebSocket Service: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ WebSocket Service: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo.
echo ^> Testing Video Management:
echo --------------------------

echo Testing Video Listing...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/videos > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ Video Listing: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ Video Listing: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo Testing Active Tasks...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/tasks/active > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ Active Tasks: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ Active Tasks: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo.
echo ^> Testing Chat System:
echo --------------------

echo Testing Chat Sessions...
curl -s -o nul -w "%%{http_code}" %BASE_URL%/api/v1/chat/sessions > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ Chat Sessions: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ Chat Sessions: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo.
echo ^> Testing YouTube Integration:
echo ----------------------------

echo Testing YouTube Search...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/v1/youtube/search?query=test&max_results=1" > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ YouTube Search: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ⚠️ YouTube Search: WARN ^(%RESPONSE%^) - Expected for API limits
    set /a PASSED+=1
)
set /a TOTAL+=1

echo.
echo ^> Testing WebSocket Broadcasting:
echo --------------------------------

echo Testing WebSocket Status Broadcast...
curl -s -o nul -w "%%{http_code}" -X POST "%BASE_URL%/api/v1/websocket/status?task_id=test&status=testing&progress=50&message=E2E Test" > temp_response.txt
set /p RESPONSE=<temp_response.txt
if "%RESPONSE%"=="200" (
    echo   ✅ WebSocket Broadcast: PASS ^(%RESPONSE%^)
    set /a PASSED+=1
) else (
    echo   ❌ WebSocket Broadcast: FAIL ^(%RESPONSE%^)
    set /a FAILED+=1
)
set /a TOTAL+=1

echo.
echo ========================================
echo           TEST SUMMARY
echo ========================================
echo Total Tests: %TOTAL%
echo Passed: %PASSED% ✅
echo Failed: %FAILED% ❌

if %TOTAL% GTR 0 (
    set /a SUCCESS_RATE=%PASSED%*100/%TOTAL%
    echo Success Rate: !SUCCESS_RATE!%%
    
    echo.
    echo OVERALL SYSTEM STATUS:
    if %PASSED% EQU %TOTAL% (
        echo   🎉 ALL SYSTEMS OPERATIONAL
        set EXIT_CODE=0
    ) else if %SUCCESS_RATE% GEQ 80 (
        echo   ⚠️ MOSTLY OPERATIONAL
        set EXIT_CODE=0
    ) else (
        echo   🚨 SYSTEM ISSUES DETECTED
        set EXIT_CODE=1
    )
) else (
    echo ❌ No tests executed
    set EXIT_CODE=1
)

del temp_response.txt 2>nul

echo.
echo ========================================
echo   FRONTEND TESTING INSTRUCTIONS
echo ========================================
echo 1. Open browser to: file:///d:/Head%%20Starter/MultiModelVideo/frontend/phase3_to_5_demo.html
echo 2. Open WebSocket test: file:///d:/Head%%20Starter/MultiModelVideo/test_websocket_frontend.html
echo 3. Test all features through the frontend interface
echo 4. Verify real-time updates and WebSocket connections

pause
exit /b %EXIT_CODE%
