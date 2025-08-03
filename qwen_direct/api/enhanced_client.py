#!/usr/bin/env python3
"""
Enhanced Qwen API Client with Advanced Features
Adds image generation, file upload, and web search to the complete client
"""

import requests
import json
import uuid
import time
import sseclient
import base64
from typing import Dict, Any, Optional, List
from complete_client import QwenCompleteClient
import logging

logger = logging.getLogger(__name__)

class QwenEnhancedClient(QwenCompleteClient):
    """
    Enhanced Qwen API Client with advanced features:
    - Image generation via text-to-image
    - File upload support  
    - Web search integration
    - Voice input handling
    """
    
    def __init__(self, jwt_token: str = None, base_url: str = "https://chat.qwen.ai"):
        super().__init__(jwt_token, base_url)
        logger.info("✅ Enhanced Qwen client initialized with advanced features")
    
    # ==========================================
    # ADVANCED FEATURES - IMAGE GENERATION
    # ==========================================
    
    def generate_image(self, prompt: str, chat_id: str = None, model: str = "qwen3-235b-a22b") -> Dict[str, Any]:
        """
        Generate image from text prompt
        Uses the chat completion endpoint with special image generation parameters
        """
        try:
            if not chat_id:
                chat_result = self.create_new_chat()
                if not chat_result.get('success'):
                    return {"success": False, "error": "Failed to create chat for image generation"}
                chat_id = chat_result['data']['id']
            
            # Generate required IDs
            turn_id = str(uuid.uuid4())
            fid = str(uuid.uuid4())
            timestamp = int(time.time())
            
            # Special payload for image generation
            payload = {
                "stream": False,  # Image generation typically returns single result
                "incremental_output": False,
                "chat_id": chat_id,
                "chat_mode": "image_generation",  # Special mode for image generation
                "model": model,
                "parent_id": None,
                "messages": [{
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": prompt,
                    "user_action": "image_generation",
                    "files": [],
                    "timestamp": timestamp,
                    "models": [model],
                    "chat_type": "t2i",  # Text to image
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "image"
                    },
                    "extra": {
                        "meta": {"subChatType": "t2i"}
                    },
                    "sub_chat_type": "t2i",
                    "parent_id": None
                }],
                "timestamp": timestamp,
                "turn_id": turn_id,
                "modelIdx": 0
            }
            
            url = f"{self.base_url}/api/v2/chat/completions"
            params = {"chat_id": chat_id}
            
            response = self.session.post(url, json=payload, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract image URL from response
            image_url = None
            if data.get('choices') and len(data['choices']) > 0:
                choice = data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    # Parse content for image URL (format may vary)
                    if isinstance(content, str) and ('http' in content or 'blob:' in content):
                        image_url = content
                    elif isinstance(content, dict) and 'image_url' in content:
                        image_url = content['image_url']
            
            logger.info(f"✅ Image generated successfully for prompt: {prompt[:50]}...")
            
            return {
                "success": True,
                "image_url": image_url,
                "chat_id": chat_id,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return {"success": False, "error": f"Image generation failed: {e}"}
    
    # ==========================================
    # ADVANCED FEATURES - FILE UPLOAD
    # ==========================================
    
    def upload_file(self, file_path: str, file_type: str = "auto") -> Dict[str, Any]:
        """
        Upload file to Qwen for use in conversations
        Returns file ID for use in chat messages
        """
        try:
            # Read file and encode as base64 for upload
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            file_name = file_path.split('/')[-1]
            file_size = len(file_content)
            
            payload = {
                "file_name": file_name,
                "file_content": file_base64,
                "file_type": file_type,
                "file_size": file_size,
                "upload_type": "chat_attachment"
            }
            
            # Use file upload endpoint (may need to be discovered)
            url = f"{self.base_url}/api/v2/files/upload"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            file_id = data.get('data', {}).get('file_id')
            
            logger.info(f"✅ File uploaded successfully: {file_name}")
            
            return {
                "success": True,
                "file_id": file_id,
                "file_name": file_name,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
            return {"success": False, "error": f"File upload failed: {e}"}
    
    def send_chat_with_files(self, message: str, file_ids: List[str], chat_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Send chat message with attached files
        """
        try:
            if not chat_id:
                chat_result = self.create_new_chat()
                if not chat_result.get('success'):
                    return {"success": False, "error": "Failed to create chat"}
                chat_id = chat_result['data']['id']
            
            # Generate required IDs
            turn_id = str(uuid.uuid4())
            fid = str(uuid.uuid4())
            timestamp = int(time.time())
            
            # Format file attachments
            files = []
            for file_id in file_ids:
                files.append({
                    "file_id": file_id,
                    "type": "attachment"
                })
            
            payload = {
                "stream": kwargs.get('stream', True),
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "normal",
                "model": kwargs.get('model', "qwen3-235b-a22b"),
                "parent_id": None,
                "messages": [{
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": message,
                    "user_action": "chat",
                    "files": files,  # Include file attachments
                    "timestamp": timestamp,
                    "models": [kwargs.get('model', "qwen3-235b-a22b")],
                    "chat_type": "t2t",
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "phase"
                    },
                    "extra": {
                        "meta": {"subChatType": "t2t"}
                    },
                    "sub_chat_type": "t2t",
                    "parent_id": None
                }],
                "timestamp": timestamp,
                "turn_id": turn_id,
                "modelIdx": 0
            }
            
            url = f"{self.base_url}/api/v2/chat/completions"
            params = {"chat_id": chat_id}
            
            if kwargs.get('stream', True):
                return self._handle_streaming_response(url, payload, params)
            else:
                response = self.session.post(url, json=payload, params=params)
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json(),
                    "chat_id": chat_id
                }
                
        except Exception as e:
            return {"success": False, "error": f"Chat with files failed: {e}"}
    
    # ==========================================
    # ADVANCED FEATURES - WEB SEARCH
    # ==========================================
    
    def send_chat_with_web_search(self, message: str, chat_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Send chat message with web search enabled
        """
        try:
            if not chat_id:
                chat_result = self.create_new_chat()
                if not chat_result.get('success'):
                    return {"success": False, "error": "Failed to create chat"}
                chat_id = chat_result['data']['id']
            
            # Generate required IDs
            turn_id = str(uuid.uuid4())
            fid = str(uuid.uuid4())
            timestamp = int(time.time())
            
            payload = {
                "stream": kwargs.get('stream', True),
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "web_search",  # Enable web search mode
                "model": kwargs.get('model', "qwen3-235b-a22b"),
                "parent_id": None,
                "messages": [{
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": message,
                    "user_action": "chat_with_search",
                    "files": [],
                    "timestamp": timestamp,
                    "models": [kwargs.get('model', "qwen3-235b-a22b")],
                    "chat_type": "t2t_search",
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "phase",
                        "web_search_enabled": True
                    },
                    "extra": {
                        "meta": {"subChatType": "t2t_search"}
                    },
                    "sub_chat_type": "t2t_search",
                    "parent_id": None
                }],
                "timestamp": timestamp,
                "turn_id": turn_id,
                "modelIdx": 0,
                "web_search": True  # Enable web search
            }
            
            url = f"{self.base_url}/api/v2/chat/completions"
            params = {"chat_id": chat_id, "web_search": "true"}
            
            if kwargs.get('stream', True):
                return self._handle_streaming_response(url, payload, params)
            else:
                response = self.session.post(url, json=payload, params=params)
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json(),
                    "chat_id": chat_id
                }
                
        except Exception as e:
            return {"success": False, "error": f"Web search chat failed: {e}"}
    
    # ==========================================
    # ENHANCED TESTING
    # ==========================================
    
    def test_advanced_features(self) -> Dict[str, Any]:
        """
        Test all advanced features
        """
        print("\n🚀 Testing Advanced Features...")
        print("=" * 60)
        
        results = {
            "timestamp": time.time(),
            "advanced_tests": {},
            "successful": 0,
            "failed": 0
        }
        
        # Test image generation
        try:
            print("🎨 Testing Image Generation...")
            img_result = self.generate_image("A beautiful sunset over mountains")
            if img_result.get("success"):
                print("✅ Image Generation: OK")
                results["successful"] += 1
                results["advanced_tests"]["image_generation"] = {"status": "success"}
            else:
                print(f"❌ Image Generation: {img_result.get('error')}")
                results["failed"] += 1
                results["advanced_tests"]["image_generation"] = {"status": "failed", "error": img_result.get('error')}
        except Exception as e:
            print(f"❌ Image Generation: Exception - {e}")
            results["failed"] += 1
            results["advanced_tests"]["image_generation"] = {"status": "failed", "error": str(e)}
        
        # Test web search
        try:
            print("🌐 Testing Web Search Chat...")
            search_result = self.send_chat_with_web_search("What are the latest developments in AI?", stream=False)
            if search_result.get("success"):
                print("✅ Web Search Chat: OK")
                results["successful"] += 1
                results["advanced_tests"]["web_search"] = {"status": "success"}
            else:
                print(f"❌ Web Search Chat: {search_result.get('error')}")
                results["failed"] += 1
                results["advanced_tests"]["web_search"] = {"status": "failed", "error": search_result.get('error')}
        except Exception as e:
            print(f"❌ Web Search Chat: Exception - {e}")
            results["failed"] += 1
            results["advanced_tests"]["web_search"] = {"status": "failed", "error": str(e)}
        
        total_tests = results["successful"] + results["failed"]
        success_rate = (results["successful"] / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 ADVANCED FEATURES TEST RESULTS")
        print("=" * 60)
        print(f"✅ Successful: {results['successful']}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed: {results['failed']}/{total_tests}")
        
        return results

def main():
    """Demo the enhanced API client"""
    print("🚀 QWEN ENHANCED API CLIENT DEMO")
    print("=" * 50)
    
    # Initialize enhanced client
    client = QwenEnhancedClient()
    
    if not client.jwt_token:
        print("❌ No authentication token found")
        return
    
    # Test all basic endpoints first
    basic_results = client.test_all_endpoints()
    
    # Test advanced features
    advanced_results = client.test_advanced_features()
    
    total_success = basic_results["successful"] + advanced_results["successful"]
    total_tests = basic_results["total_endpoints"] + (advanced_results["successful"] + advanced_results["failed"])
    overall_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"✅ Total endpoints working: {total_success}/{total_tests} ({overall_rate:.1f}%)")
    print(f"🚀 System status: {'FULLY OPERATIONAL' if overall_rate >= 80 else 'PARTIALLY FUNCTIONAL'}")
    
    print("\n👋 Enhanced demo completed!")

if __name__ == "__main__":
    main()