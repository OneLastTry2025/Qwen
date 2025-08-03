#!/usr/bin/env python3
"""
Problematic Endpoints Test for Qwen Clone Application
Tests the endpoints that showed issues in backend testing
"""

import requests
import json
import time

def test_problematic_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 Testing Problematic Endpoints in Detail")
    print("=" * 50)
    
    # Test 1: /models endpoint (timeout issues)
    print("\n1. Testing /models endpoint (known timeout issues)...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/models", timeout=60)
        end_time = time.time()
        
        print(f"   Response time: {end_time - start_time:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                models = data.get('models', [])
                print(f"   ✅ Success: Found {len(models)} models")
                print(f"   Models: {models}")
            else:
                print(f"   ❌ API returned error: {data.get('message')}")
        else:
            try:
                error_data = response.json()
                print(f"   ❌ HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: /history endpoint (NoneType errors)
    print("\n2. Testing /history endpoint (known NoneType errors)...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/history", timeout=30)
        end_time = time.time()
        
        print(f"   Response time: {end_time - start_time:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                history = data.get('history', [])
                print(f"   ✅ Success: Found {len(history)} chat sessions")
                if history:
                    print(f"   Sample history item: {history[0]}")
            else:
                print(f"   ❌ API returned error: {data.get('message')}")
        else:
            try:
                error_data = response.json()
                print(f"   ❌ HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: /chat with advanced options (timeout issues)
    print("\n3. Testing /chat with advanced options (known timeout issues)...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/chat",
            json={
                "prompt": "Tell me about artificial intelligence",
                "use_web_search": True,
                "agent_name": "Deep Research",
                "model_name": "Qwen-Plus"
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        end_time = time.time()
        
        print(f"   Response time: {end_time - start_time:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"   ✅ Success: Chat with options worked")
                print(f"   Response preview: {data.get('response', '')[:100]}...")
            else:
                print(f"   ❌ API returned error: {data.get('message')}")
        else:
            try:
                error_data = response.json()
                print(f"   ❌ HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Image generation (should work)
    print("\n4. Testing /image endpoint (should work)...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/image",
            json={"prompt": "A simple test image"},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        end_time = time.time()
        
        print(f"   Response time: {end_time - start_time:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"   ✅ Success: Image generation worked")
                print(f"   Image URL: {data.get('image_url', '')[:50]}...")
            else:
                print(f"   ❌ API returned error: {data.get('message')}")
        else:
            try:
                error_data = response.json()
                print(f"   ❌ HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 120 seconds")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    test_problematic_endpoints()