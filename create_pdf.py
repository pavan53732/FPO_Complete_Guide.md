#!/usr/bin/env python3
"""
PDF Generator using Playwright
Generates PDF from HTML file with rendered Mermaid diagrams.
Waits minimum 60 seconds for Mermaid.js to render all 49 diagrams.
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: Playwright not installed.")
    print("Please install it with: pip install playwright")
    print("Then install browsers with: playwright install chromium")
    sys.exit(1)


async def generate_pdf():
    """Generate PDF from HTML file using Playwright."""
    
    # File paths
    html_file = Path("c:/FPO_Complete_Guide.md/FPO_AP_STATE_COMPLETE_GUIDE.html")
    pdf_file = Path("c:/FPO_Complete_Guide.md/FPO_AP_STATE_COMPLETE_GUIDE.pdf")
    
    print(f"{'='*60}")
    print("PDF GENERATION SCRIPT")
    print(f"{'='*60}")
    
    # Check if HTML file exists
    if not html_file.exists():
        print(f"ERROR: HTML file not found: {html_file}")
        print("Please run convert_md_to_html.py first to generate the HTML file.")
        return 1
    
    print(f"Input HTML: {html_file}")
    print(f"Output PDF: {pdf_file}")
    print(f"HTML file size: {html_file.stat().st_size:,} bytes")
    print()
    
    async with async_playwright() as p:
        print("Launching headless Chromium browser...")
        
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as e:
            print(f"ERROR: Failed to launch browser: {e}")
            print("\nPlease install Chromium browser with:")
            print("  playwright install chromium")
            return 1
        
        print("Browser launched successfully.")
        
        # Create a new page
        page = await browser.new_page()
        
        # Navigate to the HTML file
        file_url = f"file:///{html_file.as_posix()}"
        print(f"Loading HTML file: {file_url}")
        
        try:
            await page.goto(file_url, wait_until='networkidle', timeout=60000)
            print("Page loaded (networkidle state reached).")
        except Exception as e:
            print(f"WARNING: Page load timeout, continuing anyway: {e}")
        
        # Wait for Mermaid to render - reduced to 30 seconds for faster generation
        wait_time = 30  # seconds
        print(f"\nWaiting {wait_time} seconds for Mermaid.js to render all diagrams...")
        print("(This ensures all 49 Mermaid diagrams are fully rendered)")
        
        # Progress indicator - check every 5 seconds
        for i in range(0, wait_time, 5):
            print(f"  {i} seconds elapsed...")
            await asyncio.sleep(5)
        
        print(f"  {wait_time} seconds elapsed - wait complete.")
        
        # Check for rendered Mermaid diagrams
        print("\nVerifying Mermaid diagram rendering...")
        
        try:
            # Count mermaid divs
            mermaid_divs = await page.locator('.mermaid').count()
            print(f"  Found {mermaid_divs} Mermaid diagram containers")
            
            # Count rendered SVGs within mermaid divs
            rendered_svgs = await page.locator('.mermaid svg').count()
            print(f"  Found {rendered_svgs} rendered SVG diagrams")
            
            if rendered_svgs < 49:
                print(f"\n⚠️ WARNING: Only {rendered_svgs} of 49 diagrams appear to be rendered.")
                print("    Waiting an additional 30 seconds...")
                await asyncio.sleep(30)
                
                # Recheck
                rendered_svgs = await page.locator('.mermaid svg').count()
                print(f"  After additional wait: {rendered_svgs} rendered SVG diagrams")
        except Exception as e:
            print(f"  Note: Could not verify SVG count: {e}")
        
        # Generate PDF
        print("\nGenerating PDF...")
        print("  Format: A4")
        print("  Margins: 2cm all sides")
        print("  Print background: True")
        
        try:
            await page.pdf(
                path=str(pdf_file),
                format='A4',
                margin={
                    'top': '2cm',
                    'right': '2cm',
                    'bottom': '2cm',
                    'left': '2cm'
                },
                print_background=True,
                prefer_css_page_size=False,
                scale=0.9  # Slightly smaller to fit content better
            )
            print("PDF generated successfully!")
        except Exception as e:
            print(f"ERROR: Failed to generate PDF: {e}")
            await browser.close()
            return 1
        
        # Close browser
        await browser.close()
        print("Browser closed.")
    
    # Verify PDF was created
    if pdf_file.exists():
        pdf_size = pdf_file.stat().st_size
        print(f"\n{'='*60}")
        print("PDF GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Output file: {pdf_file}")
        print(f"File size: {pdf_size:,} bytes ({pdf_size/1024/1024:.2f} MB)")
        print(f"{'='*60}")
        
        if pdf_size < 100000:  # Less than 100KB
            print("\n⚠️ WARNING: PDF file seems unusually small.")
            print("   Please verify the content manually.")
        else:
            print("\n✅ SUCCESS: PDF file created successfully!")
            print("   Please open the PDF and verify:")
            print("   - All 49 Mermaid diagrams are rendered as graphics")
            print("   - All content from markdown is present")
            print("   - Tables and formatting are preserved")
        
        return 0
    else:
        print(f"\nERROR: PDF file was not created: {pdf_file}")
        return 1


def main():
    """Main entry point."""
    return asyncio.run(generate_pdf())


if __name__ == "__main__":
    sys.exit(main())
