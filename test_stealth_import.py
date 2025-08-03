# Test import for playwright_stealth
try:
    from playwright_stealth import stealth
    print("Imported 'stealth' from 'playwright_stealth'.")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from playwright_stealth.stealth import stealth
    print("Imported 'stealth' from 'playwright_stealth.stealth'.")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from playwright_stealth.stealth import stealth_async
    print("Imported 'stealth_async' from 'playwright_stealth.stealth'.")
except ImportError as e:
    print(f"ImportError: {e}")
