#!/usr/bin/env python3
"""
Live Session Analyzer for Qwen API
Mission: Use authenticated browser session to observe API calls in real-time
"""

import asyncio
import json
from playwright.async_api import async_playwright
from typing import Dict, List, Any
import sys
import time

class QwenLiveAnalyzer:
    def __init__(self, storage_state_path: str):
        self.storage_state_path = storage_state_path
        self.captured_requests = []
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup_browser(self, headless: bool = False):
        """Initialize authenticated browser session"""
        print(f"[*] Setting up authenticated browser session...")
        print(f"[*] Using storage state: {self.storage_state_path}")
        
        playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Create context with stored authentication
        try:
            self.context = await self.browser.new_context(
                storage_state=self.storage_state_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        except FileNotFoundError:
            print(f"[!] Storage state file not found: {self.storage_state_path}")
            await self.browser.close()
            return False
        except Exception as e:
            print(f"[!] Error loading storage state: {e}")
            await self.browser.close()
            return False
        
        # Create page and setup request interception
        self.page = await self.context.new_page()
        
        # Intercept all requests to capture API calls
        self.page.on("request", self._capture_request)
        self.page.on("response", self._capture_response)
        
        print(f"[+] Browser session ready")
        return True
    
    def _capture_request(self, request):
        """Capture outgoing requests"""
        url = request.url
        method = request.method
        headers = request.headers
        
        # Check if this looks like an API call
        if self._is_api_request(url):
            request_data = {
                'type': 'request',
                'url': url,
                'method': method,
                'headers': headers,
                'timestamp': time.time(),
                'post_data': None
            }
            
            # Capture POST data if available
            if method.upper() == 'POST' and request.post_data:
                try:
                    request_data['post_data'] = json.loads(request.post_data)
                except:
                    request_data['post_data'] = request.post_data
            
            self.captured_requests.append(request_data)
            
            # Real-time logging
            auth_header = headers.get('authorization', '')
            auth_status = "🔑" if auth_header else "🚫"
            print(f"[REQ] {auth_status} {method} {url}")
    
    def _capture_response(self, response):
        """Capture API responses"""
        request = response.request
        url = request.url
        
        if self._is_api_request(url):
            status = response.status
            status_emoji = "✅" if 200 <= status < 300 else "❌" if status >= 400 else "⚠️"
            print(f"[RES] {status_emoji} {status} {url}")
    
    def _is_api_request(self, url: str) -> bool:
        """Check if URL is an API endpoint"""
        api_indicators = [
            '/api/', '/v1/', '/conversation/', '/chat/', '/message/',
            '/completion/', '/generate/', '/stream/', 'qwen.ai'
        ]
        return any(indicator in url.lower() for indicator in api_indicators)
    
    async def navigate_to_qwen(self):
        """Navigate to Qwen chat interface"""
        print(f"[*] Navigating to Qwen chat interface...")
        try:
            await self.page.goto("https://chat.qwen.ai/", wait_until="networkidle")
            print(f"[+] Successfully loaded Qwen chat page")
            
            # Wait for any initial API calls to complete
            await asyncio.sleep(2)
            
            # Check if we're authenticated by looking for chat interface elements
            chat_input = await self.page.query_selector("textarea, input[placeholder*='message'], [contenteditable='true']")
            if chat_input:
                print(f"[+] Chat interface detected - authentication appears successful")
            else:
                print(f"[!] Chat interface not found - may need to authenticate")
            
            return True
        except Exception as e:
            print(f"[!] Error navigating to Qwen: {e}")
            return False
    
    async def send_test_message(self, message: str = "Hello, this is a test message from the API analyzer."):
        """Send a test message to trigger API calls"""
        print(f"[*] Attempting to send test message: {message}")
        
        # Clear previous captures
        self.captured_requests.clear()
        
        try:
            # Look for chat input field with various possible selectors
            selectors = [
                "textarea[placeholder*='message']",
                "input[placeholder*='message']",
                "[contenteditable='true']",
                "textarea",
                ".chat-input textarea",
                "#chat-input"
            ]
            
            chat_input = None
            for selector in selectors:
                chat_input = await self.page.query_selector(selector)
                if chat_input:
                    print(f"[+] Found chat input with selector: {selector}")
                    break
            
            if not chat_input:
                print(f"[!] Could not find chat input field")
                return False
            
            # Type the message
            await chat_input.fill(message)
            print(f"[+] Message typed into input field")
            
            # Look for send button
            send_selectors = [
                "button[type='submit']",
                "button:has-text('Send')",
                "button:has-text('发送')",
                "[role='button']:has-text('Send')",
                ".send-button",
                "button:last-child"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = await self.page.query_selector(selector)
                    if send_button:
                        print(f"[+] Found send button with selector: {selector}")
                        break
                except:
                    continue
            
            if send_button:
                await send_button.click()
                print(f"[+] Send button clicked")
            else:
                # Try pressing Enter as fallback
                await chat_input.press("Enter")
                print(f"[+] Pressed Enter to send message")
            
            # Wait for API response
            print(f"[*] Waiting for API response...")
            await asyncio.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"[!] Error sending test message: {e}")
            return False
    
    async def interactive_mode(self):
        """Enter interactive mode for manual testing"""
        print(f"\n{'='*80}")
        print(f"INTERACTIVE MODE ACTIVATED")
        print(f"{'='*80}")
        print(f"The browser is now open. You can:")
        print(f"1. Manually interact with the Qwen chat interface")
        print(f"2. All API calls will be captured and displayed in real-time")
        print(f"3. Press Enter in this terminal to stop monitoring")
        print(f"{'='*80}")
        
        # Keep the session alive for manual interaction
        input("Press Enter to stop monitoring...")
    
    def print_captured_summary(self):
        """Print summary of captured API calls"""
        if not self.captured_requests:
            print(f"[!] No API requests captured")
            return
        
        print(f"\n{'='*80}")
        print(f"CAPTURED API CALLS SUMMARY")
        print(f"{'='*80}")
        print(f"Total requests captured: {len(self.captured_requests)}")
        
        for i, req in enumerate(self.captured_requests):
            auth_status = "🔑 AUTH" if req['headers'].get('authorization') else "🚫 NO AUTH"
            post_indicator = "📤 POST DATA" if req.get('post_data') else ""
            print(f"[{i:02d}] {req['method']} - {auth_status} {post_indicator}")
            print(f"     {req['url']}")
            
            if req.get('post_data'):
                print(f"     Payload: {str(req['post_data'])[:100]}...")
    
    async def cleanup(self):
        """Close browser and cleanup resources"""
        if self.browser:
            await self.browser.close()
            print(f"[+] Browser session closed")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python live_session_analyzer.py <storage_state.json> [mode]")
        print("Modes:")
        print("  test     - Send test message and capture API calls")
        print("  manual   - Open browser for manual interaction")
        return
    
    storage_state_file = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'test'
    
    analyzer = QwenLiveAnalyzer(storage_state_file)
    
    # Setup browser (non-headless for manual mode)
    headless = mode != 'manual'
    if not await analyzer.setup_browser(headless=headless):
        return
    
    try:
        # Navigate to Qwen
        if await analyzer.navigate_to_qwen():
            
            if mode == 'test':
                # Send test message to capture API calls
                await analyzer.send_test_message()
                analyzer.print_captured_summary()
                
            elif mode == 'manual':
                # Enter interactive mode
                await analyzer.interactive_mode()
                analyzer.print_captured_summary()
        
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())