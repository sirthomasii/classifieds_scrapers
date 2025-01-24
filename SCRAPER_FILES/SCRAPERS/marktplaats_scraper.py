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

def init_driver():
    """Initialize and return a new driver instance"""
    options = webdriver.ChromeOptions()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Enable headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--start-maximized')  # Start with maximized window
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
    return webdriver.Chrome(options=options)

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
                    "button[title='Accepteren']"))
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

def clean_price(price_str):
    """Clean price string and convert to number"""
    if not price_str:
        return None
    # Remove €, VB (Verhandlungsbasis/negotiable), spaces, and handle German number format
    cleaned = price_str.replace('€', '').replace('VB', '').replace(' ', '').strip()
    try:
        # Convert German number format (1.234,56 -> 1234.56)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        return int(cleaned)
    except ValueError:
        return None

def scrape(max_pages=2):
    # URLs to scrape
    urls = [
        ("https://www.marktplaats.nl/l/computers-en-software/", "computers"),
        # ("https://www.kleinanzeigen.de/s-musikinstrumente/", "music")
    ]

    all_pages_data = {}

    driver = None
    cookies_handled = False
    try:
        driver = init_driver()
        
        # Scrape each URL
        for main_url, category in urls:
            print(f"\nScraping category: {category}")
            page = 1

            while page <= max_pages:
                try:
                    page_url = f"{main_url}p/{page}/" if page > 1 else f"{main_url}"

                    # print(f"Scraping {page_url}...")
                    
                    # Get the page and wait for initial content
                    driver.get(page_url)
                    
                    # Handle cookie popup only once for the first URL
                    if not cookies_handled:
                        accept_cookies(driver)
                        cookies_handled = True
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "li"))
                    )
                    
                    # Continue with scrolling...
                    scroll_gradually(driver)
                    
                    page_source = driver.page_source
                    page_soup = BeautifulSoup(page_source, 'html.parser')

                    # Extract all ad URLs, titles, and images
                    page_data_list = []
                    articles = page_soup.find_all('li', class_=lambda x: x and 'hz-Listing' in x)
                    for article in articles:
                        try:
                            # Check if ad is featured
                            featured_div = article.find('span', class_=lambda x: x and 'hz-Listing-seller-link' in x)
                            seller_link = featured_div.find('a')
                            is_featured = seller_link is not None
                            
                            # Get link
                            link_elem = article.find('a', class_=lambda x: x and 'hz-Link' in x)
                            link = link_elem.get('href') if link_elem else None
                            full_link = f"https://www.marktplaats.nl{link}" if link else None

                            # Get title from headline span, handling nested font elements
                            title_span = article.find('h3', class_='hz-Listing-title')
                            if title_span:
                                # Get text from innermost font element, or fall back to direct text
                                font_elements = title_span.find_all('font')
                                if font_elements:
                                    full_title = font_elements[-1].get_text(strip=True)
                                else:
                                    full_title = title_span.get_text(strip=True)
                            else:
                                full_title = None
                            title = ' '.join(full_title.split()[:7]) if full_title else None
                            
                            # Get description
                            # description_container = article.find('p', class_=lambda x: x and 'description' in x)
                            # description = description_container.get_text(strip=True) if description_container else None
                            
                            # Get price
                            price_container = article.find('span', class_=lambda x: x and 'hz-text-price-label' in x)
                            if price_container:
                                # Get text from innermost font element, or fall back to direct text
                                font_elements = price_container.find_all('font')
                                if font_elements:
                                    price_text = font_elements[-1].get_text(strip=True)
                                else:
                                    price_text = price_container.get_text(strip=True)
                            else:
                                price_text = None
                            price = clean_price(price_text)
                            
                            # Get image
                            imagebox = article.find('figure', class_='hz-Listing-image-container')
                            largest_image_url = None
                            if imagebox:
                                img = imagebox.find('img')
                                if img:
                                    largest_image_url = img.get('src') or img.get('srcset')
                            
                            # Only add the item if we have at least a title and link
                            if title and link and not is_featured:
                                page_data_list.append({
                                    'title': {
                                        'original': title,
                                        'english': title,
                                    },
                                    'main_image': largest_image_url,
                                    'link': full_link,
                                    'price': {
                                        'eur': price
                                    },
                                    'timestamp': datetime.now().isoformat(),
                                    'category': category
                                })
                            
                        except Exception as e:
                            print(f"Error extracting data from article: {str(e)}")
                            continue  # Skip this item and continue with the next

                    # print(f"Found {len(page_data_list)} ads")
                    
                    # Store this page's data in the main dictionary
                    if page not in all_pages_data:
                        all_pages_data[page] = []
                    all_pages_data[page].extend(page_data_list)
                    
                    # Optional: Add a small delay between pages to be polite
                    time.sleep(2)

                    page += 1
                    
                    if page > max_pages:
                        # print(f"Reached maximum page limit ({max_pages}), stopping...")
                        break

                except Exception as e:
                    print(f"Error scraping category {category}: {str(e)}")
                    break

        # After scraping
        current_time = datetime.now().isoformat()
        for page in all_pages_data.values():
            for listing in page:
                listing['source'] = 'marktplaats'
                listing['scraped_at'] = current_time

        return all_pages_data

    except Exception as e:
        print(f"Error scraping: {str(e)}")
        return None

if __name__ == "__main__":
    all_pages_data = scrape()
    
    if not all_pages_data:
        print("Warning: No data was scraped!")
    else:
        print(f"Scraped {len(all_pages_data)} pages of data")
                # Flatten all listings into a single list
        all_listings = [listing for page in all_pages_data.values() for listing in page]
        
        # Count occurrences across all pages
        title_count = sum(1 for ad in all_listings if ad['title']['original'])
        url_count = sum(1 for ad in all_listings if ad['link'])
        price_count = sum(1 for ad in all_listings if ad['price'])
        image_count = sum(1 for ad in all_listings if ad['main_image'])
        
        print(f"\nBreakdown of all data found:")
        print(f"- Total listings: {len(all_listings)}")
        print(f"- Titles: {title_count}")
        print(f"- URLs: {url_count}")
        print(f"- Prices: {price_count}")
        print(f"- Images: {image_count}")
        print(f"- Timestamps: {sum(1 for ad in all_listings if ad['timestamp'])}")
