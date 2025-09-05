#!/usr/bin/env python3
"""
Auto-scroll browser program
Opens a URL in browser and automatically scrolls to the bottom of the page.
"""

import sys
import time
import os
import re
import requests
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader

def find_scrollable_element(driver):
    """
    Find the main scrollable element (contents div, iframe, or main content)
    """
    try:
        # First try to find div with id='contents'
        try:
            contents_div = driver.find_element(By.ID, "contents")
            div_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
            div_client_height = driver.execute_script("return arguments[0].clientHeight", contents_div)
            
            if div_height > div_client_height:
                print(f"Using div#contents for scrolling (scrollHeight: {div_height}, clientHeight: {div_client_height})")
                return "contents_div"
        except:
            print("Div with id='contents' not found")
        
        # Check iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframe(s)")
        
        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                
                # Check for contents div inside iframe
                try:
                    contents_div = driver.find_element(By.ID, "contents")
                    div_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
                    div_client_height = driver.execute_script("return arguments[0].clientHeight", contents_div)
                    
                    if div_height > div_client_height:
                        print(f"Using div#contents in iframe {i+1} for scrolling")
                        return "iframe_contents_div"
                except:
                    pass
                
                # Check iframe body
                iframe_height = driver.execute_script("return document.body.scrollHeight")
                window_height = driver.execute_script("return window.innerHeight")
                
                if iframe_height > window_height:
                    print(f"Using iframe {i+1} for scrolling (height: {iframe_height})")
                    return "iframe"
                    
                driver.switch_to.default_content()
                
            except Exception as e:
                driver.switch_to.default_content()
                continue
        
        print("Using main page for scrolling")
        return "main_page"
        
    except Exception as e:
        print(f"Error finding scrollable element: {e}")
        return "main_page"

def scroll_element(driver, scroll_delay=2, element_type="main_page"):
    """
    Scroll the specified element to bottom
    """
    print("Starting auto-scroll to bottom...")
    
    if element_type == "contents_div":
        contents_div = driver.find_element(By.ID, "contents")
        last_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
        
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", contents_div)
            time.sleep(scroll_delay)
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
            
            if new_height == last_height:
                print("Reached bottom!")
                break
                
            last_height = new_height
            print(f"Scrolling div#contents... (height: {new_height})")
    
    elif element_type == "iframe_contents_div":
        contents_div = driver.find_element(By.ID, "contents")
        last_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
        
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", contents_div)
            time.sleep(scroll_delay)
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", contents_div)
            
            if new_height == last_height:
                print("Reached bottom!")
                break
                
            last_height = new_height
            print(f"Scrolling iframe div#contents... (height: {new_height})")
    
    elif element_type == "iframe":
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                print("Reached bottom!")
                break
                
            last_height = new_height
            print(f"Scrolling iframe... (height: {new_height})")
    
    else:  # main_page
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                print("Reached bottom!")
                break
                
            last_height = new_height
            print(f"Scrolling main page... (height: {new_height})")

download_lock = Lock()

def generate_session_hash(url):
    """
    Generate a short hash from URL and current time for unique session identification
    """
    session_string = f"{url}_{datetime.now().isoformat()}"
    hash_obj = hashlib.md5(session_string.encode())
    return hash_obj.hexdigest()[:8]

def get_timestamp_paths(url):
    """
    Generate timestamp-based paths with hash for images and PDF
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    session_hash = generate_session_hash(url)
    
    # Create unique folder name with timestamp and hash
    folder_name = f"{timestamp}_{session_hash}"
    
    images_dir = os.path.join("downloaded_images", folder_name)
    pdf_dir = "downloaded"
    pdf_filename = f"{timestamp}_{session_hash}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    return images_dir, pdf_path

def download_image_fast(img_url, img_id, download_dir):
    """
    Download image from URL with better error handling and speed
    """
    try:
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        
        # Use session for connection pooling
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(img_url, timeout=15, stream=True)
        response.raise_for_status()
        
        # Get file extension from URL or content-type
        file_ext = 'jpg'
        if '.' in img_url.split('/')[-1]:
            file_ext = img_url.split('.')[-1].split('?')[0]
        elif 'content-type' in response.headers:
            content_type = response.headers['content-type']
            if 'png' in content_type:
                file_ext = 'png'
            elif 'gif' in content_type:
                file_ext = 'gif'
            elif 'webp' in content_type:
                file_ext = 'webp'
        
        filename = f"{img_id}.{file_ext}"
        filepath = os.path.join(download_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        with download_lock:
            print(f"Downloaded: {filename}")
        
        session.close()
        return filepath
        
    except Exception as e:
        with download_lock:
            print(f"Failed to download {img_url}: {e}")
        return None

def download_images_batch(image_list, download_dir, max_workers=5):
    """
    Download multiple images concurrently
    """
    downloaded_files = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_img = {
            executor.submit(download_image_fast, img_src, img_id, download_dir): (img_id, img_src)
            for img_id, img_src in image_list
        }
        
        for future in as_completed(future_to_img):
            img_id, img_src = future_to_img[future]
            try:
                filepath = future.result()
                if filepath:
                    downloaded_files.append((img_id, filepath))
            except Exception as e:
                print(f"Error downloading {img_id}: {e}")
    
    return downloaded_files

def get_visible_page_images(driver, element_type="main_page"):
    """
    Get visible images with id pattern 'page0', 'page1', etc.
    """
    try:
        if element_type in ["contents_div", "iframe_contents_div"]:
            # For div scrolling, check images within the contents div
            if element_type == "iframe_contents_div":
                imgs = driver.find_elements(By.CSS_SELECTOR, "#contents img[id^='page']")
            else:
                imgs = driver.find_elements(By.CSS_SELECTOR, "#contents img[id^='page']")
        else:
            # For page/iframe scrolling, check all images
            imgs = driver.find_elements(By.CSS_SELECTOR, "img[id^='page']")
        
        visible_images = []
        
        for img in imgs:
            try:
                # Check if image is visible in viewport
                is_displayed = img.is_displayed()
                location = img.location
                size = img.size
                
                if is_displayed and location['y'] >= 0 and size['height'] > 0:
                    # Get viewport height
                    viewport_height = driver.execute_script("return window.innerHeight")
                    
                    # Check if image is in viewport
                    img_bottom = location['y'] + size['height']
                    if location['y'] <= viewport_height and img_bottom >= 0:
                        img_id = img.get_attribute('id')
                        img_src = img.get_attribute('src')
                        
                        if img_id and img_src and re.match(r'^page\d+$', img_id):
                            visible_images.append((img_id, img_src))
                            
            except Exception as e:
                continue
                
        return visible_images
        
    except Exception as e:
        print(f"Error getting visible images: {e}")
        return []

def scroll_and_download_images(driver, scroll_delay=2, element_type="main_page", url=None):
    """
    Scroll viewport by viewport, collect all images, then download in batches
    """
    all_images_to_download = []
    downloaded_image_ids = set()
    
    print("Starting viewport-by-viewport scrolling to collect images...")
    
    if element_type == "contents_div":
        contents_div = driver.find_element(By.ID, "contents")
        viewport_height = driver.execute_script("return arguments[0].clientHeight", contents_div)
        scroll_script = f"arguments[0].scrollTop += {viewport_height}"
        current_scroll_script = "return arguments[0].scrollTop"
        max_scroll_script = "return arguments[0].scrollHeight - arguments[0].clientHeight"
        
        while True:
            # Collect visible images
            visible_imgs = get_visible_page_images(driver, element_type)
            for img_id, img_src in visible_imgs:
                if img_id not in downloaded_image_ids:
                    all_images_to_download.append((img_id, img_src))
                    downloaded_image_ids.add(img_id)
            
            # Check if we've reached the bottom
            current_scroll = driver.execute_script(current_scroll_script, contents_div)
            max_scroll = driver.execute_script(max_scroll_script, contents_div)
            
            if current_scroll >= max_scroll:
                print("Reached bottom of contents div!")
                break
            
            # Scroll by viewport height
            driver.execute_script(scroll_script, contents_div)
            time.sleep(scroll_delay)
            
            new_scroll = driver.execute_script(current_scroll_script, contents_div)
            print(f"Scrolled to: {new_scroll}/{max_scroll}")
    
    elif element_type == "iframe_contents_div":
        contents_div = driver.find_element(By.ID, "contents")
        viewport_height = driver.execute_script("return arguments[0].clientHeight", contents_div)
        scroll_script = f"arguments[0].scrollTop += {viewport_height}"
        current_scroll_script = "return arguments[0].scrollTop"
        max_scroll_script = "return arguments[0].scrollHeight - arguments[0].clientHeight"
        
        while True:
            # Collect visible images
            visible_imgs = get_visible_page_images(driver, element_type)
            for img_id, img_src in visible_imgs:
                if img_id not in downloaded_image_ids:
                    all_images_to_download.append((img_id, img_src))
                    downloaded_image_ids.add(img_id)
            
            # Check if we've reached the bottom
            current_scroll = driver.execute_script(current_scroll_script, contents_div)
            max_scroll = driver.execute_script(max_scroll_script, contents_div)
            
            if current_scroll >= max_scroll:
                print("Reached bottom of iframe contents div!")
                break
            
            # Scroll by viewport height
            driver.execute_script(scroll_script, contents_div)
            time.sleep(scroll_delay)
            
            new_scroll = driver.execute_script(current_scroll_script, contents_div)
            print(f"Scrolled to: {new_scroll}/{max_scroll}")
    
    else:  # iframe or main_page
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_script = f"window.scrollBy(0, {viewport_height})"
        
        while True:
            # Collect visible images
            visible_imgs = get_visible_page_images(driver, element_type)
            for img_id, img_src in visible_imgs:
                if img_id not in downloaded_image_ids:
                    all_images_to_download.append((img_id, img_src))
                    downloaded_image_ids.add(img_id)
            
            # Check if we've reached the bottom
            current_scroll = driver.execute_script("return window.pageYOffset")
            max_scroll = driver.execute_script("return document.body.scrollHeight - window.innerHeight")
            
            if current_scroll >= max_scroll:
                print("Reached bottom of page!")
                break
            
            # Scroll by viewport height
            driver.execute_script(scroll_script)
            time.sleep(scroll_delay)
            
            new_scroll = driver.execute_script("return window.pageYOffset")
            print(f"Scrolled to: {new_scroll}/{max_scroll}")
    
    print(f"\nFound {len(all_images_to_download)} unique images to download")
    
    if all_images_to_download:
        # Generate timestamp-based paths with hash
        images_dir, pdf_path = get_timestamp_paths(url or "unknown")
        
        print(f"Creating directories...")
        print(f"Images will be saved to: {images_dir}")
        print(f"PDF will be saved to: {pdf_path}")
        
        print("Starting batch download...")
        downloaded_files = download_images_batch(all_images_to_download, images_dir)
        
        if downloaded_files:
            print(f"\nDownload completed! Creating PDF...")
            final_pdf_path = create_pdf_from_images(downloaded_files, pdf_path)
            if final_pdf_path:
                print(f"PDF created: {final_pdf_path}")
        
        return downloaded_files
    
    return []

def create_pdf_from_images(downloaded_files, output_path):
    """
    Create PDF from downloaded images in page order
    """
    try:
        # Create PDF directory if it doesn't exist
        pdf_dir = os.path.dirname(output_path)
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
        
        # Sort files by page number
        def extract_page_number(item):
            img_id, filepath = item
            match = re.search(r'page(\d+)', img_id)
            return int(match.group(1)) if match else 999999
        
        sorted_files = sorted(downloaded_files, key=extract_page_number)
        
        if not sorted_files:
            return None
        
        # Create PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        page_width, page_height = A4
        
        for img_id, filepath in sorted_files:
            try:
                # Open and resize image if needed
                with Image.open(filepath) as img:
                    img_width, img_height = img.size
                    
                    # Calculate scaling to fit page while maintaining aspect ratio
                    scale_w = page_width / img_width
                    scale_h = page_height / img_height
                    scale = min(scale_w, scale_h) * 0.9  # Leave some margin
                    
                    new_width = img_width * scale
                    new_height = img_height * scale
                    
                    # Center image on page
                    x = (page_width - new_width) / 2
                    y = (page_height - new_height) / 2
                    
                    # Add image to PDF
                    c.drawImage(filepath, x, y, width=new_width, height=new_height)
                    c.showPage()
                    
                    print(f"Added {img_id} to PDF")
                    
            except Exception as e:
                print(f"Failed to add {img_id} to PDF: {e}")
                continue
        
        c.save()
        print(f"PDF saved with {len(sorted_files)} pages")
        return output_path
        
    except Exception as e:
        print(f"Failed to create PDF: {e}")
        return None

def scroll_and_download_from_url(url, scroll_delay=2, headless=True, keep_browser_open=False):
    """
    Scroll through a webpage and download all page images as PDF
    
    Args:
        url (str): URL to process
        scroll_delay (float): Delay between scroll actions in seconds
        headless (bool): Run browser in headless mode
        keep_browser_open (bool): Keep browser open after completion
        
    Returns:
        dict: Result containing downloaded files info and PDF path
        {
            'success': bool,
            'images_dir': str,
            'pdf_path': str,
            'downloaded_count': int,
            'error': str (if success=False)
        }
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"Opening URL: {url}")
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)
        
        element_type = find_scrollable_element(driver)
        downloaded_files = scroll_and_download_images(driver, scroll_delay, element_type, url)
        
        if keep_browser_open:
            print("Browser kept open. Close manually when done.")
        else:
            driver.quit()
            driver = None
        
        if downloaded_files:
            images_dir, pdf_path = get_timestamp_paths(url)
            return {
                'success': True,
                'images_dir': images_dir,
                'pdf_path': pdf_path,
                'downloaded_count': len(downloaded_files),
                'error': None
            }
        else:
            return {
                'success': False,
                'images_dir': None,
                'pdf_path': None,
                'downloaded_count': 0,
                'error': 'No images found to download'
            }
        
    except Exception as e:
        error_msg = f"Error occurred: {e}"
        print(error_msg)
        return {
            'success': False,
            'images_dir': None,
            'pdf_path': None,
            'downloaded_count': 0,
            'error': error_msg
        }
        
    finally:
        if driver:
            driver.quit()

def auto_scroll_page(url, scroll_delay=2, download_images=False, headless=False):
    """
    Opens URL in Chrome browser and scrolls to bottom automatically
    Handles both regular pages and iframe content
    
    Args:
        url (str): URL to open
        scroll_delay (float): Delay between scroll actions in seconds
        download_images (bool): Whether to download visible images while scrolling
        headless (bool): Run browser in headless mode
        
    Returns:
        dict: Result info if download_images=True, None otherwise
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"Opening URL: {url}")
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)
        
        element_type = find_scrollable_element(driver)
        
        if download_images:
            downloaded_files = scroll_and_download_images(driver, scroll_delay, element_type, url)
            
            if downloaded_files:
                images_dir, pdf_path = get_timestamp_paths(url)
                result = {
                    'success': True,
                    'images_dir': images_dir,
                    'pdf_path': pdf_path,
                    'downloaded_count': len(downloaded_files)
                }
            else:
                result = {
                    'success': False,
                    'images_dir': None,
                    'pdf_path': None,
                    'downloaded_count': 0
                }
            
            if not headless:
                print("Auto-scroll completed. Press Enter to close browser...")
                input()
            
            return result
        else:
            scroll_element(driver, scroll_delay, element_type)
            
            if not headless:
                print("Auto-scroll completed. Press Enter to close browser...")
                input()
            
            return None
        
    except Exception as e:
        error_msg = f"Error occurred: {e}"
        print(error_msg)
        if download_images:
            return {
                'success': False,
                'images_dir': None,
                'pdf_path': None,
                'downloaded_count': 0,
                'error': error_msg
            }
        return None
        
    finally:
        if driver:
            driver.quit()

def main():
    download_images = False
    url = None
    
    # Check command line arguments
    if len(sys.argv) >= 2:
        if sys.argv[1] == '--download-images':
            download_images = True
            if len(sys.argv) >= 3:
                url = sys.argv[2]
        elif sys.argv[1] in ['--help', '-h']:
            print("Auto Scroll Browser with Image Download")
            print("Usage:")
            print("  python auto_scroll_browser.py [options] [URL]")
            print("  python auto_scroll_browser.py  # Interactive mode")
            print("")
            print("Options:")
            print("  --download-images    Download images while scrolling")
            print("  --help, -h          Show this help message")
            print("")
            print("Examples:")
            print("  python auto_scroll_browser.py https://example.com")
            print("  python auto_scroll_browser.py --download-images https://example.com")
            print("  python auto_scroll_browser.py --download-images")
            sys.exit(0)
        else:
            url = sys.argv[1]
            if len(sys.argv) >= 3 and sys.argv[2] == '--download-images':
                download_images = True
    
    # Interactive input if no URL provided
    if not url:
        print("Auto Scroll Browser with Image Download")
        print("=" * 50)
        
        while True:
            url = input("Enter URL to scroll: ").strip()
            if url:
                break
            print("Please enter a valid URL.")
        
        while True:
            download_choice = input("Download images while scrolling? (y/n): ").strip().lower()
            if download_choice in ['y', 'yes', '1']:
                download_images = True
                break
            elif download_choice in ['n', 'no', '0']:
                download_images = False
                break
            print("Please enter 'y' for yes or 'n' for no.")
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\nStarting browser with URL: {url}")
    print(f"Download images: {'Yes' if download_images else 'No'}")
    print("-" * 50)
    
    auto_scroll_page(url, download_images=download_images)

if __name__ == "__main__":
    main()