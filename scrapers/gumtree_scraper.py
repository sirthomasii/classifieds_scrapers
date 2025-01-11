from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from deep_translator import GoogleTranslator
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

# Initialize translator
translator = GoogleTranslator(source='auto', target='en')

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
        
        print("Clicked accept button")
        
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

def parse_time_text(time_text):
    """Convert relative time text to datetime object"""
    if not time_text:
        return None
        
    now = datetime.now()
    time_text = time_text.lower().strip()
    
    # Handle "just now"
    if "just now" in time_text:
        return now
    
    # Handle "X min/minutes ago"
    if "min" in time_text:
        minutes = int(''.join(filter(str.isdigit, time_text)))
        return now - timedelta(minutes=minutes)
    
    # Handle "X hour(s) ago"
    if "hour" in time_text:
        hours = int(''.join(filter(str.isdigit, time_text)))
        return now - timedelta(hours=hours)
        
    # Handle "Today HH:MM"
    if "today" in time_text:
        time_part = time_text.replace('today', '').strip()
        hour, minute = map(int, time_part.split(':'))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
    # Handle "Yesterday HH:MM"
    if "yesterday" in time_text:
        time_part = time_text.replace('yesterday', '').strip()
        hour, minute = map(int, time_part.split(':'))
        yesterday = now - timedelta(days=1)
        return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return None

# Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
found_yesterday = False
page = 1

while not found_yesterday:
    page_url = f"{main_url}page{page}" if page > 1 else main_url
    
    print(f"Scraping {page_url}...")
    
    # Get the page and wait for initial content
    driver.get(page_url)
    
    # Handle cookie popup before proceeding (but don't stop if it fails)
    if page == 1:  # Only try this on first page
        accept_cookies(driver)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "article"))
    )
    
    # Continue with scrolling...
    scroll_gradually(driver)
    
    page_source = driver.page_source
    page_soup = BeautifulSoup(page_source, 'html.parser')

    # Extract all ad URLs, titles, and images
    page_data_list = []
    articles = page_soup.find_all('article')
    for article in articles:
        try:
            # Check if ad is featured
            featured_div = article.find('div', string='Featured')
            is_featured = featured_div is not None
            
            # Add time extraction
            time_container = article.find('div', attrs={'data-q': 'tile-datePosted'})
            time_text = time_container.get_text(strip=True) if time_container else None
            timestamp = parse_time_text(time_text) if time_text else None
            
            # Only set found_yesterday if the ad is not featured
            if time_text and 'yesterday' in time_text.lower() and not is_featured:
                found_yesterday = True

            # Get link
            link_elem = article.find('a', attrs={'data-q': 'search-result-anchor'})
            link = link_elem.get('href') if link_elem else None
            
            # Get title and translate it
            title_container = article.find('div', attrs={'data-q': 'tile-title'})
            title = title_container.get_text(strip=True) if title_container else None
            
            # Get description
            description_container = article.find('div', attrs={'data-q': 'tile-description'})
            description = description_container.find('p').get_text(strip=True) if description_container else None
                        
            # Get price from Price__StyledPrice
            price_container = article.find('div', attrs={'data-q': 'tile-price'})
            price = price_container.get_text(strip=True) if price_container else None
            
            # Get image from figure tag
            figure = article.find('figure', class_='listing-tile-thumbnail-image')
            if figure:
                img = figure.find('img')
                largest_image_url = img.get('data-src') or img.get('src') if img else None
            else:
                print("No figure tag found")
                largest_image_url = None

            # print(f"Largest image URL: {largest_image_url}")
            if not is_featured:
                page_data_list.append({
                    'title': {
                        'original': title,
                        'english': title,
                    },
                    'description': description,
                    'main_image': largest_image_url,
                    'link': "https://www.gumtree.com"+link,
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
    
    # Add a safety limit to prevent infinite loops
    if page > 2:  # Adjust this number as needed
        print("Reached maximum page limit, stopping...")
        break

# Close the driver
driver.quit()

# # Translate titles using deep_translator
# print("Translating titles...")

# # Collect all titles
# all_titles = []
# title_map = {}  # To map translated titles back to their ads

# for page_num in all_pages_data:
#     for ad in all_pages_data[page_num]:
#         if ad['title']['original']:
#             all_titles.append(ad['title']['original'])
#             # Store reference to this ad using its title as key
#             title_map[ad['title']['original']] = ad

# # Function to split titles into chunks
# def split_into_chunks(titles, max_length=5000):
#     chunks = []
#     current_chunk = []
#     current_length = 0

#     for title in titles:
#         title_length = len(title) + 2  # Account for ". " separator
#         if current_length + title_length > max_length:
#             chunks.append(current_chunk)
#             current_chunk = []
#             current_length = 0
#         current_chunk.append(title)
#         current_length += title_length

#     if current_chunk:
#         chunks.append(current_chunk)

#     return chunks

# # Measure time for chunked single string translation
# start_time_single = time.time()
# try:
#     chunks = split_into_chunks(all_titles)
#     translated_titles = []

#     for chunk in chunks:
#         single_string = ". ".join(chunk)
#         translated_chunk = translator.translate(single_string)
#         translated_titles.extend(translated_chunk.split(". "))

#     for original, translated in zip(all_titles, translated_titles[:len(all_titles)]):  # Ensure we only use as many translations as we have titles
#         title_map[original]['title']['english'] = translated
# except Exception as e:
#     print(f"Single string translation error: {e}")
#     for title in all_titles:
#         title_map[title]['title']['english'] = title
# end_time_single = time.time()
# print(f"Chunked single string translation took {end_time_single - start_time_single:.2f} seconds")

# Save the translated data
with open('../next-frontend/public/jsons/gumtree_ads.json', 'w', encoding='utf-8') as f:
    json.dump(all_pages_data, f, ensure_ascii=False, indent=4)

print(f"Scraping and translation completed. Data from {page-1} pages saved to gumtree_ads.json.")
