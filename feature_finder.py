# c:\Users\itspr\DailyQuest\Qwen\feature_finder.py
import asyncio
from playwright.async_api import async_playwright
from utils import setup_browser_page, save_error_state

async def find_features():
    """
    Launches a browser with an authenticated session to explore and identify
    the selectors for various features on the Qwen chat interface.
    """
    browser = None
    async with async_playwright() as p:
        try:
            # Use the shared utility to set up the browser and page
            # headless=False is essential for this script
            browser, page = await setup_browser_page(p, headless=False)

            print("\n" + "="*20 + " Feature Discovery " + "="*20)
            print("The script will now attempt to find selectors for key features.")
            print("After printing, the browser will pause for manual inspection.")
            print("You can use the browser's DevTools (F12) to inspect elements.")
            print("Close the browser window to end the script.\n")

            # 1. Model Selector
            print("--- 1. Model Selector ---")
            model_selector_button = page.locator('div[class*="no-translate"] button')
            await model_selector_button.wait_for(timeout=15000)
            model_name = await model_selector_button.inner_text()
            print(f"  [+] Found Model Selector Button. Current model: '{model_name.strip()}'")
            print(f"  [*] Suggested Selector: 'div[class*=\"no-translate\"] button'")

            # 2. Chat History
            print("\n--- 2. Chat History ---")
            chat_history_container = page.locator('div.session-list')
            await chat_history_container.wait_for(timeout=5000)
            chat_items_count = await chat_history_container.locator('a.chat-item-drag-link').count()
            print(f"  [+] Found Chat History container with {chat_items_count} items.")
            print(f"  [*] Suggested Selector for list: 'div.session-list'")
            print(f"  [*] Suggested Selector for items: 'a.chat-item-drag-link'")

            # 3. Action Buttons (Web Dev, Image Gen, etc.)
            print("\n--- 3. Action Buttons ---")
            action_buttons_container = page.locator('div.chat-recommend-txt-container')
            await action_buttons_container.wait_for(timeout=5000)
            buttons = action_buttons_container.locator('button.chat-prompt-suggest-button')
            button_count = await buttons.count()
            print(f"  [+] Found {button_count} action buttons:")
            for i in range(button_count):
                button_text = await buttons.nth(i).inner_text()
                print(f"    - {button_text.strip()}")
            print(f"  [*] Suggested Selector for buttons: 'button.chat-prompt-suggest-button'")

            # 4. Input Area Features
            print("\n--- 4. Input Area Features ---")
            thinking_button = page.locator('button:has-text("Thinking")')
            await thinking_button.wait_for(timeout=5000)
            print("  [+] Found 'Thinking' button.")
            print("  [*] Suggested Selector: 'button:has-text(\"Thinking\")'")
            
            search_button = page.locator('button.websearch_button')
            await search_button.wait_for(timeout=5000)
            print("  [+] Found 'Search' button.")
            print("  [*] Suggested Selector: 'button.websearch_button'")

            upload_button = page.locator('button.chat-prompt-upload-group-btn')
            await upload_button.wait_for(timeout=5000)
            print("  [+] Found Attachment (+) button.")
            print("  [*] Suggested Selector: 'button.chat-prompt-upload-group-btn'")

            print("\n" + "="*50)
            print("[*] Pausing script. The browser is now under your control.")
            print("[*] Press F12 to open DevTools and inspect elements.")
            print("[*] Close the browser window or press Ctrl+C in the terminal to exit.")
            await page.pause()

        except FileNotFoundError as e:
            print(f"\n[!] Setup Error: {e}")
        except Exception as e:
            print(f"\n[!] An error occurred during feature discovery: {e}")
            if 'page' in locals() and page:
                await save_error_state(page)
        finally:
            if browser:
                print("\n[*] Closing browser.")
                await browser.close()

if __name__ == "__main__":
    asyncio.run(find_features())