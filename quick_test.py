import requests
import json

def quick_test():
    base_url = "http://localhost:8000"
    
    print("Testing MultiModelVideo API...")
    
    # Test health
    try:
        r = requests.get(f"{base_url}/health")
        print(f"Health: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Services: {data.get('services', {})}")
    except Exception as e:
        print(f"Health test failed: {e}")
    
    # Test videos
    try:
        r = requests.get(f"{base_url}/videos")
        print(f"Videos: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            videos = data.get("videos", [])
            print(f"Found {len(videos)} videos")
    except Exception as e:
        print(f"Videos test failed: {e}")
    
    # Test YouTube search
    try:
        r = requests.post(f"{base_url}/api/v1/youtube/search", 
                         json={"query": "test", "max_results": 1})
        print(f"YouTube Search: {r.status_code}")
    except Exception as e:
        print(f"YouTube search failed: {e}")
    
    print("Test completed!")

if __name__ == "__main__":
    quick_test()
