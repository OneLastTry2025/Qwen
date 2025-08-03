# c:\Users\itspr\DailyQuest\Qwen\send_message.py
import requests
import json

# The URL of your new local API server
API_BASE_URL = "http://127.0.0.1:5000"

def send_request(endpoint, payload):
    """
    Sends a request to a specified endpoint on the API server.
    """
    url = f"{API_BASE_URL}{endpoint}"
    print(f"[*] Sending request to {url} with payload: {payload}")

    try:
        # Make the POST request to your Flask server
        response = requests.post(url, json=payload, timeout=180) # Increased timeout for Playwright
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response from the server
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"\n[!] An error occurred while contacting the API server: {e}")
        print("[!] Please ensure the `api_server.py` is running.")
    except json.JSONDecodeError:
        print("\n[!] Failed to decode JSON response from the server.")
        print(f"[!] Raw response: {response.text if 'response' in locals() else 'No response object'}")
    
    return None

def main():
    """
    Starts an interactive session with the Qwen API server.
    Supports chat and image generation commands.
    """
    print("Starting interactive session with Qwen.")
    print(" - For chat, just type your message.")
    print(" - For image generation, type: /image <your prompt>")
    print(" - Type 'exit' or 'quit' to end.")
    
    chat_id = None
    while True:
        try:
            prompt = input("You: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ['exit', 'quit']:
                print("Ending session.")
                break

            endpoint = "/chat"
            actual_prompt = prompt
            
            if prompt.lower().startswith("/image "):
                endpoint = "/image"
                actual_prompt = prompt[7:].strip()
                if not actual_prompt:
                    print("[!] Please provide a prompt for image generation.")
                    continue
                payload = {"prompt": actual_prompt}
            else:
                payload = {"prompt": actual_prompt, "chat_id": chat_id}

            data = send_request(endpoint, payload)
            
            if data and data.get("status") == "success":
                if endpoint == "/image":
                    print(f"\nQwen Image: {data.get('image_url')}\n")
                else:
                    print(f"\nQwen: {data.get('response')}\n")
                
                chat_id = data.get("chat_id")
            elif data:
                print(f"\n[!] API server returned an error: {data.get('message')}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nEnding session.")
            break

if __name__ == "__main__":
    main()