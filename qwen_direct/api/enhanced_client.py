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
import re
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
        Generate image from text prompt using Qwen's MCP image-generation tool
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
            
            # Proper MCP image generation payload using existing Qwen model
            payload = {
                "stream": False,
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "normal",
                "model": model,  # Use existing Qwen model that supports MCP
                "parent_id": None,
                "messages": [{
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": f"Generate an image: {prompt}",  # Clear instruction to generate image
                    "user_action": "chat",
                    "files": [],
                    "timestamp": timestamp,
                    "models": [model],
                    "chat_type": "t2i",  # Text-to-Image chat type (confirmed from model info)
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "phase"
                    },
                    "extra": {
                        "meta": {
                            "subChatType": "t2i"  # Text-to-image subchat type
                        }
                    },
                    "sub_chat_type": "t2i",
                    "parent_id": None
                }],
                "timestamp": timestamp,
                "turn_id": turn_id,
                "modelIdx": 0,
                # Enable MCP image generation tool
                "use_mcp_tools": True,
                "mcp_tools": ["image-generation"]  # Use the image-generation MCP tool
            }
            
            url = f"{self.base_url}/api/v2/chat/completions"
            params = {"chat_id": chat_id}
            
            response = self.session.post(url, json=payload, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract image URL from response with improved parsing for Wanx model
            image_url = None
            
            if data.get('success') and 'data' in data:
                response_data = data['data']
                
                # Check for tool results (MCP responses)
                if 'tool_results' in response_data:
                    tool_results = response_data['tool_results']
                    if isinstance(tool_results, list) and len(tool_results) > 0:
                        for result in tool_results:
                            if result.get('tool_name') == 'image_gen':
                                image_url = result.get('image_url') or result.get('url') or result.get('output')
                                if image_url:
                                    break
                
                # Check for MCP results
                if not image_url and 'mcp_results' in response_data:
                    mcp_results = response_data['mcp_results']
                    if isinstance(mcp_results, list) and len(mcp_results) > 0:
                        for result in mcp_results:
                            if 'image_gen' in str(result) or 'wanx' in str(result).lower():
                                image_url = result.get('image_url') or result.get('url') or result.get('output')
                                if image_url:
                                    break
                
                # Check choices structure for embedded images or URLs
                if not image_url and 'choices' in response_data:
                    choices = response_data['choices']
                    if choices and len(choices) > 0:
                        choice = choices[0]
                        if 'message' in choice:
                            message = choice['message']
                            
                            # Check for attachments first (most likely location for images)
                            if 'attachments' in message:
                                for attachment in message['attachments']:
                                    if attachment.get('type') in ['image', 'picture', 'file'] and attachment.get('url'):
                                        image_url = attachment['url']
                                        break
                            
                            # Check for embedded images in content
                            if not image_url:
                                content = message.get('content', '')
                                # Look for image URLs in content using comprehensive patterns
                                import re
                                url_patterns = [
                                    r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)',
                                    r'blob:[^)\s<>"]+',
                                    r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+',
                                    r'https?://[^\s<>"]+/(?:file|image|attachment|media)/[^\s<>"]+',
                                    r'https?://[^\s<>"]*qwen[^\s<>"]*/[^\s<>"]*\.(jpg|jpeg|png|gif|webp)',
                                ]
                                
                                for pattern in url_patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE)
                                    if matches:
                                        image_url = matches[0] if isinstance(matches[0], str) else matches[0][0]
                                        break
                
                # Try other possible response locations for image URLs
                if not image_url:
                    search_keys = [
                        'image_url', 'url', 'file_url', 'attachment_url', 'generated_image',
                        'wanx_image_url', 'result_url', 'output_url', 'media_url'
                    ]
                    for key in search_keys:
                        if key in response_data and response_data[key]:
                            image_url = response_data[key]
                            break
            
            # Enhanced debug logging
            logger.info(f"✅ Image generation completed for prompt: {prompt[:50]}...")
            logger.info(f"🔍 FULL API RESPONSE STRUCTURE:")
            logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            logger.info(f"Full response data: {json.dumps(data, indent=2)}")
            
            if image_url:
                logger.info(f"✅ Image URL extracted: {image_url[:100]}...")
                return {
                    "success": True,
                    "image_url": image_url,
                    "chat_id": chat_id,
                    "data": data
                }
            else:
                logger.warning(f"⚠️ No image URL found in response - trying alternative method")
                
                # Try alternative image generation API endpoint
                return self._try_alternative_image_generation(prompt, chat_id)
                
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return {"success": False, "error": f"Image generation failed: {e}"}
    
    def _try_alternative_image_generation(self, prompt: str, chat_id: str) -> Dict[str, Any]:
        """
        Alternative image generation method trying direct MCP tool invocation
        """
        try:
            logger.info("🔄 Trying alternative MCP image generation method...")
            
            # Try direct MCP tool invocation with different approach
            turn_id = str(uuid.uuid4())
            fid = str(uuid.uuid4())
            timestamp = int(time.time())
            
            # Alternative payload structure that might work better
            alt_payload = {
                "stream": False,
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "normal",
                "model": "qwen3-235b-a22b",  # Use flagship model with MCP support
                "parent_id": None,
                "messages": [{
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": f"Please use the image generation tool to create an image of: {prompt}",
                    "user_action": "chat",
                    "files": [],
                    "timestamp": timestamp,
                    "models": ["qwen3-235b-a22b"],
                    "chat_type": "t2i",
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "phase"
                    },
                    "extra": {
                        "meta": {
                            "subChatType": "t2i"
                        }
                    },
                    "sub_chat_type": "t2i",
                    "parent_id": None
                }],
                "timestamp": timestamp,
                "turn_id": turn_id,
                "modelIdx": 0,
                # Explicit MCP tool specification
                "tools": [{
                    "type": "mcp",
                    "function": {
                        "name": "image-generation",
                        "parameters": {
                            "prompt": prompt,
                            "size": "1024x1024",
                            "quality": "standard",
                            "style": "realistic"
                        }
                    }
                }],
                "tool_choice": {"type": "function", "function": {"name": "image-generation"}}
            }
            
            url = f"{self.base_url}/api/v2/chat/completions"
            params = {"chat_id": chat_id}
            
            logger.info(f"🎯 Trying alternative MCP approach")
            response = self.session.post(url, json=alt_payload, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Alternative MCP method response received")
                logger.info(f"Response: {json.dumps(data, indent=2)}")
                
                # Look for image in response
                image_url = self._extract_image_url_from_response(data)
                
                if image_url:
                    return {
                        "success": True,
                        "image_url": image_url,
                        "chat_id": chat_id,
                        "data": data
                    }
                else:
                    logger.warning("⚠️ Alternative method also returned no image URL")
            
            # If still no success, provide helpful error message
            return {
                "success": False,
                "error": "Image generation is not properly configured. The Qwen API appears to be returning text descriptions instead of actual images. This may be due to MCP tool configuration or API limitations.",
                "chat_id": chat_id,
                "suggestion": "The model has image generation capabilities listed but may require different API parameters or authentication levels to access actual image generation."
            }
            
        except Exception as e:
            logger.error(f"❌ Alternative image generation failed: {e}")
            return {
                "success": False,
                "error": f"Alternative image generation method failed: {e}",
                "chat_id": chat_id
            }
    
    def _extract_image_url_from_response(self, data: dict) -> str:
        """
        Comprehensive image URL extraction from API response
        """
        image_url = None
        
        if not data.get('success') or 'data' not in data:
            return None
            
        response_data = data['data']
        
        # Check for tool calls/results
        search_locations = [
            'tool_calls', 'tool_results', 'mcp_results', 'function_calls',
            'attachments', 'files', 'media', 'images'
        ]
        
        for location in search_locations:
            if location in response_data:
                result = response_data[location]
                if isinstance(result, list) and len(result) > 0:
                    for item in result:
                        if isinstance(item, dict):
                            # Look for URL keys
                            for url_key in ['url', 'image_url', 'file_url', 'attachment_url', 'output']:
                                if url_key in item and item[url_key]:
                                    image_url = item[url_key]
                                    break
                        if image_url:
                            break
                if image_url:
                    break
        
        # Check choices structure as fallback
        if not image_url and 'choices' in response_data:
            choices = response_data['choices']
            if choices and len(choices) > 0:
                choice = choices[0]
                if 'message' in choice and 'attachments' in choice['message']:
                    for attachment in choice['message']['attachments']:
                        if attachment.get('type') in ['image', 'picture'] and attachment.get('url'):
                            image_url = attachment['url']
                            break
        
        return image_url
    
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
        Send chat message with attached files and dynamic model configuration
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
            
            # Extract dynamic configuration
            model = kwargs.get('model', "qwen3-235b-a22b")
            feature_config = kwargs.get('feature_config', {
                "thinking_enabled": False,
                "output_schema": "phase"
            })
            
            payload = {
                "stream": kwargs.get('stream', True),
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "normal",
                "model": model,
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
                    "models": [model],
                    "chat_type": "t2t",
                    "feature_config": feature_config,
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
            
            # Apply model-specific file handling
            if kwargs.get('category') == 'vision' and any('image' in str(file_id).lower() for file_id in file_ids):
                payload["vision_mode"] = True
                payload["image_analysis"] = True
            elif kwargs.get('category') == 'coding' and any('code' in str(file_id).lower() for file_id in file_ids):
                payload["code_analysis"] = True
                payload["syntax_detection"] = True
            
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
        Send chat message with web search enabled and dynamic model configuration
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
            
            # Extract dynamic configuration
            model = kwargs.get('model', "qwen3-235b-a22b")
            feature_config = kwargs.get('feature_config', {
                "thinking_enabled": False,
                "output_schema": "phase",
                "web_search_enabled": True
            })
            
            payload = {
                "stream": kwargs.get('stream', True),
                "incremental_output": True,
                "chat_id": chat_id,
                "chat_mode": "web_search",  # Enable web search mode
                "model": model,
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
                    "models": [model],
                    "chat_type": "t2t_search",
                    "feature_config": feature_config,
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
            
            # Apply model-specific optimizations for web search
            if kwargs.get('category') == 'reasoning':
                payload["search_depth"] = "comprehensive"
                payload["reasoning_mode"] = True
            elif kwargs.get('category') == 'coding':
                payload["search_sources"] = ["stackoverflow", "github", "docs"]
            
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