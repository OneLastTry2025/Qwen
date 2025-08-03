#!/usr/bin/env python3
"""
Frontend Integration Test for Qwen Clone Application
Tests the chat functionality through direct API calls to simulate frontend behavior
"""

import requests
import json
import time

class QwenFrontendTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def test_frontend_loading(self):
        """Test if the frontend HTML loads correctly"""
        print("🔍 Testing Frontend Loading...")
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                html_content = response.text
                
                # Check for key UI elements in HTML
                required_elements = [
                    'id="app"',
                    'id="chat-input"',
                    'id="sidebar"',
                    'id="model-selector-button"',
                    'script.js',
                    'Qwen Clone'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ Frontend HTML loads correctly with all required elements")
                    self.tests_passed += 1
                else:
                    print(f"❌ Missing elements in HTML: {missing_elements}")
                
                self.tests_run += 1
                return len(missing_elements) == 0
            else:
                print(f"❌ Frontend failed to load: {response.status_code}")
                self.tests_run += 1
                return False
                
        except Exception as e:
            print(f"❌ Error loading frontend: {str(e)}")
            self.tests_run += 1
            return False

    def test_static_assets(self):
        """Test if static assets (JS, CSS) load correctly"""
        print("🔍 Testing Static Assets...")
        assets_to_test = [
            "/assets/script.js",
            "/assets/style.css"
        ]
        
        all_assets_loaded = True
        for asset in assets_to_test:
            try:
                response = requests.get(f"{self.base_url}{asset}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {asset} loads correctly")
                else:
                    print(f"❌ {asset} failed to load: {response.status_code}")
                    all_assets_loaded = False
            except Exception as e:
                print(f"❌ Error loading {asset}: {str(e)}")
                all_assets_loaded = False
        
        self.tests_run += 1
        if all_assets_loaded:
            self.tests_passed += 1
        return all_assets_loaded

    def test_chat_workflow_simulation(self):
        """Simulate a complete chat workflow as the frontend would do"""
        print("🔍 Testing Complete Chat Workflow Simulation...")
        
        try:
            # Step 1: Load model info (as frontend does on startup)
            print("  Step 1: Loading model info...")
            model_response = requests.get(f"{self.base_url}/model", timeout=10)
            if model_response.status_code != 200:
                print(f"❌ Model info failed: {model_response.status_code}")
                self.tests_run += 1
                return False
            
            model_data = model_response.json()
            print(f"  ✅ Model loaded: {model_data.get('model_name', 'Unknown')}")
            
            # Step 2: Send a chat message (as frontend does when user submits)
            print("  Step 2: Sending chat message...")
            chat_payload = {
                "prompt": "Hello! This is a frontend integration test. Please respond briefly.",
                "chat_id": None,
                "use_web_search": False,
                "agent_name": None,
                "model_name": None
            }
            
            chat_response = requests.post(
                f"{self.base_url}/chat",
                json=chat_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if chat_response.status_code != 200:
                print(f"❌ Chat failed: {chat_response.status_code}")
                self.tests_run += 1
                return False
            
            chat_data = chat_response.json()
            if chat_data.get('status') == 'success':
                chat_id = chat_data.get('chat_id')
                response_text = chat_data.get('response', '')
                print(f"  ✅ Chat successful, ID: {chat_id}")
                print(f"  ✅ Response preview: {response_text[:100]}...")
                
                # Step 3: Test chat continuation
                print("  Step 3: Testing chat continuation...")
                continue_payload = {
                    "prompt": "What was my previous message?",
                    "chat_id": chat_id,
                    "use_web_search": False,
                    "agent_name": None,
                    "model_name": None
                }
                
                continue_response = requests.post(
                    f"{self.base_url}/chat",
                    json=continue_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if continue_response.status_code == 200:
                    continue_data = continue_response.json()
                    if continue_data.get('status') == 'success':
                        print("  ✅ Chat continuation successful")
                        print(f"  ✅ Response preview: {continue_data.get('response', '')[:100]}...")
                        self.tests_run += 1
                        self.tests_passed += 1
                        return True
                    else:
                        print(f"❌ Chat continuation failed: {continue_data.get('message')}")
                else:
                    print(f"❌ Chat continuation failed: {continue_response.status_code}")
            else:
                print(f"❌ Chat failed: {chat_data.get('message')}")
            
        except Exception as e:
            print(f"❌ Error in chat workflow: {str(e)}")
        
        self.tests_run += 1
        return False

    def test_error_handling_simulation(self):
        """Test how the frontend would handle API errors"""
        print("🔍 Testing Error Handling Simulation...")
        
        try:
            # Test invalid chat request (no prompt)
            error_response = requests.post(
                f"{self.base_url}/chat",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if error_response.status_code == 400:
                error_data = error_response.json()
                if error_data.get('status') == 'error':
                    print("✅ Error handling works correctly - returns proper error response")
                    self.tests_run += 1
                    self.tests_passed += 1
                    return True
            
            print(f"❌ Error handling failed: Expected 400, got {error_response.status_code}")
            
        except Exception as e:
            print(f"❌ Error in error handling test: {str(e)}")
        
        self.tests_run += 1
        return False

def main():
    print("🚀 Starting Qwen Clone Frontend Integration Tests")
    print("=" * 60)
    
    tester = QwenFrontendTester()
    
    # Run all tests
    test_results = []
    
    print("\n📋 PHASE 1: Frontend Loading Tests")
    test_results.append(("Frontend HTML Loading", tester.test_frontend_loading()))
    test_results.append(("Static Assets Loading", tester.test_static_assets()))
    
    print("\n📋 PHASE 2: Integration Workflow Tests")
    test_results.append(("Complete Chat Workflow", tester.test_chat_workflow_simulation()))
    test_results.append(("Error Handling", tester.test_error_handling_simulation()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FRONTEND INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All frontend integration tests passed!")
        return 0
    else:
        print("⚠️  Some frontend integration tests failed")
        return 1

if __name__ == "__main__":
    exit(main())