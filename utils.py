# c:\Users\itspr\DailyQuest\Qwen\utils.py
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, PlaywrightContextManager
from playwright_stealth import Stealth

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent
STATE_FILE = PROJECT_ROOT / "storage_state.json"
QWEN_URL = "https://chat.qwen.ai/"
ERROR_SCREENSHOT_PATH = PROJECT_ROOT / "error_screenshot.png"
ERROR_HTML_PATH = PROJECT_ROOT / "error_page.html"

async def setup_browser_page(p: PlaywrightContextManager, headless: bool = False) -> tuple[Browser, Page]:
    """
    Handles the common boilerplate for setting up a Playwright browser and page.
    - Launches a Chromium browser.
    - Loads authentication state from a file.
    - Applies stealth measures to avoid detection.
    - Navigates to the Qwen chat URL.
    - Waits for the page to finish loading.

    Args:
        p: The async_playwright context manager.
        headless: Whether to run the browser in headless mode.

    Returns:
        A tuple containing the browser and page objects.
        
    Raises:
        FileNotFoundError: If the authentication state file does not exist.
    """
    if not STATE_FILE.exists():
        raise FileNotFoundError(
            f"Authentication file not found at '{STATE_FILE}'. "
            "Please run `receive_auth_state.py` and use the extension to save your session."
        )

    print("[*] Launching browser with saved authentication state...")
    browser = await p.chromium.launch(headless=headless)
    context = await browser.new_context(storage_state=str(STATE_FILE))

    print("[*] Applying stealth to browser context...")
    await Stealth().apply_stealth_async(context)

    page = await context.new_page()

    print(f"[*] Navigating to {QWEN_URL}...")
    await page.goto(QWEN_URL, wait_until="domcontentloaded")

    print("[*] Waiting for page to load and be idle...")
    await page.wait_for_load_state("networkidle")
    print("[*] Page is idle.")
    
    return browser, page

async def save_error_state(page: Page):
    """
    Saves a screenshot and the full page HTML for debugging purposes.
    Inspired by snapdom's approach to capturing page state on failure.
    """
    print(f"[!] Saving screenshot to '{ERROR_SCREENSHOT_PATH}'")
    await page.screenshot(path=ERROR_SCREENSHOT_PATH, full_page=True)
    
    print(f"[!] Saving page HTML to '{ERROR_HTML_PATH}'")
    html_content = await page.content()
    with open(ERROR_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)