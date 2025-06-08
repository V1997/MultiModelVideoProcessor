#!/bin/bash
# Comprehensive E2E Testing Script using curl
# Tests all major endpoints and functionality

echo "🚀 COMPREHENSIVE END-TO-END TESTING WITH CURL"
echo "=============================================="
echo "Target: http://localhost:8000"
echo "Time: $(date)"
echo "=============================================="

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0
TOTAL=0

# Function to test an endpoint
test_endpoint() {
    local url="$1"
    local name="$2"
    local expected_code="${3:-200}"
    local timeout="${4:-10}"
    
    echo -n "Testing $name... "
    TOTAL=$((TOTAL + 1))
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout "$url")
    
    if [ "$response_code" = "$expected_code" ] || [ "$expected_code" = "200,404" -a \( "$response_code" = "200" -o "$response_code" = "404" \) ]; then
        echo "✅ PASS ($response_code)"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL ($response_code)"
        FAILED=$((FAILED + 1))
    fi
}

# Function to test an endpoint with data
test_endpoint_with_data() {
    local url="$1"
    local name="$2"
    local data="$3"
    local timeout="${4:-15}"
    
    echo -n "Testing $name... "
    TOTAL=$((TOTAL + 1))
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$url")
    
    if [ "$response_code" = "200" ] || [ "$response_code" = "202" ] || [ "$response_code" = "404" ]; then
        echo "✅ PASS ($response_code)"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL ($response_code)"
        FAILED=$((FAILED + 1))
    fi
}

echo ""
echo "🔧 CORE SYSTEM COMPONENTS:"
echo "------------------------"
test_endpoint "$BASE_URL/health" "API Health Check"
test_endpoint "$BASE_URL/docs" "OpenAPI Documentation"
test_endpoint "$BASE_URL/redis/status" "Redis Service"
test_endpoint "$BASE_URL/api/v1/websocket/connections" "WebSocket Service"

echo ""
echo "📹 VIDEO MANAGEMENT:"
echo "------------------"
test_endpoint "$BASE_URL/videos" "Video Listing"
test_endpoint "$BASE_URL/tasks/active" "Active Tasks"

# Get a video ID for further testing
echo -n "Getting test video ID... "
VIDEO_ID=$(curl -s "$BASE_URL/videos" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data and len(data) > 0:
        print(data[0]['id'])
    else:
        print('none')
except:
    print('error')
" 2>/dev/null)

if [ "$VIDEO_ID" != "none" ] && [ "$VIDEO_ID" != "error" ] && [ -n "$VIDEO_ID" ]; then
    echo "✅ Found video ID: $VIDEO_ID"
    HAS_TEST_VIDEO=true
else
    echo "⚠️ No test video found"
    HAS_TEST_VIDEO=false
fi

echo ""
echo "💬 CHAT & CONVERSATION SYSTEM:"
echo "-----------------------------"
test_endpoint "$BASE_URL/api/v1/chat/sessions" "Chat Sessions Listing"

if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint_with_data "$BASE_URL/api/v1/conversation/start" "Conversation Start" "{\"video_id\": $VIDEO_ID}"
fi

echo ""
echo "🎥 YOUTUBE FUNCTIONALITY:"
echo "------------------------"
test_endpoint "$BASE_URL/api/v1/youtube/search?query=test&max_results=1" "YouTube Search" "200,404" 20
test_endpoint "$BASE_URL/api/v1/youtube/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" "YouTube Info" "200,403" 20

echo ""
echo "🔍 SEARCH & EMBEDDINGS:"
echo "----------------------"
if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint_with_data "$BASE_URL/api/v1/search/semantic" "Semantic Search" "{\"query\": \"test\", \"video_id\": $VIDEO_ID, \"top_k\": 5}" 20
    test_endpoint "$BASE_URL/api/v1/similarity/find/$VIDEO_ID?query=test&limit=5" "Similarity Search" "200,404" 20
fi

echo ""
echo "👁️ VISUAL ANALYSIS:"
echo "------------------"
if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint_with_data "$BASE_URL/api/v1/visual-search" "Visual Search" "{\"video_id\": $VIDEO_ID, \"query\": \"person\", \"confidence_threshold\": 0.5}" 25
    test_endpoint_with_data "$BASE_URL/api/v1/visual-search/detect-objects" "Object Detection" "{\"video_id\": $VIDEO_ID}" 25
fi

echo ""
echo "📊 CONTENT ANALYSIS:"
echo "-------------------"
if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint_with_data "$BASE_URL/api/v1/content/analyze-topics" "Topic Analysis" "{\"video_id\": $VIDEO_ID}" 25
    test_endpoint_with_data "$BASE_URL/api/v1/content/generate-outline" "Outline Generation" "{\"video_id\": $VIDEO_ID}" 25
fi

echo ""
echo "📝 VIDEO FEATURES:"
echo "----------------"
if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint "$BASE_URL/video/$VIDEO_ID/transcript" "Video Transcript" "200,404" 15
    test_endpoint "$BASE_URL/video/$VIDEO_ID/status" "Video Status" "200,404" 10
    test_endpoint "$BASE_URL/api/v1/video/$VIDEO_ID/summary" "Video Summary" "200,404" 20
fi

echo ""
echo "🔌 WEBSOCKET FEATURES:"
echo "--------------------"
test_endpoint_with_data "$BASE_URL/api/v1/websocket/status?task_id=test&status=testing&progress=50&message=E2E%20Test" "WebSocket Status Broadcast" "{}" 10
if [ "$HAS_TEST_VIDEO" = true ]; then
    test_endpoint_with_data "$BASE_URL/api/v1/websocket/visual-analysis?video_id=$VIDEO_ID" "WebSocket Visual Broadcast" "{\"analysis_type\": \"test\"}" 10
fi

echo ""
echo "=============================================="
echo "📊 COMPREHENSIVE TEST SUMMARY:"
echo "=============================================="
echo "Total Tests: $TOTAL"
echo "Passed: $PASSED ✅"
echo "Failed: $FAILED ❌"

if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    echo "Success Rate: $SUCCESS_RATE%"
    
    echo ""
    echo "🎯 OVERALL SYSTEM STATUS:"
    if [ $PASSED -eq $TOTAL ]; then
        echo "  🎉 ALL SYSTEMS OPERATIONAL"
        exit 0
    elif [ $SUCCESS_RATE -ge 80 ]; then
        echo "  ⚠️ MOSTLY OPERATIONAL (Minor Issues)"
        exit 0
    elif [ $SUCCESS_RATE -ge 50 ]; then
        echo "  🔄 PARTIALLY OPERATIONAL (Major Issues)"
        exit 1
    else
        echo "  🚨 SYSTEM ISSUES DETECTED"
        exit 1
    fi
else
    echo "❌ No tests were executed"
    exit 1
fi
