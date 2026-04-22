import asyncio
import os
from playwright.async_api import async_playwright

async def render_html_to_png(html_relative_path, output_png_path):
    async with async_playwright() as p:
        # Use Chromium
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1200, 'height': 800})
        page = await browser.new_page()
        
        # Resolve absolute path to the local HTML file
        abs_path = os.path.abspath(html_relative_path)
        file_url = f"file://{abs_path}"
        
        print(f"Opening {file_url}...")
        await page.goto(file_url)
        
        # Wait for Mermaid to render. Mermaid usually replaces the text with SVG.
        # We look for the SVG element within the mermaid div.
        try:
            await page.wait_for_selector(".mermaid svg", timeout=10000)
        except Exception as e:
            print("Warning: Mermaid SVG not found within timeout. Taking screenshot anyway.")
        
        # Give it a moment to stabilize animations
        await asyncio.sleep(2)
        
        # Locate the container for a clean crop
        container = await page.query_selector(".container")
        if container:
            await container.screenshot(path=output_png_path)
            print(f"Saved cropped screenshot to {output_png_path}")
        else:
            await page.screenshot(path=output_png_path, full_page=True)
            print(f"Saved full-page screenshot to {output_png_path}")
            
        await browser.close()

if __name__ == "__main__":
    # Render the Mermaid architecture
    html_file = "architecture_mermaid.html"
    output_file = "architecture.png"
    
    if os.path.exists(html_file):
        asyncio.run(render_html_to_png(html_file, output_file))
    else:
        print(f"Error: {html_file} not found.")
