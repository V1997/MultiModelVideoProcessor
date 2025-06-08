#!/usr/bin/env python3
"""
Quick End-to-End System Status Check
"""

import requests
import time
import sys
from datetime import datetime

def test_endpoint(url, name, timeout=5):
    """Test a single endpoint with timeout"""
    try:
        print(f"Testing {name}...", end=" ", flush=True)
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ PASS ({response.status_code}) - {elapsed:.2f}s")
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"    Found {len(data)} items")
                elif isinstance(data, dict):
                    if 'active_connections' in data:
                        print(f"    Active connections: {data['active_connections']}")
                    elif 'status' in data:
                        print(f"    Status: {data['status']}")
            except:
                pass
            return True
        else:
            print(f"⚠️ WARN ({response.status_code}) - {elapsed:.2f}s")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT (>{timeout}s)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:50]}")
        return False

def main():
    print("🚀 QUICK END-TO-END SYSTEM STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Core system tests
    print("\n🔧 CORE SYSTEM COMPONENTS:")
    core_tests = [
        (f"{base_url}/health", "API Health"),
        (f"{base_url}/docs", "OpenAPI Docs"),
        (f"{base_url}/redis/status", "Redis Service"),
        (f"{base_url}/api/v1/websocket/connections", "WebSocket Service"),
    ]
    
    core_results = []
    for url, name in core_tests:
        result = test_endpoint(url, name, timeout=10)
        core_results.append(result)
    
    # Video system tests
    print("\n📹 VIDEO SYSTEM:")
    video_tests = [
        (f"{base_url}/videos", "Video Listing"),
        (f"{base_url}/tasks/active", "Task Management"),
    ]
    
    video_results = []
    for url, name in video_tests:
        result = test_endpoint(url, name, timeout=15)
        video_results.append(result)
    
    # Chat and API tests
    print("\n💬 CHAT & API SYSTEM:")
    api_tests = [
        (f"{base_url}/api/v1/chat/sessions", "Chat Sessions"),
        (f"{base_url}/api/v1/youtube/search?query=test&max_results=1", "YouTube Search"),
    ]
    
    api_results = []
    for url, name in api_tests:
        result = test_endpoint(url, name, timeout=20)
        api_results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    all_results = core_results + video_results + api_results
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Component status
    print(f"\nCOMPONENT STATUS:")
    components = [
        ("Core System", sum(core_results), len(core_results)),
        ("Video System", sum(video_results), len(video_results)),
        ("API System", sum(api_results), len(api_results)),
    ]
    
    for name, passed_count, total_count in components:
        status = "✅" if passed_count == total_count else "⚠️" if passed_count > 0 else "❌"
        print(f"  {status} {name}: {passed_count}/{total_count}")
    
    # Overall status
    print(f"\n🎯 OVERALL STATUS:")
    if passed == total:
        print("  🎉 ALL SYSTEMS OPERATIONAL")
        return True
    elif passed >= total * 0.8:
        print("  ⚠️ MOSTLY OPERATIONAL")
        return True
    else:
        print("  🚨 SYSTEM ISSUES DETECTED")
        return False

if __name__ == "__main__":
    try:
        success = main()
        print(f"\n{'✅ SYSTEM READY' if success else '❌ SYSTEM ISSUES'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
