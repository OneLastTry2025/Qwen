#!/usr/bin/env python3
"""
Backend API Testing for Qwen Clone Application
Tests all API endpoints: /chat, /image, /history, /model, /models
"""

import requests
import sys
import json
from datetime import datetime

class QwenAPITester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.chat_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if 'status' in response_data:
                        print(f"   Response Status: {response_data['status']}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_model_info(self):
        """Test GET /model endpoint"""
        success, response = self.run_test(
            "Get Current Model Info",
            "GET",
            "/model",
            200
        )
        if success and 'model_name' in response:
            print(f"   Current Model: {response['model_name']}")
        return success

    def test_available_models(self):
        """Test GET /models endpoint - known to have timeout issues"""
        success, response = self.run_test(
            "Get Available Models",
            "GET",
            "/models",
            200,
            timeout=60  # Longer timeout for this problematic endpoint
        )
        if success and 'models' in response:
            print(f"   Found {len(response['models'])} models: {response['models'][:3]}...")
        return success

    def test_chat_basic(self):
        """Test POST /chat endpoint with basic message"""
        success, response = self.run_test(
            "Basic Chat Message",
            "POST",
            "/chat",
            200,
            data={"prompt": "Hello, this is a test message. Please respond briefly."}
        )
        if success and 'chat_id' in response:
            self.chat_id = response['chat_id']
            print(f"   Chat ID: {self.chat_id}")
            print(f"   Response Preview: {response.get('response', '')[:100]}...")
        return success

    def test_chat_continuation(self):
        """Test POST /chat endpoint with existing chat_id"""
        if not self.chat_id:
            print("⚠️  Skipping chat continuation test - no chat_id available")
            return True
            
        success, response = self.run_test(
            "Chat Continuation",
            "POST",
            "/chat",
            200,
            data={
                "prompt": "What was my previous message?",
                "chat_id": self.chat_id
            }
        )
        if success:
            print(f"   Response Preview: {response.get('response', '')[:100]}...")
        return success

    def test_chat_with_options(self):
        """Test POST /chat endpoint with various options"""
        success, response = self.run_test(
            "Chat with Options",
            "POST",
            "/chat",
            200,
            data={
                "prompt": "Tell me about AI",
                "use_web_search": True,
                "agent_name": "Deep Research",
                "model_name": "Qwen-Plus"
            }
        )
        if success:
            print(f"   Response Preview: {response.get('response', '')[:100]}...")
        return success

    def test_image_generation(self):
        """Test POST /image endpoint"""
        success, response = self.run_test(
            "Image Generation",
            "POST",
            "/image",
            200,
            data={"prompt": "A simple test image of a cat"},
            timeout=120  # Image generation takes longer
        )
        if success and 'image_url' in response:
            print(f"   Image URL: {response['image_url'][:50]}...")
        return success

    def test_chat_history(self):
        """Test GET /history endpoint - known to have NoneType errors"""
        success, response = self.run_test(
            "Get Chat History",
            "GET",
            "/history",
            200,
            timeout=30
        )
        if success and 'history' in response:
            print(f"   Found {len(response['history'])} chat sessions")
            if response['history']:
                print(f"   Sample: {response['history'][0]}")
        return success

    def test_invalid_endpoints(self):
        """Test error handling with invalid requests"""
        print(f"\n🔍 Testing Error Handling...")
        
        # Test missing prompt
        success, _ = self.run_test(
            "Chat without prompt",
            "POST",
            "/chat",
            400,
            data={}
        )
        
        # Test invalid endpoint
        success2, _ = self.run_test(
            "Invalid endpoint",
            "GET",
            "/nonexistent",
            404
        )
        
        return success and success2

def main():
    print("🚀 Starting Qwen Clone API Tests")
    print("=" * 50)
    
    tester = QwenAPITester()
    
    # Test sequence - start with working endpoints first
    test_results = []
    
    # 1. Test working endpoints first
    print("\n📋 PHASE 1: Testing Working Endpoints")
    test_results.append(("Model Info", tester.test_model_info()))
    test_results.append(("Basic Chat", tester.test_chat_basic()))
    test_results.append(("Chat Continuation", tester.test_chat_continuation()))
    test_results.append(("Chat with Options", tester.test_chat_with_options()))
    
    # 2. Test problematic endpoints
    print("\n📋 PHASE 2: Testing Problematic Endpoints")
    test_results.append(("Available Models", tester.test_available_models()))
    test_results.append(("Chat History", tester.test_chat_history()))
    
    # 3. Test image generation (may be slow)
    print("\n📋 PHASE 3: Testing Image Generation")
    test_results.append(("Image Generation", tester.test_image_generation()))
    
    # 4. Test error handling
    print("\n📋 PHASE 4: Testing Error Handling")
    test_results.append(("Error Handling", tester.test_invalid_endpoints()))
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())