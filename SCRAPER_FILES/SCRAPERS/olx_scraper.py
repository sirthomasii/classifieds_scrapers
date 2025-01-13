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
from pymongo import MongoClient
from selenium.webdriver.common.action_chains import ActionChains

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def init_driver():
    """Initialize and return a new driver instance"""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--window-size=100,100")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    # chrome_options.add_argument('--window-position=-32000,-32000')
    chrome_options.add_argument('--headless')  # Enable headless mode

    # Create the driver with a timeout
    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path=None,  # Let it find the driver automatically
        suppress_welcome=True,        # Suppress welcome message
        use_subprocess=True          # Use subprocess to avoid circular import
    )
    return driver

def scrape(max_pages=1):
    driver = None
    try:
        driver = init_driver()
        
        # Initialize MongoDB client
        client = MongoClient("mongodb+srv://sirthomasii:ujvkc8W1eeYP9axW@fleatronics-1.lppod.mongodb.net/?retryWrites=true&w=majority&appName=fleatronics-1")
        db = client['fleatronics']
        collection = db['listings']

        # Move all the existing scraping code here
        # URL to scrape
        main_url = "https://www.olx.ro/electronice-si-electrocasnice/"
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


            # Initialize dictionary to store data by page
            all_pages_data = {}

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

            def parse_time(time_text):
                """Convert time formats to datetime object"""
                now = datetime.now()
                
                if not time_text:
                    return None
                    
                time_text = time_text.lower()
                
                # Handle Romanian format "Reactualizat Azi la HH:MM"
                if 'azi' in time_text:
                    try:
                        # Extract time from format "HH:MM"
                        time_part = time_text.split('la')[-1].strip()
                        hour, minute = map(int, time_part.split(':'))
                        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    except:
                        return None
                # Handle "ieri la HH:MM"
                elif 'ieri' in time_text:
                    try:
                        time_part = time_text.split('la')[-1].strip()
                        hour, minute = map(int, time_part.split(':'))
                        yesterday = now - timedelta(days=1)
                        return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    except:
                        return None
                
                return None

            def parse_srcset(srcset_str):
                """Extract the highest resolution image URL from srcset"""
                if not srcset_str:
                    return None
                
                # Split the srcset into individual entries
                entries = srcset_str.strip().split(', ')
                # Get the last entry and extract just the URL part
                if entries:
                    last_entry = entries[-1]
                    return last_entry.split(' ')[0]
                return None

            # Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
            found_yesterday = False
            page = 1

            # while page <= max_pages and not found_yesterday:  # Changed condition to <= instead of >
            while page <= max_pages:  # Changed condition to <= instead of >
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
                    
                    # Get page source and parse with BeautifulSoup
                    page_source = driver.page_source
                    page_soup = BeautifulSoup(page_source, 'html.parser')

                    # Extract all ad URLs, titles, and images
                    page_data_list = []
                    articles = page_soup.find_all('div', attrs={'data-testid': 'l-card'})
                    # print(f"\nDEBUG: Found {len(articles)} total articles")

                    for idx, article in enumerate(articles):
                        try:
                            # print(f"\nProcessing article {idx + 1}:")
                            
                            # Debug the article structure
                            # print(f"Article HTML:\n{article.prettify()[:500]}")
                            
                            # Get link first - we'll use this to skip invalid entries
                            link_elem = article.find('a')
                            # print(f"Link element found: {link_elem is not None}")
                            
                            if not link_elem or not link_elem.get('href'):
                                print("Skipping - No valid link found")
                                continue

                            link = link_elem['href']
                            # print(f"Link: {link}")

                            # Get title
                            title_div = article.find('h4')  # Changed from h4 to h6
                            title = title_div.get_text(strip=True) if title_div else None
                            # print(f"Title: {title}")
                            
                            # Find image with data-testid
                            img = article.find('img')
                            img_src = None
                            if img:
                                # Try to get high-res image from srcset first
                                srcset = img.get('srcset')
                                if srcset:
                                    img_src = parse_srcset(srcset)
                                # Fallback to src if no srcset or parsing failed
                                if not img_src:
                                    img_src = img.get('src', '')
                            
                            # Skip placeholder/thumbnail images
                            if img_src and 'no_thumbnail' in img_src:
                                img_src = None
                            
                            # Get price
                            price_container = article.find('p', attrs={'data-testid': 'ad-price'})
                            price = price_container.get_text(strip=True) if price_container else None

                            # Check if ad is featured
                            featured_div = article.find('div', string='PROMOVAT')
                            is_featured = featured_div is not None
                            
                            # Locate the parent container of the time
                            time_container = article.find('p', attrs={'data-testid': 'location-date'})
                            time_text = time_container.get_text(strip=True) if time_container else None
                            timestamp = parse_time(time_text) if time_text else None
                                
                            # Check if this post is from yesterday or earlier
                            if timestamp and timestamp.date() < datetime.now().date():
                                found_yesterday = True

                            # Get description
                            description_container = article.find('p', class_=lambda x: x and 'description' in x)
                            description = description_container.get_text(strip=True) if description_container else None
                                
                            if not is_featured:
                                page_data_list.append({
                                    'title': {
                                        'original': title,
                                        'english': title,
                                    },
                                    'description': description,
                                    'main_image': img_src,
                                    'link': f"https://www.olx.ro{link}" if link else None,
                                    'price': price,
                                    'timestamp': timestamp.isoformat() if timestamp else None,
                                })
                            
                        except Exception as e:
                            print(f"Error processing article {idx + 1}: {str(e)}")

                    print(f"Found {len(page_data_list)} ads")
                    
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

            # After scraping
            current_time = datetime.now().isoformat()
            for page in all_pages_data.values():
                for listing in page:
                    listing['source'] = 'olx'
                    listing['scraped_at'] = current_time

            # Close MongoDB connection
            client.close()

            return all_pages_data

        finally:
            # Ensure the driver is properly quit
            try:
                if 'driver' in locals():
                    driver.quit()
            except Exception as e:
                print(f"Warning: Error while closing driver: {e}")
            
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return {}  # Return empty dict on error

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
        print(f"- Descriptions: {sum(1 for ad in all_listings if ad['description'])}")
        print(f"- Timestamps: {sum(1 for ad in all_listings if ad['timestamp'])}")
