#!/usr/bin/env python3
"""
Frontend Health Monitor - Quick validation for ongoing monitoring
Run this script to quickly validate frontend-backend integration health
"""

import requests
import json
import time
from pathlib import Path

class FrontendHealthMonitor:
    def __init__(self, backend_url="http://localhost:8001"):
        self.backend_url = backend_url
        self.frontend_file = Path("frontend/phase3_to_5_demo.html")
        
    def check_backend_health(self):
        """Quick backend health check"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_critical_endpoints(self):
        """Test critical endpoints for frontend"""
        endpoints = [
            "/",
            "/videos",
            "/docs",
            "/api/v1/youtube/search"
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                if endpoint == "/api/v1/youtube/search":
                    response = requests.post(f"{self.backend_url}{endpoint}", 
                                           json={"query": "test"}, timeout=5)
                else:
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                results[endpoint] = response.status_code
            except Exception as e:
                results[endpoint] = f"ERROR: {str(e)}"
        
        return results
    
    def check_frontend_file(self):
        """Verify frontend file exists and basic structure"""
        if not self.frontend_file.exists():
            return False, "Frontend file not found"
        
        try:
            content = self.frontend_file.read_text(encoding='utf-8')
            checks = {
                "HTML5 DOCTYPE": "<!DOCTYPE html>" in content,
                "Tailwind CSS": "tailwindcss" in content,
                "Axios Library": "axios" in content,
                "Socket.IO": "socket.io" in content,
                "API Configuration": "localhost:" in content or "127.0.0.1:" in content
            }
            return True, checks
        except Exception as e:
            return False, f"Error reading frontend: {str(e)}"
    
    def run_health_check(self):
        """Run complete health check"""
        print("🏥 FRONTEND HEALTH MONITOR")
        print("=" * 50)
        
        # Backend health
        backend_healthy = self.check_backend_health()
        status = "✅ HEALTHY" if backend_healthy else "❌ UNHEALTHY"
        print(f"Backend Status: {status}")
        
        if backend_healthy:
            # Critical endpoints
            endpoints = self.check_critical_endpoints()
            print("\n🔌 Critical Endpoints:")
            for endpoint, status_code in endpoints.items():
                if isinstance(status_code, int) and 200 <= status_code < 300:
                    print(f"  ✅ {endpoint}: {status_code}")
                else:
                    print(f"  ❌ {endpoint}: {status_code}")
        
        # Frontend file check
        frontend_ok, frontend_info = self.check_frontend_file()
        print(f"\n📁 Frontend File: {'✅ OK' if frontend_ok else '❌ ERROR'}")
        
        if frontend_ok and isinstance(frontend_info, dict):
            for check, passed in frontend_info.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check}")
        elif not frontend_ok:
            print(f"  Error: {frontend_info}")
        
        # Overall status
        overall_healthy = backend_healthy and frontend_ok
        print(f"\n🎯 Overall Status: {'✅ SYSTEM HEALTHY' if overall_healthy else '❌ ISSUES DETECTED'}")
        
        return overall_healthy

if __name__ == "__main__":
    monitor = FrontendHealthMonitor()
    monitor.run_health_check()
