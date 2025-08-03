#!/usr/bin/env python3
"""
Qwen Feature Explorer
Systematically explores every feature on chat.qwen.ai using Playwright
Captures all network calls and maps complete API surface
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
from urllib.parse import urlparse
import os
from datetime import datetime

class QwenFeatureExplorer:
    def __init__(self, storage_state_path: str = "/app/storage_state.json"):
        self.storage_state_path = storage_state_path
        self.captured_requests = []
        self.api_endpoints = {}
        self.feature_map = {}
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup_browser(self):
        """Initialize authenticated browser with network monitoring"""
        print("🚀 Launching Playwright browser for comprehensive feature exploration...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,  # Must be headless in container environment
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with authentication
        self.context = await self.browser.new_context(
            storage_state=self.storage_state_path,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Enable network monitoring
        await self.context.route("**/*", self._intercept_requests)
        
        self.page = await self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"🟦 Console: {msg.text}"))
        
        print("✅ Browser setup complete with network monitoring enabled")
        return True
    
    async def _intercept_requests(self, route, request):
        """Intercept and log all network requests"""
        # Continue the request
        await route.continue_()
        
        # Capture API requests
        url = request.url
        if self._is_api_request(url):
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': url,
                'headers': dict(request.headers),
                'post_data': request.post_data,
                'resource_type': request.resource_type
            }
            
            self.captured_requests.append(request_data)
            
            # Update endpoint mapping
            path = urlparse(url).path
            if path not in self.api_endpoints:
                self.api_endpoints[path] = {
                    'methods': set(),
                    'examples': []
                }
            
            self.api_endpoints[path]['methods'].add(request.method)
            self.api_endpoints[path]['examples'].append(request_data)
            
            print(f"📡 API Call: {request.method} {url}")
    
    def _is_api_request(self, url: str) -> bool:
        """Check if URL is an API endpoint"""
        api_patterns = [
            '/api/', '/v1/', '/v2/', '/graphql',
            'chat.qwen.ai/api', '/completion', '/models',
            '/auth', '/user', '/chat', '/message',
            '/folder', '/tag', '/file', '/image'
        ]
        return any(pattern in url for pattern in api_patterns)
    
    async def navigate_to_qwen(self):
        """Navigate to Qwen and wait for page load"""
        print("🌐 Navigating to Qwen chat interface...")
        await self.page.goto("https://chat.qwen.ai/", wait_until="networkidle")
        await asyncio.sleep(3)  # Allow time for initial API calls
        
        # Check if authenticated
        try:
            await self.page.wait_for_selector("[data-testid='chat-input'], .chat-input, textarea", timeout=10000)
            print("✅ Successfully loaded and authenticated to Qwen interface")
            return True
        except:
            print("❌ Failed to load Qwen interface or authentication failed")
            return False
    
    async def explore_sidebar_features(self):
        """Explore all sidebar features and capture API calls"""
        print("\n🔍 Exploring Sidebar Features...")
        print("-" * 50)
        
        features_found = []
        
        # New Chat button
        try:
            new_chat = await self.page.wait_for_selector("button:has-text('New Chat'), [data-testid='new-chat'], .new-chat", timeout=5000)
            if new_chat:
                print("📝 Found: New Chat button")
                await new_chat.click()
                await asyncio.sleep(2)
                features_found.append("new_chat")
        except:
            print("⚠️ New Chat button not found")
        
        # Chat history / conversations list
        try:
            chat_items = await self.page.query_selector_all(".conversation-item, .chat-item, [data-testid='chat-item']")
            if chat_items:
                print(f"💬 Found: {len(chat_items)} chat history items")
                if len(chat_items) > 0:
                    await chat_items[0].click()
                    await asyncio.sleep(2)
                    features_found.append("chat_history")
        except:
            print("⚠️ Chat history items not found")
        
        # Folders/categories
        try:
            folders = await self.page.query_selector_all(".folder, .category, [data-testid='folder']")
            if folders:
                print(f"📁 Found: {len(folders)} folders/categories")
                features_found.append("folders")
        except:
            print("⚠️ Folders not found")
        
        # Settings/preferences
        try:
            settings = await self.page.query_selector("button:has-text('Settings'), [data-testid='settings'], .settings")
            if settings:
                print("⚙️ Found: Settings button")
                await settings.click()
                await asyncio.sleep(2)
                features_found.append("settings")
        except:
            print("⚠️ Settings button not found")
        
        return features_found
    
    async def explore_chat_features(self):
        """Explore chat-related features"""
        print("\n💬 Exploring Chat Features...")
        print("-" * 50)
        
        features_found = []
        
        # Model selector
        try:
            model_selector = await self.page.query_selector(".model-selector, [data-testid='model-selector'], button:has-text('Model')")
            if model_selector:
                print("🧠 Found: Model selector")
                await model_selector.click()
                await asyncio.sleep(2)
                features_found.append("model_selector")
        except:
            print("⚠️ Model selector not found")
        
        # File upload
        try:
            file_upload = await self.page.query_selector("input[type='file'], [data-testid='file-upload'], .file-upload")
            if file_upload:
                print("📎 Found: File upload")
                features_found.append("file_upload")
        except:
            print("⚠️ File upload not found")
        
        # Agent/assistant selector
        try:
            agent_buttons = await self.page.query_selector_all("button:has-text('Code'), button:has-text('Creative'), button:has-text('General')")
            if agent_buttons:
                print(f"🤖 Found: {len(agent_buttons)} agent/assistant buttons")
                for i, button in enumerate(agent_buttons[:3]):  # Test first 3
                    await button.click()
                    await asyncio.sleep(1)
                features_found.append("agent_selector")
        except:
            print("⚠️ Agent buttons not found")
        
        # Send message
        try:
            chat_input = await self.page.query_selector("textarea, input[placeholder*='message'], [contenteditable='true']")
            if chat_input:
                print("💭 Found: Chat input field")
                await chat_input.fill("Test message for API exploration")
                await asyncio.sleep(1)
                
                # Find send button
                send_button = await self.page.query_selector("button[type='submit'], button:has-text('Send'), [data-testid='send']")
                if send_button:
                    await send_button.click()
                    await asyncio.sleep(3)  # Wait for response
                    features_found.append("send_message")
        except:
            print("⚠️ Chat input/send not found")
        
        return features_found
    
    async def explore_advanced_features(self):
        """Explore advanced features like image generation, web search, etc."""
        print("\n🔬 Exploring Advanced Features...")
        print("-" * 50)
        
        features_found = []
        
        # Image generation
        try:
            image_gen = await self.page.query_selector("button:has-text('Image'), [data-testid='image-gen'], .image-generation")
            if image_gen:
                print("🎨 Found: Image generation")
                await image_gen.click()
                await asyncio.sleep(2)
                features_found.append("image_generation")
        except:
            print("⚠️ Image generation not found")
        
        # Web search toggle
        try:
            web_search = await self.page.query_selector("input[type='checkbox']:near-text('web'), .web-search-toggle")
            if web_search:
                print("🌐 Found: Web search toggle")
                await web_search.click()
                await asyncio.sleep(1)
                features_found.append("web_search")
        except:
            print("⚠️ Web search toggle not found")
        
        # Voice input
        try:
            voice_input = await self.page.query_selector("button:has-text('Voice'), [data-testid='voice'], .voice-input")
            if voice_input:
                print("🎤 Found: Voice input")
                features_found.append("voice_input")
        except:
            print("⚠️ Voice input not found")
        
        # Export/share chat
        try:
            export_button = await self.page.query_selector("button:has-text('Export'), button:has-text('Share'), [data-testid='export']")
            if export_button:
                print("📤 Found: Export/Share button")
                await export_button.click()
                await asyncio.sleep(2)
                features_found.append("export_share")
        except:
            print("⚠️ Export/Share not found")
        
        return features_found
    
    async def explore_user_features(self):
        """Explore user account and profile features"""
        print("\n👤 Exploring User Features...")
        print("-" * 50)
        
        features_found = []
        
        # User profile/avatar
        try:
            user_profile = await self.page.query_selector(".user-avatar, .profile-button, [data-testid='user-profile']")
            if user_profile:
                print("👤 Found: User profile")
                await user_profile.click()
                await asyncio.sleep(2)
                features_found.append("user_profile")
        except:
            print("⚠️ User profile not found")
        
        # Subscription/billing
        try:
            subscription = await self.page.query_selector("button:has-text('Upgrade'), button:has-text('Pro'), .subscription")
            if subscription:
                print("💳 Found: Subscription/billing")
                features_found.append("subscription")
        except:
            print("⚠️ Subscription features not found")
        
        # API keys/tokens
        try:
            api_keys = await self.page.query_selector("button:has-text('API'), .api-keys, [data-testid='api-keys']")
            if api_keys:
                print("🔑 Found: API keys section")
                await api_keys.click()
                await asyncio.sleep(2)
                features_found.append("api_keys")
        except:
            print("⚠️ API keys section not found")
        
        return features_found
    
    def analyze_captured_data(self):
        """Analyze all captured API calls and create comprehensive mapping"""
        print("\n📊 Analyzing Captured API Data...")
        print("=" * 60)
        
        # Process endpoints
        endpoint_summary = {}
        for path, data in self.api_endpoints.items():
            endpoint_summary[path] = {
                'methods': list(data['methods']),
                'call_count': len(data['examples']),
                'first_seen': data['examples'][0]['timestamp'] if data['examples'] else None
            }
        
        print(f"📈 Total unique endpoints discovered: {len(endpoint_summary)}")
        print(f"🔥 Total API calls captured: {len(self.captured_requests)}")
        
        # Show top endpoints
        sorted_endpoints = sorted(endpoint_summary.items(), key=lambda x: x[1]['call_count'], reverse=True)
        print(f"\n🏆 Top 10 Most Active Endpoints:")
        for i, (path, info) in enumerate(sorted_endpoints[:10], 1):
            methods = ", ".join(info['methods'])
            print(f"{i:2d}. {path:<40} [{methods}] ({info['call_count']} calls)")
        
        return {
            'endpoints': endpoint_summary,
            'total_calls': len(self.captured_requests),
            'raw_calls': self.captured_requests
        }
    
    def save_exploration_results(self, analysis_data: Dict, features_discovered: Dict):
        """Save exploration results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive API mapping
        api_file = f"/app/qwen_direct/docs/api_endpoints_{timestamp}.json"
        with open(api_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            serializable_data = {}
            for path, info in analysis_data['endpoints'].items():
                serializable_data[path] = {
                    'methods': info['methods'],
                    'call_count': info['call_count'],
                    'first_seen': info['first_seen']
                }
            json.dump(serializable_data, f, indent=2)
        
        # Save raw captured requests
        raw_file = f"/app/qwen_direct/docs/raw_requests_{timestamp}.json"
        with open(raw_file, 'w') as f:
            json.dump(analysis_data['raw_calls'], f, indent=2)
        
        # Save feature mapping
        features_file = f"/app/qwen_direct/docs/features_discovered_{timestamp}.json"
        with open(features_file, 'w') as f:
            json.dump(features_discovered, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   - API endpoints: {api_file}")
        print(f"   - Raw requests: {raw_file}")
        print(f"   - Features map: {features_file}")
    
    async def run_comprehensive_exploration(self):
        """Run complete feature exploration"""
        print("🎯 STARTING COMPREHENSIVE QWEN FEATURE EXPLORATION")
        print("=" * 60)
        
        if not await self.setup_browser():
            return False
        
        try:
            # Navigate to Qwen
            if not await self.navigate_to_qwen():
                return False
            
            print("\n⏱️ Waiting 5 seconds for initial page load and API calls...")
            await asyncio.sleep(5)
            
            # Explore all feature categories
            all_features = {}
            
            all_features['sidebar'] = await self.explore_sidebar_features()
            await asyncio.sleep(3)
            
            all_features['chat'] = await self.explore_chat_features()
            await asyncio.sleep(3)
            
            all_features['advanced'] = await self.explore_advanced_features()
            await asyncio.sleep(3)
            
            all_features['user'] = await self.explore_user_features()
            await asyncio.sleep(3)
            
            print("\n⏱️ Final wait for any remaining API calls...")
            await asyncio.sleep(5)
            
            # Analyze results
            analysis = self.analyze_captured_data()
            self.save_exploration_results(analysis, all_features)
            
            print(f"\n🎉 Exploration complete!")
            print(f"✅ Features discovered: {sum(len(v) for v in all_features.values())}")
            print(f"✅ API endpoints mapped: {len(analysis['endpoints'])}")
            print(f"✅ Total network calls: {analysis['total_calls']}")
            
            return True
            
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            print("🧹 Browser cleanup complete")

async def main():
    """Main exploration function"""
    explorer = QwenFeatureExplorer()
    success = await explorer.run_comprehensive_exploration()
    
    if success:
        print("\n🏆 FEATURE EXPLORATION MISSION COMPLETE!")
        print("Check the /app/qwen_direct/docs/ directory for detailed results.")
    else:
        print("\n❌ Exploration failed. Check authentication and connection.")

if __name__ == "__main__":
    asyncio.run(main())