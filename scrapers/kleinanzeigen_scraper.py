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
from pymongo import MongoClient

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configure Selenium WebDriver (make sure you have ChromeDriver installed)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Enable headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--start-maximized')  # Start with maximized window

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

# URL to scrape
main_url = "https://www.kleinanzeigen.de/s-multimedia-elektronik/"

# First navigate to the URL
driver.get(main_url)

# Then clear everything
try:
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")
except Exception as e:
    print(f"Warning: Could not clear browser data: {e}")

# # Verify we're on the right page
# current_url = driver.current_url
# if "elektronik" not in current_url:  # adjust this based on your expected URL
#     print(f"Warning: Unexpected URL: {current_url}")
#     print(f"Expected URL to contain 'elektronik'")
#     # Optionally force the correct URL
#     driver.get(main_url)

# Initialize dictionary to store data by page
all_pages_data = {}

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
        print("Looking for cookie consent button...")

        # Wait for the cookie banner to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gdpr-banner"))
        )

        # Locate the accept button using its data-testid or id
        accept_button = driver.find_element(By.ID, "gdpr-banner-accept")
        
        # Click the accept button
        accept_button.click()
        
        print("Clicked accept button")

        # Wait for the banner to be removed from the DOM
        WebDriverWait(driver, 10).until(
            EC.staleness_of(driver.find_element(By.ID, "gdpr-banner"))
        )

        return True

    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
        return False

def parse_time(time_text):
    """Convert time formats to datetime object"""
    now = datetime.now()
    
    if not time_text:
        return None
        
    time_text = time_text.lower()
    
    if 'heute' in time_text:
        # Extract HH:MM from "heute, HH:MM"
        time_part = time_text.replace('heute,', '').strip()
        hour, minute = map(int, time_part.split(':'))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif 'gestern' in time_text:
        # Handle "gestern, HH:MM" format
        time_part = time_text.replace('gestern,', '').strip()
        hour, minute = map(int, time_part.split(':'))
        yesterday = now - timedelta(days=1)
        return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return None

def scrape(max_pages=2):
    found_yesterday = False
    page = 1
    
    # while page <= max_pages and not found_yesterday:  # Changed condition to <= instead of >
    while page <= max_pages:  # Changed condition to <= instead of >
        page_url = f"{main_url}seite:{page}/c161" if page > 1 else f"{main_url}c161"

        print(f"Scraping {page_url}...")
        
        # Get the page and wait for initial content
        driver.get(page_url)
        
        # Handle cookie popup before proceeding (but don't stop if it fails)
        if page == 1:  # Only try this on first page
            accept_cookies(driver)
        
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
                
                # Locate the parent container of the time
                time_container = article.find('div', class_='aditem-main--top--right')
                time_text = time_container.get_text(strip=True) if time_container else None
                timestamp = parse_time(time_text) if time_text else None
                            
                # Check if this post is from yesterday or earlier
                if timestamp and timestamp.date() < datetime.now().date():
                    found_yesterday = True

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
                price = price_container.get_text(strip=True) if price_container else None
                
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
                        'price': price,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                    })
                
            except Exception as e:
                print(f"Error extracting data from article: {str(e)}")
                continue  # Skip this item and continue with the next

        print(f"Found {len(page_data_list)} ads")
        
        # Store this page's data in the main dictionary
        all_pages_data[page] = page_data_list
        
        # Optional: Add a small delay between pages to be polite
        time.sleep(2)

        page += 1
        
        if page > max_pages:
            print(f"Reached maximum page limit ({max_pages}), stopping...")
            break

    # After scraping
    current_time = datetime.now().isoformat()
    for page in all_pages_data.values():
        for listing in page:
            listing['source'] = 'kleinanzeigen'
            listing['scraped_at'] = current_time

    return all_pages_data

if __name__ == "__main__":
    all_pages_data = scrape()
    
    if not all_pages_data:
        print("Warning: No data was scraped!")
    else:
        print(f"Scraped {len(all_pages_data)} pages of data")
        
        # Create directory if it doesn't exist
        os.makedirs('./JSON', exist_ok=True)

        # Save the original data to JSON
        output_path = './JSON/kleinanzeigen_ads.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_pages_data, f, ensure_ascii=False, indent=4)
        
        print(f"Data successfully saved to {output_path}")
