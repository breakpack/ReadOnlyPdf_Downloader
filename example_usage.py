#!/usr/bin/env python3
"""
Example usage of auto_scroll_browser module
"""

from auto_scroll_browser import scroll_and_download_from_url, auto_scroll_page

def example_1_simple_download():
    """
    Simple example: Download images from URL and create PDF
    """
    url = "https://example.com"
    
    print("=== Example 1: Simple Download ===")
    result = scroll_and_download_from_url(url, headless=True)
    
    if result['success']:
        print(f"✓ Success! Downloaded {result['downloaded_count']} images")
        print(f"✓ Images saved to: {result['images_dir']}")
        print(f"✓ PDF created at: {result['pdf_path']}")
    else:
        print(f"✗ Failed: {result['error']}")
    
    return result

def example_2_with_options():
    """
    Example with custom options
    """
    url = "https://example.com"
    
    print("\n=== Example 2: With Options ===")
    result = scroll_and_download_from_url(
        url=url,
        scroll_delay=1.5,  # Faster scrolling
        headless=False,    # Show browser
        keep_browser_open=False
    )
    
    if result['success']:
        print(f"✓ Downloaded {result['downloaded_count']} images")
        print(f"✓ PDF: {result['pdf_path']}")
    else:
        print(f"✗ Failed: {result['error']}")
    
    return result

def example_3_scroll_only():
    """
    Example: Just scroll without downloading
    """
    url = "https://example.com"
    
    print("\n=== Example 3: Scroll Only ===")
    result = auto_scroll_page(
        url=url,
        scroll_delay=1.0,
        download_images=False,
        headless=True
    )
    
    print("✓ Scrolling completed")
    return result

def example_4_batch_processing():
    """
    Example: Process multiple URLs
    """
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    print("\n=== Example 4: Batch Processing ===")
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"Processing {i}/{len(urls)}: {url}")
        
        result = scroll_and_download_from_url(
            url=url,
            headless=True,
            scroll_delay=1.0
        )
        
        if result['success']:
            print(f"  ✓ Downloaded {result['downloaded_count']} images")
        else:
            print(f"  ✗ Failed: {result['error']}")
        
        results.append(result)
    
    successful = sum(1 for r in results if r['success'])
    print(f"\nCompleted: {successful}/{len(urls)} successful")
    
    return results

if __name__ == "__main__":
    # Run examples (uncomment the ones you want to test)
    
    # example_1_simple_download()
    # example_2_with_options()
    # example_3_scroll_only()
    # example_4_batch_processing()
    
    print("Example usage file created. Uncomment examples to run them.")