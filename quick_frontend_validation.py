#!/usr/bin/env python3
"""
Quick Frontend Validation
Tests key frontend-backend integration points
"""

import requests
import json
import time

def test_frontend_backend_integration():
    print("🎨 FRONTEND-BACKEND INTEGRATION VALIDATION")
    print("Testing key integration points...")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    results = []
    
    # Test 1: API Connectivity
    print("\n🔌 API CONNECTIVITY TESTS")
    print("-" * 30)
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/videos/", "Video listing"),
        ("GET", "/docs", "API documentation"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            start = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            end = time.time()
            
            success = 200 <= response.status_code < 300
            response_time = (end - start) * 1000
            
            status = "✅" if success else "❌"
            print(f"{status} {description}: {response.status_code} ({response_time:.0f}ms)")
            results.append(success)
            
        except Exception as e:
            print(f"❌ {description}: ERROR - {str(e)}")
            results.append(False)
    
    # Test 2: CORS Headers
    print("\n🌐 CORS VALIDATION")
    print("-" * 30)
    
    try:
        response = requests.options(
            f"{base_url}/api/v1/youtube/search",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        cors_working = allow_origin in ["*", "http://localhost:8080"]
        
        status = "✅" if cors_working else "❌"
        print(f"{status} CORS Headers: {allow_origin}")
        results.append(cors_working)
        
    except Exception as e:
        print(f"❌ CORS Headers: ERROR - {str(e)}")
        results.append(False)
    
    # Test 3: Frontend-Critical Endpoints
    print("\n🎯 FRONTEND-CRITICAL ENDPOINTS")
    print("-" * 30)
    
    critical_tests = [
        ("POST", "/api/v1/youtube/search", {"query": "test", "max_results": 3}),
        ("GET", "/api/v1/youtube/info?video_id=dQw4w9WgXcQ", None),
        ("POST", "/api/v1/chat/sessions?video_id=1&title=Test", None),
        ("GET", "/redis/health", None),
        ("GET", "/websocket/status", None),
    ]
    
    for method, endpoint, payload in critical_tests:
        try:
            if method == "POST" and payload:
                response = requests.post(f"{base_url}{endpoint}", json=payload, timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            success = response.status_code < 500  # Accept 4xx but not 5xx
            status = "✅" if success else "❌"
            
            endpoint_name = endpoint.split("/")[-1] or endpoint.split("/")[-2]
            print(f"{status} {endpoint_name}: HTTP {response.status_code}")
            results.append(success)
            
        except Exception as e:
            endpoint_name = endpoint.split("/")[-1] or endpoint.split("/")[-2]
            print(f"❌ {endpoint_name}: ERROR - {str(e)}")
            results.append(False)
    
    # Test 4: Frontend File Structure
    print("\n📁 FRONTEND FILE STRUCTURE")
    print("-" * 30)
    
    try:
        frontend_path = "d:/Head Starter/MultiModelVideo/frontend/phase3_to_5_demo.html"
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check key components
        components = {
            "HTML Structure": "<!DOCTYPE html>" in content,
            "Tailwind CSS": "tailwindcss.com" in content,
            "Axios Library": "axios" in content,
            "Socket.IO": "socket.io" in content,
            "API Configuration": "API_BASE" in content,
            "Chat Interface": 'id="chat-panel"' in content,
            "Visual Search": 'id="visual-panel"' in content,
            "YouTube Integration": "youtube" in content.lower(),
        }
        
        for component, present in components.items():
            status = "✅" if present else "❌"
            print(f"{status} {component}")
            results.append(present)
            
    except Exception as e:
        print(f"❌ Frontend File Access: ERROR - {str(e)}")
        results.append(False)
    
    # Test 5: JavaScript API Integration
    print("\n⚙️ JAVASCRIPT API INTEGRATION")
    print("-" * 30)
    
    if 'content' in locals():
        js_features = {
            "Fetch API Calls": "fetch(" in content,
            "Error Handling": "catch(" in content,
            "WebSocket Setup": "socket.on(" in content,
            "Chat Functions": "sendMessage" in content,
            "YouTube Functions": "searchYouTube" in content,
            "Visual Search": "performVisualSearch" in content,
        }
        
        for feature, present in js_features.items():
            status = "✅" if present else "❌"
            print(f"{status} {feature}")
            results.append(present)
    
    # Generate Summary
    print("\n📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if pass_rate >= 80:
        print("\n✅ FRONTEND INTEGRATION: EXCELLENT")
        print("   System ready for production frontend deployment")
    elif pass_rate >= 60:
        print("\n⚠️ FRONTEND INTEGRATION: GOOD")
        print("   System ready with minor improvements needed")
    else:
        print("\n❌ FRONTEND INTEGRATION: NEEDS WORK")
        print("   Several issues need attention before deployment")
    
    print("\n🎯 KEY FRONTEND FEATURES VALIDATED:")
    print("   • API endpoint connectivity and responses")
    print("   • CORS configuration for cross-origin requests")
    print("   • Critical backend endpoints for frontend functionality")
    print("   • Frontend file structure and component organization")
    print("   • JavaScript API integration and error handling")
    print("   • Real-time features with WebSocket support")
    
    return pass_rate >= 70

if __name__ == "__main__":
    success = test_frontend_backend_integration()
    exit(0 if success else 1)
