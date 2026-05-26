import sys
import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        # Create a new page with a premium widescreen desktop viewport
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        # Navigate to sign-in page to establish the correct origin domain
        print("Navigating to sign-in...")
        page.goto('http://localhost:3001/sign-in')
        page.wait_for_load_state('networkidle')
        
        # Inject sandbox localStorage bypass keys
        print("Injecting Sandbox localStorage credentials...")
        page.evaluate("""() => {
            localStorage.setItem('helix_sandbox_session', 'true');
            localStorage.setItem('helix_sandbox_email', 'sandbox@helix.app');
            localStorage.setItem('helix_sandbox_name', 'Sandbox Explorer');
        }""")
        
        # Navigate to the dashboard command center
        print("Navigating to Overview Dashboard...")
        page.goto('http://localhost:3001/overview')
        page.wait_for_load_state('networkidle')
        
        # Wait for Framer Motion animations to finish loading completely
        print("Waiting for visual elements and council map to render...")
        time.sleep(5)
        
        # Take a high-resolution screenshot
        screenshot_path = '/Users/mihirsachdev/.gemini/antigravity/brain/98e426bf-a4c3-40d4-88b4-bc7b5304ac87/dashboard.png'
        print(f"Saving screenshot to: {screenshot_path}")
        page.screenshot(path=screenshot_path, full_page=False)
        
        browser.close()
        print("Success!")

if __name__ == '__main__':
    main()
