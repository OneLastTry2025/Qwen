#!/usr/bin/env python3
"""
HAR File Analysis Tool for Qwen API Reverse Engineering
Mission: Extract API endpoints, authentication tokens, and request patterns
"""

import json
import sys
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re

class QwenHARAnalyzer:
    def __init__(self, har_file_path: str):
        self.har_file_path = har_file_path
        self.har_data = None
        self.api_requests = []
        
    def load_har_file(self) -> bool:
        """Load and parse the HAR file"""
        try:
            print(f"[*] Loading HAR file: {self.har_file_path}")
            with open(self.har_file_path, 'r', encoding='utf-8') as f:
                self.har_data = json.load(f)
            print(f"[+] HAR file loaded successfully")
            return True
        except FileNotFoundError:
            print(f"[!] HAR file not found: {self.har_file_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"[!] Invalid JSON in HAR file: {e}")
            return False
        except Exception as e:
            print(f"[!] Error loading HAR file: {e}")
            return False
    
    def is_api_request(self, url: str) -> bool:
        """Determine if a URL is likely an API endpoint"""
        api_patterns = [
            r'/api/',
            r'/v\d+/',
            r'/conversation/',
            r'/chat/',
            r'/message/',
            r'/completion/',
            r'/generate/',
            r'/stream/',
            r'\.json$',
            r'/graphql',
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def extract_auth_token(self, headers: List[Dict]) -> Optional[str]:
        """Extract authentication token from headers"""
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'authorization':
                if value.startswith('Bearer '):
                    return value
                elif value.startswith('sk-'):
                    return f"Bearer {value}"
            elif name == 'x-api-key' and value:
                return value
        return None
    
    def analyze_entries(self) -> None:
        """Analyze all HAR entries for API patterns"""
        if not self.har_data:
            print("[!] No HAR data loaded")
            return
        
        entries = self.har_data.get('log', {}).get('entries', [])
        print(f"[*] Analyzing {len(entries)} HAR entries...")
        
        for i, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            url = request.get('url', '')
            method = request.get('method', '')
            status = response.get('status', 0)
            headers = request.get('headers', [])
            
            # Check if this looks like an API request
            if self.is_api_request(url):
                auth_token = self.extract_auth_token(headers)
                
                # Extract POST data if available
                post_data = None
                if method.upper() == 'POST':
                    post_data_raw = request.get('postData', {})
                    if post_data_raw.get('text'):
                        try:
                            post_data = json.loads(post_data_raw.get('text', ''))
                        except:
                            post_data = post_data_raw.get('text', '')
                
                api_request = {
                    'index': i,
                    'url': url,
                    'method': method,
                    'status': status,
                    'headers': headers,
                    'auth_token': auth_token,
                    'post_data': post_data,
                    'domain': urlparse(url).netloc
                }
                
                self.api_requests.append(api_request)
    
    def print_summary(self) -> None:
        """Print a summary of discovered API endpoints"""
        print(f"\n{'='*80}")
        print(f"QWEN API INTELLIGENCE REPORT")
        print(f"{'='*80}")
        print(f"Total API requests found: {len(self.api_requests)}")
        
        if not self.api_requests:
            print("[!] No API requests discovered. Check HAR file content.")
            return
        
        # Group by domain
        domains = {}
        for req in self.api_requests:
            domain = req['domain']
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(req)
        
        for domain, requests in domains.items():
            print(f"\n[DOMAIN] {domain}")
            print(f"  Requests: {len(requests)}")
            
            for req in requests[:10]:  # Show first 10 per domain
                auth_status = "✓ AUTH" if req['auth_token'] else "✗ NO AUTH"
                post_indicator = "📤 POST" if req['post_data'] else ""
                print(f"  [{req['index']:03d}] {req['method']} {req['status']} - {auth_status} {post_indicator}")
                print(f"       {req['url']}")
    
    def print_detailed_request(self, index: int) -> None:
        """Print detailed information about a specific request"""
        request = next((r for r in self.api_requests if r['index'] == index), None)
        if not request:
            print(f"[!] Request index {index} not found")
            return
        
        print(f"\n{'='*80}")
        print(f"DETAILED REQUEST ANALYSIS - Index {index}")
        print(f"{'='*80}")
        print(f"URL: {request['url']}")
        print(f"Method: {request['method']}")
        print(f"Status: {request['status']}")
        
        if request['auth_token']:
            print(f"\n[AUTH TOKEN FOUND]")
            print(f"{request['auth_token']}")
        
        print(f"\n[HEADERS]")
        for header in request['headers']:
            name = header.get('name', '')
            value = header.get('value', '')
            if 'authorization' in name.lower() or 'token' in name.lower():
                print(f"  {name}: {value[:50]}..." if len(value) > 50 else f"  {name}: {value}")
            else:
                print(f"  {name}: {value}")
        
        if request['post_data']:
            print(f"\n[REQUEST PAYLOAD]")
            if isinstance(request['post_data'], dict):
                print(json.dumps(request['post_data'], indent=2))
            else:
                print(request['post_data'])
    
    def generate_curl_command(self, index: int) -> str:
        """Generate a curl command for testing the API endpoint"""
        request = next((r for r in self.api_requests if r['index'] == index), None)
        if not request:
            return f"# Request index {index} not found"
        
        curl_parts = [f"curl '{request['url']}'"]
        curl_parts.append(f"  -X '{request['method']}'")
        
        # Add headers
        for header in request['headers']:
            name = header.get('name', '')
            value = header.get('value', '')
            # Skip some headers that curl adds automatically
            if name.lower() in ['host', 'content-length', 'connection']:
                continue
            curl_parts.append(f"  -H '{name}: {value}'")
        
        # Add POST data
        if request['post_data'] and request['method'].upper() == 'POST':
            if isinstance(request['post_data'], dict):
                data = json.dumps(request['post_data'], separators=(',', ':'))
                curl_parts.append(f"  --data-raw '{data}'")
            else:
                curl_parts.append(f"  --data-raw '{request['post_data']}'")
        
        return ' \\\n'.join(curl_parts)
    
    def find_chat_endpoints(self) -> List[Dict]:
        """Find endpoints specifically related to chat functionality"""
        chat_requests = []
        chat_patterns = [
            r'/chat',
            r'/conversation',
            r'/message',
            r'/completion',
            r'/generate',
            r'/stream'
        ]
        
        for req in self.api_requests:
            url = req['url'].lower()
            for pattern in chat_patterns:
                if re.search(pattern, url):
                    chat_requests.append(req)
                    break
        
        return chat_requests

def main():
    if len(sys.argv) < 2:
        print("Usage: python har_analyzer.py <har_file> [command] [index]")
        print("Commands:")
        print("  summary (default) - Show API endpoints summary")
        print("  detail <index>    - Show detailed request info")
        print("  curl <index>      - Generate curl command")
        print("  chat              - Show chat-related endpoints only")
        return
    
    har_file = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    
    analyzer = QwenHARAnalyzer(har_file)
    
    if not analyzer.load_har_file():
        return
    
    analyzer.analyze_entries()
    
    if command == 'summary':
        analyzer.print_summary()
    elif command == 'detail' and len(sys.argv) > 3:
        try:
            index = int(sys.argv[3])
            analyzer.print_detailed_request(index)
        except ValueError:
            print("[!] Invalid index. Must be a number.")
    elif command == 'curl' and len(sys.argv) > 3:
        try:
            index = int(sys.argv[3])
            print(analyzer.generate_curl_command(index))
        except ValueError:
            print("[!] Invalid index. Must be a number.")
    elif command == 'chat':
        chat_requests = analyzer.find_chat_endpoints()
        print(f"\n[CHAT ENDPOINTS] Found {len(chat_requests)} chat-related requests:")
        for req in chat_requests:
            auth_status = "✓ AUTH" if req['auth_token'] else "✗"
            print(f"  [{req['index']:03d}] {req['method']} {req['status']} {auth_status} - {req['url']}")
    else:
        print(f"[!] Unknown command: {command}")

if __name__ == "__main__":
    main()