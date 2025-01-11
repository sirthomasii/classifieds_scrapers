import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timedelta
import os
import random

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def init_driver():
    """Initialize and return a new driver instance"""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--window-position=-32000,-32000')
    
    # Create the driver with a timeout
    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path=None,  # Let it find the driver automatically
        suppress_welcome=True,        # Suppress welcome message
        use_subprocess=True          # Use subprocess to avoid circular import
    )
    return driver

def scrape(max_pages=2):
    driver = None
    try:
        driver = init_driver()
        
        # Move all the existing scraping code here
        # URL to scrape
        main_url = "https://www.ricardo.ch/de/c/computer-netzwerk-39091/"
        driver.get(main_url)
        
        # Wrap the main scraping code in a try-finally block to ensure cleanup
        try:
            # Now we can use driver.capabilities if needed
            # You could add this here if you want to dynamically set the Chrome version:
            # chrome_version = driver.capabilities["chrome"]["chromedriverVersion"].split(".")[0]
            # driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36'})

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
                        EC.presence_of_element_located((By.ID, "onetrust-consent-sdk"))
                    )

                    # Locate the accept button using its data-testid or id
                    accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
                    
                    # Click the accept button
                    accept_button.click()
                    
                    print("Clicked accept button")

                    # Wait for the banner to become invisible instead of checking for staleness
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.ID, "onetrust-banner-sdk"))
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

            # Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
            found_yesterday = False
            page = 1

            while not found_yesterday:
                try:
                    page_url = f"{main_url}?page={page}" if page > 1 else main_url
                    print(f"Scraping {page_url}...")
                    
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
                    articles = page_soup.find_all('a', class_=lambda x: x and 'style_link' in x)
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
                            link = article.get('href')

                            # Get title and translate it
                            title_div = article.find_all('div', recursive=False)[0].find_all('div', recursive=False)[0].find_all('div', recursive=False)[1].find_all('div', recursive=False)[0]
                            title = title_div.get_text(strip=True) if title_div else None
                            
                            # Get description
                            description_container = article.find('p', class_=lambda x: x and 'description' in x)
                            description = description_container.get_text(strip=True) if description_container else None
                                
                            # Get price by finding text with .00 pattern
                            price = None
                            price_text = article.find(text=lambda t: t and '.00' in t)
                            if price_text:
                                # Clean up the price text and remove any whitespace
                                price = price_text.strip()
                            
                            # Get the main product image container (first one only)
                            img_containers = article.find_all('div', class_=lambda x: x and 'image' in x)
                            img_container = img_containers[0] if img_containers else None
                            all_imgs = img_container.find_all('img') if img_container else []
                            
                            # Find first valid image URL
                            largest_image_url = None
                            for img in all_imgs:
                                img_src = img.get('src')
                                if img_src and 'money-guard' not in img_src and 'ai-icon' not in img_src:
                                    largest_image_url = img_src
                                    break

                            # print(f"Largest image URL: {largest_image_url}")
                            if not is_featured:
                                page_data_list.append({
                                    'title': {
                                        'original': title,
                                        'english': title,
                                    },
                                    'description': description,
                                    'main_image': largest_image_url,
                                    'link': "https://www.ricardo.ch"+link,
                                    'price': price,
                                    'timestamp': timestamp.isoformat() if timestamp else None,
                                })
                            
                        except Exception as e:
                            print(f"Error extracting data: {e}")

                    print(f"Found {len(page_data_list)} ads")
                    
                    # Count non-None values for each field
                    title_count = sum(1 for ad in page_data_list if ad['title']['original'])
                    url_count = sum(1 for ad in page_data_list if ad['link'])
                    price_count = sum(1 for ad in page_data_list if ad['price'])
                    image_count = sum(1 for ad in page_data_list if ad['main_image'])
                    
                    print(f"Breakdown of data found:")
                    print(f"- Titles: {title_count}")
                    print(f"- URLs: {url_count}")
                    print(f"- Prices: {price_count}")
                    print(f"- Images: {image_count}")
                    print(f"- Descriptions: {sum(1 for ad in page_data_list if ad['description'])}")
                    print(f"- Timestamps: {sum(1 for ad in page_data_list if ad['timestamp'])}")

                    # Store this page's data in the main dictionary
                    all_pages_data[page] = page_data_list
                    
                    # Optional: Add a small delay between pages to be polite
                    time.sleep(2)

                    page += 1
                    
                    # Replace existing page limit check with max_pages parameter
                    if page > max_pages:
                        print(f"Reached maximum page limit ({max_pages}), stopping...")
                        break

                except Exception as e:
                    print(f"Error in main loop: {e}")
                    break


            # Save the translated data
            with open('../next-frontend/public/jsons/ricardo_ads.json', 'w', encoding='utf-8') as f:
                json.dump(all_pages_data, f, ensure_ascii=False, indent=4)

            print(f"Scraping and translation completed. Data from {page-1} pages saved to ricardo_ads.json.")
            return all_pages_data

        finally:
            # Ensure the driver is properly quit
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Warning: Driver cleanup issue (this is normal): {e}")
            
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return {}  # Return empty dict on error

if __name__ == "__main__":
    scrape()  # Add this to allow direct execution
