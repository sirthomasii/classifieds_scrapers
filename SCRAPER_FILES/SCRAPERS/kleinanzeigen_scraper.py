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
    # Initial wait for first batch of content
    time.sleep(pause_time)
    
    # Get initial height
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    
    # Set a maximum number of scroll attempts
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        # Scroll down by viewport height
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        
        # Wait for potential new content
        time.sleep(pause_time)
        
        # Calculate new scroll height
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        
        # Break if no new content (heights equal)
        if new_height == last_height:
            break
            
        last_height = new_height
        attempts += 1
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")

def accept_cookies(driver):
    """Find and click the accept cookies button"""
    try:
        # print("Looking for cookie consent button...")

        # Wait for the cookie banner to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gdpr-banner"))
        )

        # Locate the accept button using its data-testid or id
        accept_button = driver.find_element(By.ID, "gdpr-banner-accept")
        
        # Click the accept button
        accept_button.click()
        
        # print("Clicked accept button")

        # Wait for the banner to be removed from the DOM
        WebDriverWait(driver, 10).until(
            EC.staleness_of(driver.find_element(By.ID, "gdpr-banner"))
        )

        return True

    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
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
        ("https://www.kleinanzeigen.de/s-computer-sonstiges/", "c161", "computers"),
        ("https://www.kleinanzeigen.de/s-musikinstrumente/", "c74", "music")
    ]

    all_pages_data = {}

    driver = None
    cookies_handled = False
    try:
        driver = init_driver()
        
        # Scrape each URL
        for main_url, category_id, category in urls:
            print(f"\nScraping category: {category_id}")
            page = 1

            while page <= max_pages:
                try:
                    page_url = f"{main_url}seite:{page}/{category_id}" if page > 1 else f"{main_url}{category_id}"

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
                    articles = page_soup.find_all('li', class_=lambda x: x and 'ad-listitem' in x)
                    for article in articles:
                        try:
                            # Check if ad is featured
                            featured_div = article.find('div', string='Featured')
                            is_featured = featured_div is not None
                            
                            # Get link
                            link_elem = article.find('a', class_=lambda x: x and 'ellipsis' in x)
                            link = link_elem.get('href') if link_elem else None
                            full_link = f"https://www.kleinanzeigen.de{link}" if link else None

                            # Get title and translate it
                            title_container = article.find('a', class_=lambda x: x and 'ellipsis' in x)
                            title = title_container.get_text(strip=True) if title_container else None
                            
                            # Get description
                            description_container = article.find('p', class_=lambda x: x and 'description' in x)
                            description = description_container.get_text(strip=True) if description_container else None
                            
                            # Get price
                            price_container = article.find('p', class_=lambda x: x and 'price-shipping' in x)
                            price_text = price_container.get_text(strip=True) if price_container else None
                            price = clean_price(price_text)
                            
                            # Get image
                            imagebox = article.find('div', class_='imagebox srpimagebox')
                            largest_image_url = None
                            if imagebox:
                                img = imagebox.find('img')
                                if img:
                                    largest_image_url = img.get('src') or img.get('srcset')
                            
                            # Only add the item if we have at least a title and link
                            if title and link:
                                page_data_list.append({
                                    'title': {
                                        'original': title,
                                        'english': title,
                                    },
                                    'description': description,
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
                    print(f"Error scraping category {category_id}: {str(e)}")
                    break

        # After scraping
        current_time = datetime.now().isoformat()
        for page in all_pages_data.values():
            for listing in page:
                listing['source'] = 'kleinanzeigen'
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
        