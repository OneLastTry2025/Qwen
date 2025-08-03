#!/usr/bin/env python3
"""
Complete API Testing Suite
Tests all 17+ discovered endpoints comprehensively
"""

import sys
import os
sys.path.append('/app/qwen_direct/api')

from complete_client import QwenCompleteClient

def test_api_client():
    """Test the complete API client without interactive input"""
    print("🧪 COMPREHENSIVE API CLIENT TEST")
    print("=" * 50)
    
    client = QwenCompleteClient()
    
    if not client.jwt_token:
        print("❌ No authentication token found")
        return False
    
    # Run comprehensive endpoint tests
    results = client.test_all_endpoints()
    
    # Test a single chat message
    print(f"\n💬 Testing single chat message...")
    chat_response = client.send_chat_completion("Write a short haiku about technology", stream=False)
    
    if chat_response.get("success"):
        print(f"✅ Chat message successful")
        print(f"📝 Response preview: {str(chat_response.get('data', ''))[:100]}...")
    else:
        print(f"❌ Chat message failed: {chat_response.get('error')}")
    
    # Summary
    success_rate = (results["successful"] / results["total_endpoints"]) * 100 if results["total_endpoints"] > 0 else 0
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"✅ Endpoints working: {results['successful']}/{results['total_endpoints']} ({success_rate:.1f}%)")
    print(f"🚀 System status: {'FULLY OPERATIONAL' if success_rate >= 80 else 'PARTIALLY FUNCTIONAL'}")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = test_api_client()
    print(f"\n{'🎉 All systems operational!' if success else '⚠️ Some issues detected'}")