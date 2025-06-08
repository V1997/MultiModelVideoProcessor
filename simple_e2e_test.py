#!/usr/bin/env python3
"""
Simple E2E Test for MultiModelVideo Application
"""

import requests
import json
import time

def test_endpoints():
    """Test basic endpoints"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/health",
        "/videos", 
        "/redis/status",
        "/api/v1/conversation/list",
        "/api/v1/chat/models",
        "/api/v1/embeddings/status",
        "/api/v1/content/topics"
    ]
    
    print("=" * 50)
    print("MULTIMODELVIDEO E2E TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Testing {endpoint}...", end=" ")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("PASS")
                passed += 1
            else:
                print(f"FAIL (Status: {response.status_code})")
                failed += 1
                
        except Exception as e:
            print(f"FAIL (Error: {str(e)})")
            failed += 1
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = test_endpoints()
    if success:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED!")
