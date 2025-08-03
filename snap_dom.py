import asyncio
from playwright.async_api import async_playwright
from utils import setup_browser_page, save_error_state
import pyperclip
import bs4

# --- Configuration ---
# Change this selector to target different parts of the UI
TARGET_SELECTOR = ".flex.h-full.w-full.items-center.overflow-auto"
# You can find selectors using the browser's DevTools (F12 -> Inspect)

async def snap_dom():
    """
    Launches a browser, navigates to Qwen, finds a target element,
    and prints its detailed HTML structure (SnapDOM) to the console.
    """
    browser = None
    print("--- SnapDOM UI Capture Script ---")
    async with async_playwright() as p:
        try:
            browser, page = await setup_browser_page(p, headless=True)

            print(f"\n[*] Attempting to capture the DOM for selector: '{TARGET_SELECTOR}'")
            
            target_element = page.locator(TARGET_SELECTOR).first
            await target_element.wait_for(state="visible", timeout=20000)
            
            print("[+] Target element found on the page.")
            
            # Get the outer HTML of the element
            dom_snapshot = await target_element.evaluate("element => element.outerHTML")
            
            # Clean up the snapshot for better readability
            soup = bs4.BeautifulSoup(dom_snapshot, 'html.parser')
            pretty_dom = soup.prettify()

            print("\n" + "="*20 + " DOM Snapshot (Copied to Clipboard) " + "="*20)
            print(pretty_dom)
            print("="*60)

            # Copy to clipboard for convenience
            try:
                pyperclip.copy(pretty_dom)
                print("\n[+] The HTML snapshot has been copied to your clipboard.")
            except pyperclip.PyperclipException:
                print("\n[!] Pyperclip not found or failed. Please copy the HTML manually from the console.")
                print("[!] To enable auto-copy, run: pip install pyperclip beautifulsoup4")

            print("[*] You can now paste this information back to the assistant to proceed.")

        except Exception as e:
            print(f"\n[!] An error occurred during DOM capture: {e}")
            if 'page' in locals() and page:
                await save_error_state(page)
        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(snap_dom())