import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
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

# Configure Selenium WebDriver
options = uc.ChromeOptions()
options.add_argument('--disable-gpu')
options.add_argument("--window-size=1920,1080")
options.add_argument("--start-maximized")
options.add_argument('--disable-extensions')
options.add_argument('--disable-notifications')
options.add_argument('--disable-popup-blocking')
# options.add_argument('--headless')  # Enable headless mode if needed

# Modify the driver initialization to use a context manager
try:
    driver = uc.Chrome(options=options)
    
    try:
        # URL to scrape
        main_url = "https://www.leboncoin.fr/recherche?category=14&shippable=1&sort=time"

        # First navigate to the URL
        driver.get(main_url)

        # Then clear everything
        try:
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            print(f"Warning: Could not clear browser data: {e}")

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
            """Find and click the accept cookies button with human-like behavior"""
            try:
                print("Looking for cookie consent popup...")
                
                # Randomized initial wait (simulating page load reading)
                time.sleep(random.uniform(2.0, 7.0))
                
                # Add more random mouse movements before looking for the button
                action = ActionChains(driver)
                for _ in range(random.randint(3, 6)):
                    x = random.randint(50, 900)
                    y = random.randint(50, 700)
                    action.move_by_offset(x, y)\
                          .pause(random.uniform(0.05, 0.5))\
                          .perform()
                    action.reset_actions()
                
                # Wait for the accept button with a randomized selector strategy
                selectors = [
                    "button#didomi-notice-agree-button",
                    "[aria-label*='accept']",
                    "[data-testid*='cookie-accept']"
                ]
                
                for selector in selectors:
                    try:
                        accept_button = WebDriverWait(driver, random.uniform(8, 12)).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        if accept_button:
                            break
                    except:
                        continue
                        
                print("Found accept button")
                
                # Simulate human-like cursor movement to button
                action = ActionChains(driver)
                
                # Move cursor in a slightly curved path
                steps = random.randint(7, 12)
                for i in range(steps):
                    offset_x = random.randint(-15, 15)
                    offset_y = random.randint(-15, 15)
                    action.move_by_offset(offset_x, offset_y)\
                          .pause(random.uniform(0.03, 0.15))
                
                # Click with offset
                button_location = accept_button.location
                button_size = accept_button.size
                offset_x = random.uniform(0.1, 0.9) * button_size['width']
                offset_y = random.uniform(0.1, 0.9) * button_size['height']
                
                action.move_to_element_with_offset(accept_button, offset_x, offset_y)\
                      .pause(random.uniform(0.2, 0.8))\
                      .click()\
                      .perform()
                
                print("Clicked accept button")
                
                # Randomized post-click wait
                time.sleep(random.uniform(2.0, 5.0))
                
                print("Pausing for verification - press Enter to continue...")
                input()
                
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
            
            if 'today' in time_text:
                # Extract HH:MM from "today at HH:MM"
                time_part = time_text.replace('today at', '').strip()
                hour, minute = map(int, time_part.split(':'))
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif 'yesterday' in time_text:
                # Handle "Yesterday HH:MM" format
                time_part = time_text.replace('yesterday', '').strip()
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
            articles = page_soup.find_all('li', class_=lambda x: x and 'styles_adCard' in x)
            for article in articles:
                try:
                    # Add time extraction
                    time_container = article.find('p', class_=lambda x: x and 'styled__Time' in x)
                    time_text = time_container.get_text(strip=True) if time_container else None
                    timestamp = parse_time(time_text)
                    
                    # Check if this post is from yesterday or earlier
                    if timestamp and timestamp.date() < datetime.now().date():
                        found_yesterday = True

                    # Get link
                    link_elem = article.find('a', attrs={'data-qa-id': 'aditem_container'})
                    link = link_elem.get('href') if link_elem else None
                    
                    # Get title and translate it
                    title_container = article.find('p', attrs={'data-qa-id': 'aditem_title'})
                    title = title_container.get('title') if title_container else None
                        
                    # Get price from the p tag with data-test-id="price"
                    price_container = article.find('p', attrs={'data-test-id': 'price'})
                    if price_container:
                        # Extract text and clean it up
                        price_text = price_container.get_text(strip=True)
                        # Remove '€' symbol and any whitespace, then convert to number
                        price = price_text.replace('€', '').strip()
                    else:
                        price = None
                    
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
                        'link': link,
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

        # Translate titles using deep_translator
        if translator is not None:
            print("Translating titles...")
            for page_num in all_pages_data:
                for ad in all_pages_data[page_num]:
                    if ad['title']['original']:
                        try:
                            translated_title = translator.translate(ad['title']['original'])
                            ad['title']['english'] = translated_title
                        except Exception as e:
                            print(f"Translation error for '{ad['title']['original']}': {e}")
                            ad['title']['english'] = ad['title']['original']
                        time.sleep(0.1)
        else:
            print("Skipping translation (will be handled by run_all_scrapers.py)")
            for page_num in all_pages_data:
                for ad in all_pages_data[page_num]:
                    ad['title']['english'] = None

        # Save the data
        with open('../next-frontend/public/jsons/leboncoin_ads.json', 'w', encoding='utf-8') as f:
            json.dump(all_pages_data, f, ensure_ascii=False, indent=4)

        print(f"Scraping and translation completed. Data from {page-1} pages saved to leboncoin_ads.json.")

    finally:
        # Ensure the driver is properly quit
        try:
            if driver and driver.service.process:
                driver.quit()
        except Exception as e:
            print(f"Warning: Driver cleanup issue (this is normal): {e}")
            
except Exception as e:
    print(f"Error initializing driver: {e}")
