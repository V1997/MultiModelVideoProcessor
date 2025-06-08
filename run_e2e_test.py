#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for MultiModelVideo Application
"""

import requests
import json
import time
from datetime import datetime

def main():
    print("COMPREHENSIVE END-TO-END TESTING")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = 'http://localhost:8000'
    session = requests.Session()
    session.timeout = 15
    
    tests = []
    test_video_id = None
    
    def test_endpoint(name, method, url, data=None, expected_codes=[200], timeout=15):
        nonlocal tests
        try:
            print(f"Testing {name}...", end=" ", flush=True)
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = session.post(url, json=data, timeout=timeout)
            
            elapsed = time.time() - start_time
            
            if response.status_code in expected_codes:
                print(f"PASS ({response.status_code}) - {elapsed:.2f}s")
                tests.append((name, True, response.status_code, elapsed))
                return response
            else:
                print(f"FAIL ({response.status_code}) - {elapsed:.2f}s")
                tests.append((name, False, response.status_code, elapsed))
                return None
        except requests.exceptions.Timeout:
            print(f"TIMEOUT (>{timeout}s)")
            tests.append((name, False, 'TIMEOUT', timeout))
            return None
        except Exception as e:
            print(f"ERROR: {str(e)[:50]}")
            tests.append((name, False, 'ERROR', 0))
            return None
    
    print("\nCORE SYSTEM TESTS:")
    test_endpoint('API Health', 'GET', f'{base_url}/health')
    test_endpoint('OpenAPI Docs', 'GET', f'{base_url}/docs')
    test_endpoint('Redis Status', 'GET', f'{base_url}/redis/status')
    test_endpoint('WebSocket Connections', 'GET', f'{base_url}/api/v1/websocket/connections')
    
    print("\nVIDEO MANAGEMENT:")
    videos_response = test_endpoint('Video Listing', 'GET', f'{base_url}/videos')
    if videos_response and videos_response.status_code == 200:
        try:
            videos_data = videos_response.json()
            if videos_data and len(videos_data) > 0:
                test_video_id = videos_data[0]['id']
                print(f"    Found {len(videos_data)} videos, using ID {test_video_id} for tests")
            else:
                print("    No videos found in database")
        except:
            pass
    
    test_endpoint('Active Tasks', 'GET', f'{base_url}/tasks/active')
    
    print("\nCHAT SYSTEM:")
    test_endpoint('Chat Sessions', 'GET', f'{base_url}/api/v1/chat/sessions')
    
    if test_video_id:
        test_endpoint('Start Conversation', 'POST', f'{base_url}/api/v1/conversation/start', 
                     {'video_id': test_video_id}, [200, 201])
    
    print("\nYOUTUBE FUNCTIONALITY:")
    test_endpoint('YouTube Search', 'GET', f'{base_url}/api/v1/youtube/search?query=test&max_results=1', 
                 expected_codes=[200, 403, 404], timeout=20)
    
    print("\nSEARCH & EMBEDDINGS:")
    if test_video_id:
        test_endpoint('Semantic Search', 'POST', f'{base_url}/api/v1/search/semantic',
                     {'query': 'test', 'video_id': test_video_id, 'top_k': 5}, [200, 404], 20)
    
    print("\nVISUAL ANALYSIS:")
    if test_video_id:
        test_endpoint('Visual Search', 'POST', f'{base_url}/api/v1/visual-search',
                     {'video_id': test_video_id, 'query': 'person', 'confidence_threshold': 0.5}, 
                     [200, 404], 25)
    
    print("\nCONTENT ANALYSIS:")
    if test_video_id:
        test_endpoint('Topic Analysis', 'POST', f'{base_url}/api/v1/content/analyze-topics',
                     {'video_id': test_video_id}, [200, 202, 404], 25)
    
    print("\nVIDEO FEATURES:")
    if test_video_id:
        test_endpoint('Video Transcript', 'GET', f'{base_url}/video/{test_video_id}/transcript', 
                     expected_codes=[200, 404])
        test_endpoint('Video Status', 'GET', f'{base_url}/video/{test_video_id}/status',
                     expected_codes=[200, 404])
    
    print("\nWEBSOCKET FEATURES:")
    test_endpoint('WebSocket Status Broadcast', 'POST', 
                 f'{base_url}/api/v1/websocket/status?task_id=e2e_test&status=testing&progress=50&message=E2E%20Test')
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    total = len(tests)
    passed = sum(1 for _, success, _, _ in tests if success)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDETAILED RESULTS:")
    for name, success, code, elapsed in tests:
        status = 'PASS' if success else 'FAIL'
        print(f"{status} {name}: {code} ({elapsed:.2f}s)")
    
    print("\nSYSTEM STATUS:")
    if passed == total:
        print("ALL SYSTEMS OPERATIONAL")
    elif passed >= total * 0.8:
        print("MOSTLY OPERATIONAL")
    else:
        print("SYSTEM ISSUES DETECTED")
    
    return passed, total

if __name__ == "__main__":
    main()
