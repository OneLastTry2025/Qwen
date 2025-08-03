# Full Qwen API server with browser automation - adapted for supervisor
import asyncio
import os
import uuid
from pathlib import Path
from quart import Quart, request, jsonify, send_from_directory, current_app
from quart_cors import cors
from playwright.async_api import async_playwright, Browser, Page, Playwright
from playwright_stealth import Stealth
from utils import save_error_state, QWEN_URL, STATE_FILE

# --- Browser and Page Management ---
class BrowserManager:
    """Manages a persistent browser instance and a pool of pages for concurrent requests."""
    def __init__(self, pool_size=3):
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page_pool: asyncio.Queue = None
        self.pool_size = pool_size

    async def initialize(self):
        print("[*] Initializing browser manager...")
        if not STATE_FILE.exists():
            raise FileNotFoundError(
                f"Authentication file not found at '{STATE_FILE}'. "
                "Please run `receive_auth_state.py` and use the extension to save your session."
            )
        
        self.playwright = await async_playwright().start()
        print("[*] Launching persistent browser (this may take a moment)...")
        self.browser = await self.playwright.chromium.launch(headless=True)
        
        context = await self.browser.new_context(storage_state=str(STATE_FILE))
        
        print("[*] Applying stealth to browser context...")
        await Stealth().apply_stealth_async(context)
        
        self.page_pool = asyncio.Queue(maxsize=self.pool_size)
        for i in range(self.pool_size):
            print(f"[*] Creating page {i+1}/{self.pool_size} for the pool...")
            page = await context.new_page()
            await page.goto(QWEN_URL, wait_until="domcontentloaded")
            await self.page_pool.put(page)
        print(f"[+] Browser and a pool of {self.pool_size} pages initialized successfully.")

    async def get_page(self) -> Page:
        print("[*] Acquiring a page from the pool...")
        page = await self.page_pool.get()
        print("[+] Page acquired.")
        return page

    def release_page(self, page: Page):
        print("[*] Releasing page back to the pool...")
        self.page_pool.put_nowait(page)
        print("[+] Page released.")

    async def shutdown(self):
        print("[*] Shutting down browser manager...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("[+] Shutdown complete.")

# --- Global Browser Manager Instance ---
browser_manager = BrowserManager(pool_size=3)

# --- Quart App ---
app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.before_serving
async def startup():
    await browser_manager.initialize()

@app.after_serving
async def shutdown():
    await browser_manager.shutdown()

# --- Core Chat Logic ---
async def ask_qwen(page: Page, prompt: str, chat_id: str = None, use_web_search: bool = False, file_paths: list = None, agent_name: str = None, model_name: str = None) -> dict:
    """
    Uses a pre-existing browser page to send a prompt to Qwen and return the response.
    """
    try:
        if chat_id:
            # We have a specific chat to continue
            target_url = f"{QWEN_URL}c/{chat_id}"
            # Navigate only if we are not already on the correct chat page
            if not page.url.startswith(target_url):
                print(f"[*] Navigating to existing chat: {target_url}")
                await page.goto(target_url, wait_until="networkidle")
        else:
            # We want a new chat.
            # If we are currently in an old chat, click the "New Chat" button to start fresh.
            if "/c/" in page.url or QWEN_URL in page.url:
                print("[*] Currently in a chat, clicking 'New Chat' to start a new one...")
                await page.locator("#sidebar-new-chat-button").click()
                # The click should navigate to a new chat URL. We wait for that to happen.
                try:
                    await page.wait_for_url(f"{QWEN_URL}c/*", wait_until="load", timeout=15000)
                except Exception as e:
                    print(f"[!] Error waiting for new chat URL: {e}")
                    await save_error_state(page)
            else:
                # We are on the homepage, ready for a new chat.
                print("[*] On homepage, will start a new chat directly.")

            # Handle Model Selection
            if model_name:
                print(f"[*] Switching to model: {model_name}")
                try:
                    model_selector_button = page.locator('#model-selector-button')
                    await model_selector_button.click()
                    dropdown_menu = page.locator('div[role="menu"]')
                    await dropdown_menu.wait_for(state="visible", timeout=10000)
                    await dropdown_menu.locator(f'a:has-text("{model_name}")').click()
                    await dropdown_menu.wait_for(state="hidden", timeout=5000)
                    print(f"[+] Switched to model '{model_name}' successfully.")
                except Exception as e:
                    print(f"[!] Could not switch model to '{model_name}'. Error: {e}")

            # Handle Agent Activation
            if agent_name:
                print(f"[*] Activating agent: {agent_name}")
                try:
                    action_buttons_container = page.locator('div.chat-recommend-txt-container')
                    agent_button = action_buttons_container.locator(f'button:has-text("{agent_name}")')
                    await agent_button.click(timeout=10000)
                except Exception as e:
                    print(f"[!] Could not activate agent '{agent_name}'. It might not be available on the page. Error: {e}")

            # Handle Web Search Toggle - This should only be done for new chats.
            try:
                search_button = page.locator('button.websearch_button')
                await search_button.wait_for(state="visible", timeout=10000)
                is_search_active = await search_button.get_attribute('aria-pressed') == 'true'

                if use_web_search and not is_search_active:
                    print("[*] Web search requested and is not active. Clicking to enable.")
                    await search_button.click()
                elif not use_web_search and is_search_active:
                    print("[*] Web search is not requested and is active. Clicking to disable.")
                    await search_button.click()
                else:
                    print(f"[*] Web search state is already as requested (active: {is_search_active}).")
            except Exception as e:
                print(f"[!] Could not toggle web search (button might not be present): {e}")

        # Handle file attachments
        if file_paths:
            print(f"[*] Attaching {len(file_paths)} file(s)...")
            # The Qwen UI has a hidden file input that is used for uploads.
            file_input_selector = 'input#filesUpload'
            # We need to make sure the file chooser is ready, which can be done by clicking the attachment button.
            await page.locator('button.chat-prompt-upload-group-btn').click()
            await page.locator(file_input_selector).set_input_files(file_paths)
            # Wait for the UI to show the attachment.
            await page.locator('div[class*="_fileItem_"]').first.wait_for(state="visible", timeout=30000)
            print("[+] Files attached successfully.")

        chat_input = page.locator("textarea#chat-input")
        await chat_input.wait_for(timeout=30000)
        if prompt:
            await chat_input.fill(prompt)
        await chat_input.press('Enter')
        
        print("[*] Waiting for the new response to finish generating...")
        # Waiting for the "Thinking" button to disappear can be unreliable.
        # A better approach is to wait for the response controls (like the regenerate button)
        # to appear in the last message bubble, which confirms the response is fully rendered.
        last_response_container = page.locator('.response-meesage-container').last
        regenerate_button = last_response_container.locator("button.regenerate-response-button")
        await regenerate_button.wait_for(state="visible", timeout=90000)
        print("[+] Response finished.")
        
        response_text = await last_response_container.locator('.markdown-content-container').inner_text()
        
        # Extract the new or existing chat_id from the URL
        current_chat_id = page.url.split('/c/')[1].split('?')[0]
        print(f"[+] Response received for chat_id: {current_chat_id}")
        return {"status": "success", "response": response_text, "chat_id": current_chat_id}

    except Exception as e:
        print(f"\n[!] An error occurred during automation: {e}")
        await save_error_state(page)
        return {"status": "error", "message": str(e)}
    finally:
        # Clean up any temporary files that were uploaded
        if file_paths:
            for path in file_paths:
                try:
                    os.remove(path)
                    print(f"[*] Cleaned up temporary file: {path}")
                except OSError as e:
                    print(f"[!] Error cleaning up file {path}: {e}")

# --- Core Image Generation Logic ---
async def generate_qwen_image(page: Page, prompt: str) -> dict:
    """
    Uses a pre-existing browser page to generate an image from a prompt.
    """
    try:
        # To get to the action buttons, we must be on a "new chat" screen.
        # If we are in an existing chat, click "New Chat".
        if "/c/" in page.url:
            print("[*] Currently in a chat, clicking 'New Chat' to access action buttons...")
            await page.locator("#sidebar-new-chat-button").click()
            # Wait for the URL to change to a new chat, which indicates the page has reset.
            try:
                await page.wait_for_url(f"{QWEN_URL}c/*", timeout=15000)
            except Exception as e:
                print(f"[!] Error waiting for new chat URL: {e}")
                await save_error_state(page)

        print("[*] Clicking 'Image Generation' action button...")
        action_buttons_container = page.locator('div.chat-recommend-txt-container')
        image_gen_button = action_buttons_container.locator('button:has-text("Image Generation")')
        await image_gen_button.wait_for(timeout=15000)
        await image_gen_button.click()

        chat_input = page.locator("textarea#chat-input")
        await chat_input.wait_for(timeout=30000)
        
        print(f"[*] Filling image prompt: \"{prompt}\"")
        await chat_input.fill(prompt)
        await chat_input.press('Enter')

        print("[*] Waiting for the image to be generated...")
        last_response_container = page.locator('.response-meesage-container').last
        
        # Wait for an image tag with a blob or http src to be present.
        generated_image = last_response_container.locator("#response-content-container img[src^='blob'], #response-content-container img[src^='http']:not([src*='image_generating.png'])")
        await generated_image.wait_for(state="visible", timeout=120000)
        
        image_url = await generated_image.get_attribute("src")
        print(f"[+] Image generated successfully: {image_url}")

        current_chat_id = page.url.split('/c/')[1].split('?')[0]
        return {"status": "success", "image_url": image_url, "chat_id": current_chat_id}

    except Exception as e:
        print(f"\n[!] An error occurred during image generation: {e}")
        await save_error_state(page)
        return {"status": "error", "message": str(e)}

# --- Core Model Fetching Logic ---
async def get_available_models(page: Page) -> dict:
    """
    Clicks the model selector and scrapes the list of available models.
    """
    try:
        print("[*] Fetching available models...")
        model_selector_button = page.locator('#model-selector-button')
        await model_selector_button.click()

        # Wait for the dropdown menu to appear
        dropdown_menu = page.locator('div[role="menu"]')
        await dropdown_menu.wait_for(state="visible", timeout=10000)

        model_items = dropdown_menu.locator('a[role="menuitem"]')
        count = await model_items.count()
        models = [await model_items.nth(i).inner_text() for i in range(count)]
        
        print(f"[+] Found {len(models)} models: {models}")
        # Click somewhere to close the dropdown
        await page.locator('body').click()
        return {"status": "success", "models": models}
    except Exception as e:
        print(f"\n[!] An error occurred while fetching models: {e}")
        await save_error_state(page)
        return {"status": "error", "message": str(e)}

# --- API Endpoints with /api prefix ---
@app.route('/api/chat', methods=['POST'])
async def chat_handler():
    # Handle both JSON and multipart/form-data requests
    if 'multipart/form-data' in request.content_type:
        form = await request.form
        files = await request.files
        prompt = form.get('prompt', '')
        chat_id = form.get('chat_id')
        use_web_search = form.get('use_web_search', 'false').lower() == 'true'
        agent_name = form.get('agent_name')
        model_name = form.get('model_name')
        
        uploaded_files = files.getlist('files')
        file_paths = []
        if uploaded_files:
            # Create a temporary directory for uploads if it doesn't exist
            temp_dir = Path(current_app.root_path) / "temp_uploads"
            temp_dir.mkdir(exist_ok=True)
            
            for file in uploaded_files:
                # Use a unique filename to avoid collisions
                filename = f"{uuid.uuid4()}_{file.filename}"
                path = temp_dir / filename
                await file.save(path)
                file_paths.append(str(path))
    else:
        # Original JSON handling for requests without files
        data = await request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"status": "error", "message": "Missing 'prompt' in request body"}), 400
        prompt = data['prompt']
        chat_id = data.get('chat_id')
        use_web_search = data.get('use_web_search', False)
        agent_name = data.get('agent_name')
        model_name = data.get('model_name')
        file_paths = None

    if not prompt and not file_paths:
        return jsonify({"status": "error", "message": "Request must contain a 'prompt' or files"}), 400

    print(f"[*] Received request for chat_id: {chat_id}, prompt: \"{prompt[:50]}...\", agent: {agent_name}, model: {model_name}, files: {len(file_paths) if file_paths else 0}")

    page = await browser_manager.get_page()
    try:
        result = await ask_qwen(page, prompt, chat_id, use_web_search, file_paths, agent_name, model_name)
    finally:
        browser_manager.release_page(page)

    return jsonify(result), 200 if result['status'] == 'success' else 500

@app.route('/api/image', methods=['POST'])
async def image_handler():
    """
    API endpoint to handle image generation requests.
    """
    data = await request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"status": "error", "message": "Missing 'prompt' in request body"}), 400

    prompt = data['prompt']
    print(f"[*] Received request for /api/image: \"{prompt[:50]}...\"")

    page = await browser_manager.get_page()
    try:
        result = await generate_qwen_image(page, prompt)
    finally:
        browser_manager.release_page(page)

    return jsonify(result), 200 if result['status'] == 'success' else 500

@app.route('/api/history', methods=['GET'])
async def history_handler():
    """
    API endpoint to fetch the user's chat history.
    """
    page = await browser_manager.get_page()
    try:
        print("[*] Fetching chat history...")
        # Ensure we are on a page where the sidebar is visible by navigating to the base URL
        if "/c/" not in page.url:
            await page.goto(QWEN_URL, wait_until="networkidle")

        history_items_selector = 'div.session-list a.chat-item-drag-link'
        history_items = page.locator(history_items_selector)
        try:
            await history_items.first.wait_for(state="visible", timeout=15000)
        except Exception as e:
            print(f"[!] Error waiting for history items: {e}")
            await save_error_state(page)

        count = await history_items.count()
        history = []
        for i in range(count):
            item = history_items.nth(i)
            title_element = item.locator('.chat-item-drag-link-content-tip-text')
            title = await title_element.inner_text()
            href = await item.get_attribute('href')
            chat_id = href.split('/c/')[-1]
            history.append({"id": chat_id, "title": title.strip()})
        
        print(f"[+] Found {len(history)} chat sessions.")
        result = {"status": "success", "history": history}
    except Exception as e:
        print(f"\n[!] An error occurred while fetching history: {e}")
        await save_error_state(page)
        result = {"status": "error", "message": str(e)}
    finally:
        browser_manager.release_page(page)
    
    return jsonify(result), 200 if result['status'] == 'success' else 500

@app.route('/api/model', methods=['GET'])
async def model_handler():
    """
    API endpoint to fetch the current model name.
    """
    page = await browser_manager.get_page()
    try:
        print("[*] Fetching model information...")
        model_selector_button = page.locator('div[class*="no-translate"] button')
        await model_selector_button.wait_for(state="visible", timeout=15000)
        model_name = await model_selector_button.inner_text()
        result = {"status": "success", "model_name": model_name.strip()}
    except Exception as e:
        print(f"\n[!] An error occurred while fetching model info: {e}")
        await save_error_state(page)
        result = {"status": "error", "message": str(e)}
    finally:
        browser_manager.release_page(page)
    return jsonify(result), 200 if result['status'] == 'success' else 500

@app.route('/api/models', methods=['GET'])
async def models_handler():
    """
    API endpoint to fetch the list of available models.
    """
    page = await browser_manager.get_page()
    try:
        result = await get_available_models(page)
    except Exception as e:
        result = {"status": "error", "message": str(e)}
    finally:
        browser_manager.release_page(page)
    return jsonify(result), 200 if result['status'] == 'success' else 500

# --- Frontend Serving ---
@app.route('/')
async def serve_index():
    # Serve the index.html from the ui_clone subfolder
    return await send_from_directory('ui_clone', 'index.html')

@app.route('/assets/<path:filename>')
async def serve_assets(filename):
    """Serves static files from the ui_clone/assets directory."""
    return await send_from_directory(Path('ui_clone') / 'assets', filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001)