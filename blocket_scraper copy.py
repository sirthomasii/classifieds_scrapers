from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator


# Configure Selenium WebDriver (make sure you have ChromeDriver installed)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

# URL to scrape
url = "https://www.blocket.se/annonser/hela_sverige/fritid_hobby?cg=6000"

# Configure number of pages to scrape
PAGES_TO_SCRAPE = 10

# Initialize dictionary to store data by page
all_pages_data = {}

# Initialize translator

for page in range(1, PAGES_TO_SCRAPE + 1):
    # Modify URL for pagination
    page_url = f"{url}&page={page}" if page > 1 else url
    
    # Print the URL being scraped
    print(f"Scraping URL: {page_url}")
        
    # Get and cache the page source
    driver.get(page_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "article"))
    )
    page_source = driver.page_source
    page_soup = BeautifulSoup(page_source, 'html.parser')

    # Extract all ad URLs, titles, and images
    page_data_list = []
    articles = page_soup.find_all('article')
    for article in articles:
        try:
            # Get link
            link_elem = article.find('a', class_=lambda x: x and 'StyledTitleLink' in x)
            link = link_elem.get('href') if link_elem else None
                        
            # Get title (without translation)
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
                if source and source.get('srcset'):
                    # Split srcset and parse into width-url pairs
                    srcset_items = source['srcset'].split(',')
                    # Parse each item into (url, width) pairs
                    image_versions = []
                    for item in srcset_items:
                        parts = item.strip().split()
                        if len(parts) == 2:
                            url, width = parts
                            width = int(width.rstrip('w'))
                            image_versions.append((url, width))
                    
                    # Get URL of highest resolution version
                    if image_versions:
                        image_540 = max(image_versions, key=lambda x: x[1])[0]
                    else:
                        image_540 = None
                else:
                    # Fallback to img tag src if no srcset
                    img = picture.find('img')
                    image_540 = img.get('src') if img else None
            else:
                image_540 = None
            
            page_data_list.append({
                'title': {
                    'original': title,
                    'english': None  # We'll fill this later
                },
                'description': None,
                'main_image': image_540,
                'link': link,
                'price': price
            })
            
        except Exception as e:
            print(f"Error extracting data: {e}")

    print(f"Found {len(page_data_list)} ads")

    # Store this page's data in the main dictionary
    all_pages_data[page] = page_data_list
    
    # Optional: Add a small delay between pages to be polite
    time.sleep(2)

# Close the driver
driver.quit()

# After scraping is done, translate all titles using Google Translate in batch
print("Translating titles...")
translator = GoogleTranslator(source='sv', target='en')

# Collect all titles
all_titles = []
title_map = {}  # To map translated titles back to their ads

for page_num in all_pages_data:
    for ad in all_pages_data[page_num]:
        if ad['title']['original']:
            all_titles.append(ad['title']['original'])
            # Store reference to this ad using its title as key
            title_map[ad['title']['original']] = ad

# Translate all titles at once
try:
    translations = translator.translate_batch(all_titles)
    
    # Map translations back to their ads
    for original, translated in zip(all_titles, translations):
        title_map[original]['title']['english'] = translated

except Exception as e:
    print(f"Translation error: {e}")
    # Fallback: keep original titles if translation fails
    for title in all_titles:
        title_map[title]['title']['english'] = title

# Save the translated data
with open('blocket_ads.json', 'w', encoding='utf-8') as f:
    json.dump(all_pages_data, f, ensure_ascii=False, indent=4)

print("Scraping and translation completed!")
