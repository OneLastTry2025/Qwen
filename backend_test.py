#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Qwen Direct API System
Tests hybrid architecture: Direct API (0.8s) + Browser Fallback (2-50s)
Expected Performance: Up to 60x faster with direct API
"""

import requests
import sys
import time
import json
from datetime import datetime

class QwenHybridAPITester:
    def __init__(self, base_url="https://f4705fad-2915-4b96-a09c-29e7655c6eed.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.performance_data = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60):
        """Run a single API test with performance tracking"""
        url = f"{self.base_url}/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            
            duration = time.time() - start_time
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}, Time: {duration:.2f}s")
                
                # Record performance data
                self.performance_data.append({
                    'endpoint': endpoint,
                    'duration': duration,
                    'timestamp': datetime.now()
                })
                
                try:
                    response_data = response.json()
                    return success, response_data
                except:
                    return success, {"raw_response": response.text}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            print(f"⏰ Timeout after {duration:.2f}s - This might indicate browser fallback is being used")
            return False, {}
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Failed - Error: {str(e)}, Time: {duration:.2f}s")
            return False, {}

    def test_performance_endpoint(self):
        """Test performance statistics endpoint"""
        print("\n" + "="*60)
        print("🚀 TESTING PERFORMANCE & SPEED")
        print("="*60)
        
        success, response = self.run_test(
            "Performance Statistics",
            "GET",
            "api/performance",
            200
        )
        
        if success and response:
            print("\n📊 Performance Stats:")
            data = response.get('data', {})
            print(f"   Direct API Calls: {data.get('direct_api_calls', 0)}")
            print(f"   Browser Fallback Calls: {data.get('browser_fallback_calls', 0)}")
            print(f"   Average Direct Time: {data.get('avg_direct_time', 0):.2f}s")
            print(f"   Average Browser Time: {data.get('avg_browser_time', 0):.2f}s")
            
            if data.get('speed_improvement'):
                print(f"   🚀 Speed Improvement: {data['speed_improvement']:.1f}x faster")
            
            print(f"   Direct API Available: {response.get('direct_api_available', False)}")
            
            return data
        
        return None

    def test_auth_status(self):
        """Test authentication status (Direct API only)"""
        success, response = self.run_test(
            "Authentication Status",
            "GET", 
            "api/auth/status",
            200
        )
        
        if success:
            print(f"   Auth Status: {response.get('success', False)}")
        
        return success

    def test_models_endpoint(self):
        """Test available models endpoint"""
        success, response = self.run_test(
            "Available Models",
            "GET",
            "api/models", 
            200
        )
        
        if success and response.get('data'):
            models = response['data']
            print(f"   Found {len(models)} models")
            if models:
                print(f"   Sample models: {[m.get('name', m) for m in models[:3]]}")
        
        return success, response.get('data', [])

    def test_conversations_endpoint(self):
        """Test conversations endpoint (Direct API only)"""
        success, response = self.run_test(
            "Conversations List",
            "GET",
            "api/conversations",
            200
        )
        
        if success and response.get('data'):
            conversations = response['data']
            print(f"   Found {len(conversations)} conversations")
        
        return success

    def test_folders_endpoint(self):
        """Test folders endpoint (Direct API only)"""
        success, response = self.run_test(
            "User Folders",
            "GET",
            "api/folders",
            200
        )
        
        if success and response.get('data'):
            folders = response['data']
            print(f"   Found {len(folders)} folders")
        
        return success

    def test_chat_functionality(self):
        """Test core chat functionality with performance measurement"""
        print("\n" + "="*60)
        print("💬 TESTING CORE CHAT FUNCTIONALITY")
        print("="*60)
        
        test_prompts = [
            "Hello, can you tell me what you are?",
            "What's 2+2?",
            "Tell me a short joke"
        ]
        
        chat_results = []
        
        for i, prompt in enumerate(test_prompts):
            print(f"\n--- Chat Test {i+1} ---")
            
            success, response = self.run_test(
                f"Chat Message {i+1}",
                "POST",
                "api/chat",
                200,
                data={
                    "prompt": prompt,
                    "model_name": "qwen3-235b-a22b"
                },
                timeout=120  # Allow more time for potential browser fallback
            )
            
            if success:
                chat_response = response.get('response') or response.get('data', {}).get('response', 'No response')
                print(f"   Response: {chat_response[:100]}...")
                
                # Check if we got a chat_id for conversation continuity
                if response.get('chat_id'):
                    print(f"   Chat ID: {response['chat_id']}")
                
                chat_results.append({
                    'prompt': prompt,
                    'success': True,
                    'response': chat_response
                })
            else:
                chat_results.append({
                    'prompt': prompt, 
                    'success': False,
                    'response': None
                })
        
        return chat_results

    def test_web_search_chat(self):
        """Test chat with web search enabled"""
        print(f"\n--- Web Search Chat Test ---")
        
        success, response = self.run_test(
            "Chat with Web Search",
            "POST",
            "api/chat",
            200,
            data={
                "prompt": "What's the latest news about AI?",
                "use_web_search": True,
                "model_name": "qwen3-235b-a22b"
            },
            timeout=180  # Web search might take longer
        )
        
        if success:
            chat_response = response.get('response') or response.get('data', {}).get('response', 'No response')
            print(f"   Web Search Response: {chat_response[:150]}...")
        
        return success

    def test_image_generation(self):
        """Test image generation functionality"""
        print("\n" + "="*60)
        print("🎨 TESTING IMAGE GENERATION")
        print("="*60)
        
        success, response = self.run_test(
            "Image Generation",
            "POST",
            "api/image",
            200,
            data={
                "prompt": "A beautiful sunset over mountains"
            },
            timeout=180  # Image generation might take longer
        )
        
        if success:
            image_url = response.get('image_url')
            if image_url:
                print(f"   ✅ Image generated successfully")
                print(f"   Image URL: {image_url}")
            else:
                print(f"   ⚠️ No image URL in response")
        
        return success

    def analyze_performance(self):
        """Analyze performance data and verify speed claims"""
        print("\n" + "="*60)
        print("⚡ PERFORMANCE ANALYSIS")
        print("="*60)
        
        if not self.performance_data:
            print("❌ No performance data collected")
            return
        
        # Calculate average response times
        total_time = sum(p['duration'] for p in self.performance_data)
        avg_time = total_time / len(self.performance_data)
        
        print(f"📊 Performance Summary:")
        print(f"   Total API calls: {len(self.performance_data)}")
        print(f"   Average response time: {avg_time:.2f}s")
        print(f"   Fastest response: {min(p['duration'] for p in self.performance_data):.2f}s")
        print(f"   Slowest response: {max(p['duration'] for p in self.performance_data):.2f}s")
        
        # Check if we're meeting the direct API performance claims
        direct_api_responses = [p for p in self.performance_data if p['duration'] <= 3.0]
        browser_fallback_responses = [p for p in self.performance_data if p['duration'] > 10.0]
        
        print(f"\n🚀 Speed Analysis:")
        print(f"   Fast responses (≤3s, likely Direct API): {len(direct_api_responses)}")
        print(f"   Slow responses (>10s, likely Browser Fallback): {len(browser_fallback_responses)}")
        
        if direct_api_responses:
            avg_direct = sum(p['duration'] for p in direct_api_responses) / len(direct_api_responses)
            print(f"   Average Direct API time: {avg_direct:.2f}s")
            
            if avg_direct <= 2.0:
                print(f"   ✅ Direct API performance meets expectations (≤2s)")
            else:
                print(f"   ⚠️ Direct API slower than expected (target: ≤2s)")

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 STARTING COMPREHENSIVE QWEN HYBRID API TESTING")
        print("=" * 80)
        print("🎯 Testing Direct API (0.8s) + Browser Fallback (2-50s) System")
        print("⚡ Expected: Up to 60x speed improvement")
        print("=" * 80)
        
        # Test performance endpoint first
        perf_stats = self.test_performance_endpoint()
        
        # Test direct API endpoints
        print("\n" + "="*60)
        print("🔗 TESTING DIRECT API ENDPOINTS")
        print("="*60)
        
        self.test_auth_status()
        models_success, models = self.test_models_endpoint()
        self.test_conversations_endpoint()
        self.test_folders_endpoint()
        
        # Test core functionality
        chat_results = self.test_chat_functionality()
        self.test_web_search_chat()
        self.test_image_generation()
        
        # Performance analysis
        self.analyze_performance()
        
        # Final summary
        print("\n" + "="*80)
        print("📋 FINAL TEST SUMMARY")
        print("="*80)
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"📊 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if perf_stats:
            print(f"\n🚀 System Performance:")
            if perf_stats.get('direct_api_calls', 0) > 0:
                print(f"   Direct API working: ✅")
                print(f"   Average Direct API time: {perf_stats.get('avg_direct_time', 0):.2f}s")
            else:
                print(f"   Direct API working: ❌ (using browser fallback)")
            
            if perf_stats.get('speed_improvement'):
                improvement = perf_stats['speed_improvement']
                print(f"   Speed improvement: {improvement:.1f}x")
                if improvement >= 10:
                    print(f"   🎯 Significant speed improvement achieved!")
                else:
                    print(f"   ⚠️ Speed improvement lower than expected")
        
        # Determine overall result
        if self.tests_passed >= self.tests_run * 0.8:  # 80% pass rate
            print(f"\n🎉 OVERALL RESULT: SYSTEM WORKING WELL")
            return 0
        else:
            print(f"\n❌ OVERALL RESULT: SYSTEM NEEDS ATTENTION")
            return 1

def main():
    tester = QwenHybridAPITester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())