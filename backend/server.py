#!/usr/bin/env python3
"""
Hybrid Qwen API Server
Combines fast direct API calls with Playwright fallback for maximum reliability
Performance: Direct API (0.8s) vs Browser Automation (2-50s) = 60x faster
"""

import asyncio
import os
import sys
import uuid
import time
from pathlib import Path
from quart import Quart, request, jsonify, send_from_directory
from quart_cors import cors
import json
import logging

# Add the qwen_direct API to Python path
sys.path.append('/app/qwen_direct/api')

try:
    from enhanced_client import QwenEnhancedClient
    DIRECT_API_AVAILABLE = True
except ImportError:
    try:
        from complete_client import QwenCompleteClient as QwenEnhancedClient
        DIRECT_API_AVAILABLE = True
    except ImportError:
        DIRECT_API_AVAILABLE = False

# Import original Playwright system as fallback
from server_original import BrowserManager, ask_qwen, generate_qwen_image, get_available_models

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridQwenServer:
    """
    Hybrid server that uses direct API when possible, falls back to Playwright
    
    Performance Priority:
    1. Direct API calls (0.8 seconds) - 60x faster
    2. Playwright automation (2-50 seconds) - reliable fallback
    """
    
    def __init__(self):
        self.direct_client = None
        self.browser_manager = None
        self.direct_api_working = False
        self.performance_stats = {
            "direct_api_calls": 0,
            "browser_fallback_calls": 0,
            "avg_direct_time": 0,
            "avg_browser_time": 0
        }
        
        # Initialize direct API client
        if DIRECT_API_AVAILABLE:
            try:
                self.direct_client = QwenEnhancedClient()
                if self.direct_client.jwt_token:
                    # Test direct API connection
                    auth_result = self.direct_client.get_auth_status()
                    self.direct_api_working = auth_result.get('success', False)
                    if self.direct_api_working:
                        logger.info("✅ Direct API client initialized and working")
                    else:
                        logger.warning("⚠️ Direct API client initialized but authentication failed")
                else:
                    logger.warning("⚠️ Direct API client initialized but no JWT token found")
            except Exception as e:
                logger.error(f"❌ Failed to initialize direct API client: {e}")
                self.direct_api_working = False
        else:
            logger.warning("⚠️ Direct API client not available, using browser automation only")
        
        # Initialize browser manager as fallback
        self.browser_manager = BrowserManager(pool_size=2)  # Smaller pool since direct API is primary
        logger.info("✅ Hybrid server initialized - Direct API primary, Browser fallback")
    
    async def initialize(self):
        """Initialize the browser manager fallback"""
        try:
            await self.browser_manager.initialize()
            logger.info("✅ Browser fallback system initialized")
        except Exception as e:
            logger.error(f"❌ Browser fallback initialization failed: {e}")
    
    async def shutdown(self):
        """Shutdown both systems"""
        if self.browser_manager:
            await self.browser_manager.shutdown()
            logger.info("✅ Hybrid server shutdown complete")
    
    def _record_performance(self, method: str, duration: float, api_type: str):
        """Record performance metrics"""
        if api_type == "direct":
            self.performance_stats["direct_api_calls"] += 1
            # Calculate running average
            prev_avg = self.performance_stats["avg_direct_time"]
            count = self.performance_stats["direct_api_calls"]
            self.performance_stats["avg_direct_time"] = ((prev_avg * (count - 1)) + duration) / count
        else:
            self.performance_stats["browser_fallback_calls"] += 1
            prev_avg = self.performance_stats["avg_browser_time"]
            count = self.performance_stats["browser_fallback_calls"]
            self.performance_stats["avg_browser_time"] = ((prev_avg * (count - 1)) + duration) / count
        
        # Calculate speed improvement
        if self.performance_stats["avg_browser_time"] > 0:
            speed_improvement = self.performance_stats["avg_browser_time"] / self.performance_stats["avg_direct_time"]
            logger.info(f"⚡ Performance: Direct API is {speed_improvement:.1f}x faster than browser automation")
    
    async def send_message(self, prompt: str, chat_id: str = None, use_web_search: bool = False, 
                          agent_name: str = None, model_name: str = None, file_paths: list = None) -> dict:
        """
        Send chat message with hybrid approach
        Priority: Direct API -> Browser fallback
        """
        start_time = time.time()
        
        # Try direct API first if available
        if self.direct_api_working and self.direct_client:
            try:
                logger.info(f"🚀 Using Direct API for chat (expected: ~0.8s)")
                
                if use_web_search:
                    result = self.direct_client.send_chat_with_web_search(
                        prompt, chat_id, stream=False, model=model_name or "qwen3-235b-a22b"
                    )
                elif file_paths and hasattr(self.direct_client, 'send_chat_with_files'):
                    # Upload files first, then send message
                    file_ids = []
                    for file_path in file_paths:
                        upload_result = self.direct_client.upload_file(file_path)
                        if upload_result.get('success'):
                            file_ids.append(upload_result['file_id'])
                    
                    result = self.direct_client.send_chat_with_files(
                        prompt, file_ids, chat_id, stream=False, model=model_name or "qwen3-235b-a22b"
                    )
                else:
                    result = self.direct_client.send_chat_completion(
                        prompt, chat_id, model=model_name or "qwen3-235b-a22b", stream=False
                    )
                
                if result.get('success'):
                    duration = time.time() - start_time
                    self._record_performance("chat", duration, "direct")
                    logger.info(f"✅ Direct API chat completed in {duration:.2f}s")
                    
                    # Extract response from nested structure
                    response_text = ""
                    if result.get('data', {}).get('data', {}).get('choices'):
                        choices = result['data']['data']['choices']
                        if choices and len(choices) > 0:
                            response_text = choices[0].get('message', {}).get('content', '')
                    elif result.get('response'):
                        response_text = result['response']
                    
                    return {
                        "success": True,
                        "response": response_text,
                        "chat_id": result.get('chat_id'),
                        "data": result.get('data')
                    }
                else:
                    logger.warning(f"⚠️ Direct API failed: {result.get('error')}, falling back to browser")
            
            except Exception as e:
                logger.warning(f"⚠️ Direct API exception: {e}, falling back to browser")
        
        # Fallback to browser automation
        logger.info(f"🔄 Using Browser Automation fallback (expected: 2-50s)")
        page = await self.browser_manager.get_page()
        try:
            result = await ask_qwen(page, prompt, chat_id, use_web_search, file_paths, agent_name, model_name)
            duration = time.time() - start_time
            self._record_performance("chat", duration, "browser")
            logger.info(f"✅ Browser automation completed in {duration:.2f}s")
            return result
        finally:
            self.browser_manager.release_page(page)
    
    async def generate_image(self, prompt: str, chat_id: str = None) -> dict:
        """
        Generate image with hybrid approach
        Priority: Direct API -> Browser fallback
        """
        start_time = time.time()
        
        # Try direct API first if available
        if self.direct_api_working and self.direct_client and hasattr(self.direct_client, 'generate_image'):
            try:
                logger.info(f"🚀 Using Direct API for image generation")
                result = self.direct_client.generate_image(prompt, chat_id)
                
                if result.get('success'):
                    duration = time.time() - start_time
                    self._record_performance("image", duration, "direct")
                    logger.info(f"✅ Direct API image generation completed in {duration:.2f}s")
                    return result
                else:
                    logger.warning(f"⚠️ Direct API image generation failed, falling back to browser")
            
            except Exception as e:
                logger.warning(f"⚠️ Direct API image generation exception: {e}, falling back to browser")
        
        # Fallback to browser automation
        logger.info(f"🔄 Using Browser Automation for image generation")
        page = await self.browser_manager.get_page()
        try:
            result = await generate_qwen_image(page, prompt)
            duration = time.time() - start_time
            self._record_performance("image", duration, "browser")
            logger.info(f"✅ Browser image generation completed in {duration:.2f}s")
            return result
        finally:
            self.browser_manager.release_page(page)
    
    async def get_models(self) -> dict:
        """
        Get available models with hybrid approach
        """
        start_time = time.time()
        
        # Try direct API first
        if self.direct_api_working and self.direct_client:
            try:
                result = self.direct_client.get_available_models()
                if result.get('success'):
                    duration = time.time() - start_time
                    self._record_performance("models", duration, "direct")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Direct API models failed: {e}, falling back to browser")
        
        # Fallback to browser automation
        page = await self.browser_manager.get_page()
        try:
            result = await get_available_models(page)
            duration = time.time() - start_time
            self._record_performance("models", duration, "browser")
            return result
        finally:
            self.browser_manager.release_page(page)
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        
        # Calculate totals and ratios
        total_calls = stats["direct_api_calls"] + stats["browser_fallback_calls"]
        if total_calls > 0:
            stats["direct_api_ratio"] = (stats["direct_api_calls"] / total_calls) * 100
            stats["browser_fallback_ratio"] = (stats["browser_fallback_calls"] / total_calls) * 100
        
        if stats["avg_browser_time"] > 0 and stats["avg_direct_time"] > 0:
            stats["speed_improvement"] = stats["avg_browser_time"] / stats["avg_direct_time"]
        
        return stats

# Initialize hybrid server
hybrid_server = HybridQwenServer()

# --- Quart App ---
app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.before_serving
async def startup():
    await hybrid_server.initialize()

@app.after_serving
async def shutdown():
    await hybrid_server.shutdown()

# --- Hybrid API Endpoints ---

@app.route('/api/chat', methods=['POST'])
async def hybrid_chat_handler():
    """Hybrid chat endpoint with performance optimization"""
    data = await request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"status": "error", "message": "Missing 'prompt' in request body"}), 400
    
    prompt = data['prompt']
    chat_id = data.get('chat_id')
    use_web_search = data.get('use_web_search', False)
    agent_name = data.get('agent_name')
    model_name = data.get('model_name')
    file_paths = data.get('file_paths')
    
    logger.info(f"📨 Hybrid chat request: {prompt[:50]}...")
    
    result = await hybrid_server.send_message(
        prompt, chat_id, use_web_search, agent_name, model_name, file_paths
    )
    
    return jsonify(result), 200 if result.get('success') or result.get('status') == 'success' else 500

@app.route('/api/image', methods=['POST'])
async def hybrid_image_handler():
    """Hybrid image generation endpoint"""
    data = await request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"status": "error", "message": "Missing 'prompt' in request body"}), 400
    
    prompt = data['prompt']
    chat_id = data.get('chat_id')
    
    logger.info(f"🎨 Hybrid image request: {prompt[:50]}...")
    
    result = await hybrid_server.generate_image(prompt, chat_id)
    
    return jsonify(result), 200 if result.get('success') or result.get('status') == 'success' else 500

@app.route('/api/models', methods=['GET'])
async def hybrid_models_handler():
    """Hybrid models endpoint"""
    result = await hybrid_server.get_models()
    return jsonify(result), 200 if result.get('success') or result.get('status') == 'success' else 500

@app.route('/api/performance', methods=['GET'])
async def performance_stats_handler():
    """Get performance statistics"""
    stats = hybrid_server.get_performance_stats()
    return jsonify({
        "success": True,
        "data": stats,
        "direct_api_available": hybrid_server.direct_api_working
    })

@app.route('/api/model', methods=['GET'])
async def hybrid_model_handler():
    """Get current model (direct API optimized)"""
    if hybrid_server.direct_api_working and hybrid_server.direct_client:
        try:
            # Use settings to get current model faster
            settings = hybrid_server.direct_client.get_user_settings_v2()
            if settings.get('success'):
                # Extract model from settings if available
                model_name = settings.get('data', {}).get('default_model', 'qwen3-235b-a22b')
                return jsonify({"status": "success", "model_name": model_name})
        except Exception as e:
            logger.warning(f"⚠️ Direct API model check failed: {e}")
    
    # Fallback to original implementation
    from server import model_handler
    return await model_handler()

# --- Direct API Exclusive Endpoints ---

@app.route('/api/conversations', methods=['GET'])
async def conversations_handler():
    """List conversations (direct API only)"""
    if not hybrid_server.direct_api_working:
        return jsonify({"status": "error", "message": "Direct API not available"}), 503
    
    page = request.args.get('page', 1, type=int)
    result = hybrid_server.direct_client.list_conversations(page)
    return jsonify(result), 200 if result.get('success') else 500

@app.route('/api/folders', methods=['GET'])
async def folders_handler():
    """Get folders (direct API only)"""
    if not hybrid_server.direct_api_working:
        return jsonify({"status": "error", "message": "Direct API not available"}), 503
    
    result = hybrid_server.direct_client.get_folders()
    return jsonify(result), 200 if result.get('success') else 500

@app.route('/api/auth/status', methods=['GET'])
async def auth_status_handler():
    """Get authentication status (direct API only)"""
    if not hybrid_server.direct_api_working:
        return jsonify({"status": "error", "message": "Direct API not available"}), 503
    
    result = hybrid_server.direct_client.get_auth_status()
    return jsonify(result), 200 if result.get('success') else 500

# --- Frontend Serving (maintain compatibility) ---
@app.route('/')
async def serve_index():
    """Serve the main UI"""
    # Check if React build exists, otherwise serve original UI
    react_build_path = Path('/app/frontend/build/index.html')
    if react_build_path.exists():
        return await send_from_directory('/app/frontend/build', 'index.html')
    else:
        return await send_from_directory('ui_clone', 'index.html')

@app.route('/assets/<path:filename>')
async def serve_assets(filename):
    """Serve static assets"""
    return await send_from_directory(Path('ui_clone') / 'assets', filename)

@app.route('/static/<path:filename>')
async def serve_react_static(filename):
    """Serve React build static files"""
    return await send_from_directory('/app/frontend/build/static', filename)

if __name__ == "__main__":
    print("🚀 Starting Hybrid Qwen API Server")
    print("=" * 50)
    print("⚡ Performance Mode: Direct API (0.8s) + Browser Fallback (2-50s)")
    print("🎯 Expected Speed Improvement: Up to 60x faster")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8001, debug=False)