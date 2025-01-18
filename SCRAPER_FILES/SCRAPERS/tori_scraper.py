from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timedelta
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configure Selenium WebDriver (make sure you have ChromeDriver installed)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Enable headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Add these options to handle WebGL and GPU warnings
options.add_argument('--disable-gpu-driver-bug-workarounds')
options.add_argument('--disable-software-rasterizer')
options.add_argument('--disable-webgl')
options.add_argument('--disable-webgl2')

options.add_argument('--disable-blink-features=AutomationControlled')  # Try to avoid detection
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
prefs = {
    "profile.managed_default_content_settings.images": 1,  # Enable images
    "profile.default_content_setting_values.notifications": 2  # Block notifications
}
options.add_experimental_option("prefs", prefs)
options.add_argument('--disable-gpu')
options.add_argument("--log-level=3")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--enable-unsafe-swiftshader')

# Add these new options to clear cache and cookies
options.add_argument('--incognito')  # Use incognito mode
options.add_argument('--disable-cache')  # Disable cache
options.add_argument('--disable-application-cache')  # Disable application cache
options.add_argument('--disable-offline-load-stale-cache')  # Disable offline cache

driver = webdriver.Chrome(options=options)

# URLs to scrape
urls = [
    ("https://www.tori.fi/recommerce/forsale/search?category=0.93", "computers"),
    ("https://www.tori.fi/recommerce/forsale/search?sub_category=1.86.92", "instruments")
]

def scroll_gradually(driver, pause_time=0.125):
    """Scroll until no new content loads"""
    # print("Starting scroll operation...")
    time.sleep(pause_time)
    
    # Get initial page height
    initial_height = driver.execute_script("return document.documentElement.scrollHeight")
    # print(f"Initial page height: {initial_height}")
    
    # JavaScript function to scroll gradually
    scroll_script = """
        return new Promise((resolve) => {
            let lastScrollHeight = 0;
            let unchangedCount = 0;
            const windowHeight = window.innerHeight;
            const scrollStep = Math.min(300, windowHeight * 0.3);  // Fixed smaller step size
            let currentPosition = window.pageYOffset;
            
            function checkAndScroll() {
                const scrollHeight = document.documentElement.scrollHeight;
                
                console.log(`Current scroll position: ${currentPosition}, Total height: ${scrollHeight}`);
                
                if (currentPosition + windowHeight >= scrollHeight - 50 || 
                    (scrollHeight === lastScrollHeight && ++unchangedCount >= 2)) {
                    resolve('bottom');
                    return;
                }
                
                currentPosition = Math.min(currentPosition + scrollStep, scrollHeight - windowHeight);
                window.scrollTo({
                    top: currentPosition,
                    behavior: 'smooth'
                });
                
                unchangedCount = (scrollHeight === lastScrollHeight) ? unchangedCount : 0;
                lastScrollHeight = scrollHeight;
                setTimeout(checkAndScroll, 300);  // Slower interval
            }
            
            checkAndScroll();
        });
    """
    
    # Execute the gradual scroll
    driver.execute_script(scroll_script)
    time.sleep(1.5)
    
    # Gentle final verification scrolls
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    current_pos = driver.execute_script("return window.pageYOffset")
    remaining_scroll = last_height - current_pos
    
    if remaining_scroll > 0:
        driver.execute_script("""
            window.scrollTo({
                top: document.documentElement.scrollHeight,
                behavior: 'smooth'
            });
        """)
        time.sleep(1)

def accept_cookies(driver):
    """Find and click the accept cookies button"""
    try:
        # First try the Sourcepoint iframe approach
        try:
            # Wait for and switch to the iframe - using partial match for SP iframe
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "iframe[title='SP Consent Message'], iframe[id^='sp_message_iframe_']"))
            )
            driver.switch_to.frame(iframe)
            
            # Try to find the accept button
            accept_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "button[title='Hyväksy kaikki evästeet']"))
            )
            accept_button.click()
            driver.switch_to.default_content()
            return True
        except Exception:
            driver.switch_to.default_content()
            
        # Try finding button directly on the page
        try:
            accept_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, """
                    button[class*='cookie'],
                    button[id*='cookie'],
                    button[class*='consent'],
                    #onetrust-accept-btn-handler,
                    .accept-cookies-button
                """))
            )
            accept_button.click()
            return True
        except Exception:
            pass
            
        return False
        
    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
        driver.switch_to.default_content()
        return False


def convert_sek_to_eur(sek_amount):
    """Convert SEK to EUR using a fixed conversion rate"""
    # Using an approximate conversion rate (you might want to use an API for real-time rates)
    SEK_TO_EUR_RATE = 0.087
    return int(sek_amount * SEK_TO_EUR_RATE)

def clean_price(price_str):
    """Clean price string and convert to number"""
    if not price_str:
        return None
    # Remove spaces, '€', commas, and handle possible thousands separator
    cleaned = price_str.replace(' ', '').replace('€', '').replace(',', '').replace('\xa0', '')
    try:
        return int(cleaned)
    except ValueError:
        return None

def scrape(max_pages=2):
    """Scrape Tori listings"""
    all_data = {}
    cookies_handled = False

    for main_url, category in urls:
        found_yesterday = False
        page = 1

        while page <= max_pages:
            # print(f"DEBUG: Scraping page {page} of {max_pages}")
            if "sub_category" in main_url:
                page_url = f"{main_url.replace('search?', f'search?page={page}&')}" if page > 1 else main_url
            else:
                page_url = f"{main_url}&page={page}" if page > 1 else main_url
            # print(f"Scraping {page_url}...")
            
            # Get the page and wait for initial content
            driver.get(page_url)
            
            # Handle cookie popup before proceeding (but don't stop if it fails)
            if not cookies_handled:  # Only handle cookies once
                accept_cookies(driver)
                cookies_handled = True
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Continue with scrolling...
            scroll_gradually(driver)
            
            page_source = driver.page_source
            page_soup = BeautifulSoup(page_source, 'html.parser')

            # Extract all ad URLs, titles, and images
            articles = page_soup.find_all('article')
            for article in articles:
                try:
                    # Get link
                    link_elem = article.find('a', class_=lambda x: x and 'sf-search-ad-link' in x)
                    link = link_elem.get('href') if link_elem else None
                    
                    # Get title and traverse through nested elements to get the deepest text
                    title_container = article.find('h2', class_=lambda x: x and 'h4' in x)
                    if title_container:
                        # Find the deepest text within nested font tags
                        font_tags = title_container.find_all('font')
                        if font_tags:
                            # Get the text from the last (deepest) font tag
                            title = font_tags[-1].get_text(strip=True)
                        else:
                            # Fallback to direct text if no font tags
                            title = title_container.get_text(strip=True)
                    else:
                        title = None
                    
                    # Initialize the item dictionary first
                    item = {
                        'title': {
                            'original': title,
                            'english': None
                        },
                        'description': None,
                        'main_image': None,  # Initialize as None
                        'link': link if link else None,
                        'price': {
                            'eur': None  # Changed from 'sek' to 'eur'
                        },
                        'timestamp': datetime.now().isoformat(),
                        'category': category
                    }
                    
                    # Handle price
                    price_container = article.find('div', class_='text-m')
                    if price_container and '€' in price_container.text:
                        price_str = price_container.get_text(strip=True)
                        item['price']['eur'] = clean_price(price_str.replace('€', ''))
                    
                    # Handle image
                    source = article.find('img')
                    if source:
                        srcset = source.get('srcset')
                        if srcset:
                            # Split srcset and parse into width-url pairs
                            srcset_items = srcset.split(',')
                            image_versions = []
                            for srcset_item in srcset_items:
                                parts = srcset_item.strip().split()
                                if len(parts) == 2:
                                    url, width = parts
                                    width = int(width.rstrip('w'))
                                    image_versions.append((url, width))
                            
                            # Get the URL with the highest width
                            if image_versions:
                                item['main_image'] = max(image_versions, key=lambda x: x[1])[0]
                    else:
                        print("No source found in picture")

                    # print(f"Largest image URL: {largest_image_url}")
                    # Initialize page list if not exists
                    if page not in all_data:
                        all_data[page] = []
                    
                    all_data[page].append(item)
            
                except Exception as e:
                    print(f"Error extracting data: {e}")

            
            
            #Count statistics for the current page
            # page_data = all_data[page]
            # title_count = sum(1 for ad in page_data if ad['title']['original'])
            # url_count = sum(1 for ad in page_data if ad['link'])
            # price_count = sum(1 for ad in page_data if ad['price']['eur'])  # Changed from 'sek' to 'eur'
            # image_count = sum(1 for ad in page_data if ad['main_image'])
            
            # print(f"Found {len(page_data)} ads")
            # print(f"- Titles: {title_count}")
            # print(f"- URLs: {url_count}")
            # print(f"- Prices: {price_count}")
            # print(f"- Images: {image_count}")
            # print(f"- Descriptions: {sum(1 for ad in page_data if ad['description'])}")
            # print(f"- Timestamps: {sum(1 for ad in page_data if ad['timestamp'])}")

            # Optional: Add a small delay between pages to be polite
            time.sleep(2)
            page += 1

    return all_data

if __name__ == "__main__":
    try:
        all_pages_data = scrape()
        
        if not all_pages_data:
            print("Warning: No data was scraped!")
        else:
            print(f"Scraped {len(all_pages_data)} pages of data")
            
    finally:
        driver.quit()  # Always close the browser
