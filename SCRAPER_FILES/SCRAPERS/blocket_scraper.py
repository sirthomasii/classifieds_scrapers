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
options.add_argument('--silent')  # Add this line to suppress DevTools messages
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
    ("https://www.blocket.se/annonser/hela_sverige/datorer_tv-spel/datorer_tillbehor", "computers"),
    ("https://www.blocket.se/annonser/hela_sverige/fritid_hobby/musikutrustning?cg=6160", "music")
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
        # print("Looking for cookie consent iframe...")
        
        # Wait for the iframe to be present
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='sp_message_iframe']"))
        )
        
        # Switch to the iframe context
        driver.switch_to.frame(iframe)
        # print("Switched to iframe context")
        
        # Look for the accept button within the iframe
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Godkänn alla cookies']"))
            )
            # print("Found accept button")
            accept_button.click()
            # print("Clicked accept button")
        except Exception as e:
            print(f"Failed to find/click accept button: {e}")
        
        # Switch back to default content
        driver.switch_to.default_content()
        # print("Switched back to main context")
        
        return True
        
    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
        # Make sure we're back in the main context
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
    # Remove spaces, 'kr', and handle possible thousands separator
    cleaned = price_str.replace(' ', '').replace('kr', '').replace('\xa0', '')
    try:
        return int(cleaned)
    except ValueError:
        return None

def scrape(max_pages=2):
    """Scrape Blocket listings"""
    all_data = {}
    cookies_handled = False

    for main_url, category in urls:
        found_yesterday = False
        page = 1

        while page <= max_pages:
            # print(f"DEBUG: Scraping page {page} of {max_pages}")
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
                    link_elem = article.find('a', class_=lambda x: x and 'StyledTitleLink' in x)
                    link = link_elem.get('href') if link_elem else None
                    
                    # Get title and translate it
                    title_container = article.find('span', class_=lambda x: x and 'styled__SubjectContainer' in x)
                    title = title_container.get_text(strip=True) if title_container else None
                            
                    # Get price from Price__StyledPrice and convert to EUR
                    price_container = article.find('div', class_=lambda x: x and 'Price__StyledPrice' in x)
                    price_sek = price_container.get_text(strip=True) if price_container else None
                    price_sek_clean = clean_price(price_sek)
                    price_eur = convert_sek_to_eur(price_sek_clean) if price_sek_clean is not None else None
                    
                    # Get image from picture tag and srcset
                    picture = article.find('picture')
                    if picture:
                        # Try WebP source first, fall back to JPEG
                        source = picture.find('source', {'type': 'image/webp'}) or picture.find('source', {'type': 'image/jpeg'})
                        if source:
                            srcset = source.get('srcset')
                            if srcset:
                                # Split srcset and parse into width-url pairs
                                srcset_items = srcset.split(',')
                                image_versions = []
                                for item in srcset_items:
                                    parts = item.strip().split()
                                    if len(parts) == 2:
                                        url, width = parts
                                        width = int(width.rstrip('w'))
                                        image_versions.append((url, width))
                        
                                # Get URL of highest resolution version
                                if image_versions:
                                    largest_image_url = max(image_versions, key=lambda x: x[1])[0]
                                else:
                                    largest_image_url = None
                            else:
                                print("No srcset found in source")
                                largest_image_url = None
                        else:
                            print("No source found in picture")
                            # Fallback to img tag src if no srcset
                            img = picture.find('img')
                            largest_image_url = img.get('src') if img else None
                    else:
                        print("No picture tag found")
                        largest_image_url = None

                    # print(f"Largest image URL: {largest_image_url}")
                    # Initialize page list if not exists
                    if page not in all_data:
                        all_data[page] = []
                    
                    all_data[page].append({
                        'title': {
                            'original': title,
                            'english': None
                        },
                        'description': None,
                        'main_image': largest_image_url,
                        'link': ("https://www.blocket.se" + link) if link else None,
                        'price': {
                            'sek': price_sek_clean,
                            'eur': price_eur
                        },
                        'timestamp': datetime.now().isoformat(),
                        'category': category
                    })
            
                except Exception as e:
                    print(f"Error extracting data: {e}")

            
            
            # Count statistics for the current page
            # page_data = all_data[page]
            # title_count = sum(1 for ad in page_data if ad['title']['original'])
            # url_count = sum(1 for ad in page_data if ad['link'])
            # price_count = sum(1 for ad in page_data if ad['price']['sek'])
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
