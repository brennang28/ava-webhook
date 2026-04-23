from playwright.sync_api import sync_playwright
import sys

def test_extract(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        page = context.new_page()
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        text = page.inner_text('body')
        print(f"Extracted length: {len(text)}")
        print("Snippet:", text[:500])
        browser.close()

if __name__ == "__main__":
    test_extract("https://www.google.com") # Simple test
