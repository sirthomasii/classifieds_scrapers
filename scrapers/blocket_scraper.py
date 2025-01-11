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
main_url = "https://www.blocket.se/annonser/hela_sverige/elektronik?cg=5000"

# First navigate to the URL
driver.get(main_url)

# Then clear everything
try:
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")
except Exception as e:
    print(f"Warning: Could not clear browser data: {e}")

# Verify we're on the right page
current_url = driver.current_url
if "elektronik" not in current_url:  # adjust this based on your expected URL
    print(f"Warning: Unexpected URL: {current_url}")
    print(f"Expected URL to contain 'elektronik'")
    # Optionally force the correct URL
    driver.get(main_url)

# Initialize dictionary to store data by page
all_pages_data = {}

# Initialize translator
translator = GoogleTranslator(source='auto', target='en')

def scroll_gradually(driver, pause_time=0.125):
    """Scroll until no new content loads"""
    # Initial wait for first batch of content
    time.sleep(pause_time)
    
    # JavaScript function to scroll gradually
    scroll_script = """
        return new Promise((resolve) => {
            const windowHeight = window.innerHeight;
            const scrollStep = windowHeight ;  
            const scrollInterval = setInterval(() => {
                const scrollHeight = document.documentElement.scrollHeight;
                const scrollPosition = window.pageYOffset;
                
                if (scrollPosition + windowHeight >= scrollHeight) {
                    clearInterval(scrollInterval);
                    resolve('bottom');
                } else {
                    window.scrollBy(0, scrollStep);
                }
            }, 125);  // Scroll every 250ms
        });
    """
    
    # Execute the gradual scroll
    driver.execute_script(scroll_script)
    
    # Wait for scrolling to complete
    while True:
        current_height = driver.execute_script("return document.documentElement.scrollHeight")
        time.sleep(0.125)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        
        if current_height == new_height:
            break

def accept_cookies(driver):
    """Find and click the accept cookies button"""
    try:
        print("Looking for cookie consent iframe...")
        
        # Wait for the iframe to be present
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='sp_message_iframe']"))
        )
        
        # Switch to the iframe context
        driver.switch_to.frame(iframe)
        print("Switched to iframe context")
        
        # Look for the accept button within the iframe
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Godkänn alla cookies']"))
            )
            print("Found accept button")
            accept_button.click()
            print("Clicked accept button")
        except Exception as e:
            print(f"Failed to find/click accept button: {e}")
        
        # Switch back to default content
        driver.switch_to.default_content()
        print("Switched back to main context")
        
        return True
        
    except Exception as e:
        print(f"Could not handle cookie popup: {e}")
        # Make sure we're back in the main context
        driver.switch_to.default_content()
        return False

def parse_swedish_time(time_text):
    """Convert Swedish time text to datetime object"""
    now = datetime.now()
    if 'Idag' in time_text:
        # Extract HH:MM from "Idag HH:MM"
        time_part = time_text.replace('Idag', '').strip()
        hour, minute = map(int, time_part.split(':'))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif 'Igår' in time_text:
        # Extract HH:MM from "Igår HH:MM"
        time_part = time_text.replace('Igår', '').strip()
        hour, minute = map(int, time_part.split(':'))
        yesterday = now - timedelta(days=1)
        return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return None

# Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
found_yesterday = False
page = 1

while not found_yesterday:
    page_url = f"{main_url}&page={page}" if page > 1 else main_url
    
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
            # Add time extraction
            time_container = article.find('p', class_=lambda x: x and 'styled__Time' in x)
            time_text = time_container.get_text(strip=True) if time_container else None
            timestamp = parse_swedish_time(time_text) if time_text else None
            
            if time_text and 'Igår' in time_text:
                found_yesterday = True

            # Get link
            link_elem = article.find('a', class_=lambda x: x and 'StyledTitleLink' in x)
            link = link_elem.get('href') if link_elem else None
            
            # Get title and translate it
            title_container = article.find('span', class_=lambda x: x and 'styled__SubjectContainer' in x)
            title = title_container.get_text(strip=True) if title_container else None
                        
            # Get price from Price__StyledPrice
            price_container = article.find('div', class_=lambda x: x and 'Price__StyledPrice' in x)
            price = price_container.get_text(strip=True) if price_container else None
            
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
            
            page_data_list.append({
                'title': {
                    'original': title,
                    'english': None
                },
                'description': None,
                'main_image': largest_image_url,
                'link': "https://www.blocket.se"+link,
                'price': price,
                'timestamp': timestamp.isoformat() if timestamp else None  # Add timestamp to output
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

# Translate titles using deep_translator
print("Translating titles...")

# Collect all titles
all_titles = []
title_map = {}  # To map translated titles back to their ads

for page_num in all_pages_data:
    for ad in all_pages_data[page_num]:
        if ad['title']['original']:
            all_titles.append(ad['title']['original'])
            # Store reference to this ad using its title as key
            title_map[ad['title']['original']] = ad

# Function to split titles into chunks
def split_into_chunks(titles, max_length=5000):
    chunks = []
    current_chunk = []
    current_length = 0

    for title in titles:
        title_length = len(title) + 2  # Account for ". " separator
        if current_length + title_length > max_length:
            chunks.append(current_chunk)
            current_chunk = []
            current_length = 0
        current_chunk.append(title)
        current_length += title_length

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# Measure time for chunked single string translation
start_time_single = time.time()
try:
    chunks = split_into_chunks(all_titles)
    translated_titles = []

    for chunk in chunks:
        single_string = ". ".join(chunk)
        translated_chunk = translator.translate(single_string)
        translated_titles.extend(translated_chunk.split(". "))

    for original, translated in zip(all_titles, translated_titles[:len(all_titles)]):  # Ensure we only use as many translations as we have titles
        title_map[original]['title']['english'] = translated
except Exception as e:
    print(f"Single string translation error: {e}")
    for title in all_titles:
        title_map[title]['title']['english'] = title
end_time_single = time.time()
print(f"Chunked single string translation took {end_time_single - start_time_single:.2f} seconds")

# Create directory if it doesn't exist
os.makedirs('./jsons', exist_ok=True)

# Save the translated data
with open('../next-frontend/public/jsons/blocket_ads.json', 'w', encoding='utf-8') as f:
    json.dump(all_pages_data, f, ensure_ascii=False, indent=4)

print(f"Scraping and translation completed. Data from {page-1} pages saved to blocket_ads.json.")
