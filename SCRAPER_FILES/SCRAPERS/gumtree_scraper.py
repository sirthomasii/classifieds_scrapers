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

driver = webdriver.Chrome(options=options)

# URL to scrape
main_url = "https://www.gumtree.com/for-sale/stereos-audio/uk/"

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
        # print("Looking for cookie consent button...")
        
        # Wait for the cookie banner to be present and visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "onetrust-banner-sdk"))
        )
        
        # Try multiple methods to click the accept button
        try:    
            # Method 1: Direct click
            accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            accept_button.click()
        except:
            try:
                # Method 2: JavaScript click
                accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
                driver.execute_script("arguments[0].click();", accept_button)
            except:
                # Method 3: Action chains
                accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
                ActionChains(driver).move_to_element(accept_button).click().perform()
        
        # print("Clicked accept button")
        
        # Wait for banner to be hidden (checking CSS visibility)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return window.getComputedStyle(document.getElementById('onetrust-banner-sdk')).visibility"
            ) == "hidden"
        )
        
        return True
        
    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
        return False

def convert_gbp_to_eur(gbp_amount):
    """Convert GBP to EUR using a fixed conversion rate"""
    if gbp_amount is None:
        return None
    # Using an approximate conversion rate (you might want to use an API for real-time rates)
    GBP_TO_EUR_RATE = 1.17
    # Round to nearest integer for final EUR amount
    return int(round(gbp_amount * GBP_TO_EUR_RATE))

def clean_price(price_str):
    """Clean price string and convert to number"""
    if not price_str:
        return None
    # Remove £ symbol and any spaces, commas
    cleaned = price_str.replace('£', '').replace(' ', '').replace(',', '')
    try:
        # Convert to float first to handle decimal prices
        float_price = float(cleaned)
        # Convert to pence/cents (integer) to avoid floating point issues
        return round(float_price, 2)
    except ValueError:
        return None

def scrape(max_pages=2):
    found_yesterday = False
    page = 1
    
    while page <= max_pages:
        page_url = f"{main_url}page{page}/" if page > 1 else main_url
        
        # print(f"Scraping {page_url}...")
        
        try:
            driver.get(page_url)
            
            if page == 1:
                accept_cookies(driver)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            scroll_gradually(driver)
            
            page_source = driver.page_source
            page_soup = BeautifulSoup(page_source, 'html.parser')

            page_data_list = []
            articles = page_soup.find_all('article')
            
            for article in articles:
                try:
                    # Check if ad is featured
                    featured_div = article.find('div', string='Featured')
                    is_featured = featured_div is not None
                    
                    # Get link first - we'll use this to skip invalid entries
                    link_elem = article.find('a', attrs={'data-q': 'search-result-anchor'})
                    if not link_elem or not link_elem.get('href'):
                        continue

                    link = "https://www.gumtree.com" + link_elem['href']
                    
                    # Get title
                    title_container = article.find('div', attrs={'data-q': 'tile-title'})
                    title = title_container.get_text(strip=True) if title_container else None
                    if not title:
                        continue
                    
                    # Get description
                    description_container = article.find('div', attrs={'data-q': 'tile-description'})
                    description = description_container.find('p').get_text(strip=True) if description_container else None
                            
                    # Get price and convert to EUR
                    price_container = article.find('div', attrs={'data-q': 'tile-price'})
                    price_gbp = price_container.get_text(strip=True) if price_container else None
                    price_gbp_clean = clean_price(price_gbp)
                    price_eur = convert_gbp_to_eur(price_gbp_clean) if price_gbp_clean is not None else None

                    # Get image
                    figure = article.find('figure', class_='listing-tile-thumbnail-image')
                    largest_image_url = None
                    if figure:
                        img = figure.find('img')
                        if img:
                            largest_image_url = img.get('data-src') or img.get('src')

                    # Get time text
                    time_container = article.find('div', attrs={'data-q': 'tile-date'})

                    if not is_featured:
                        page_data_list.append({
                            'title': {
                                'original': title,
                                'english': title,
                            },
                            'description': description,
                            'main_image': largest_image_url,
                            'link': link,
                            'price': {
                                'gbp': price_gbp_clean,
                                'eur': price_eur
                            },
                            'timestamp': datetime.now().isoformat(),
                            'source': 'gumtree',
                            'scraped_at': datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue

            # print(f"Found {len(page_data_list)} ads")
            all_pages_data[page] = page_data_list
            
            time.sleep(2)
            page += 1
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            break

    return all_pages_data

if __name__ == "__main__":
    all_pages_data = scrape()
    
    if not all_pages_data:
        print("Warning: No data was scraped!")
    else:
        print(f"Scraped {len(all_pages_data)} pages of data")
        