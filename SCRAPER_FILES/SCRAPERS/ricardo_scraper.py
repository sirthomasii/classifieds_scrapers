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
    chrome_options.add_argument("--window-size=800,600")  # Reasonable default size
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--silent')  # Add this line to suppress DevTools messages

    # Create the driver with a timeout
    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path=None,  # Let it find the driver automatically
        suppress_welcome=True,        # Suppress welcome message
        use_subprocess=True          # Use subprocess to avoid circular import
    )
    
    # Minimize the window after creation
    # driver.minimize_window()
    
    return driver

def scrape(max_pages=2):
    driver = None
    try:
        driver = init_driver()
        
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


            # Initialize dictionary to store data by page
            all_pages_data = {}

            def scroll_gradually(driver, pause_time=0.25):
                """Scroll gradually and ensure images are loaded"""
                # print("\nDEBUG: Starting scroll_gradually...")
                
                # Initial longer wait for page to stabilize
                time.sleep(pause_time * 2)
                
                # Get scroll height
                total_height = driver.execute_script("return document.body.scrollHeight")
                
                # More robust image loading script
                driver.execute_script(r"""
                    window.forceLoadImages = function() {
                        let loaded = 0;
                        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
                        images.forEach(img => {
                            if (img.dataset.src && !img.src.includes(img.dataset.src)) {
                                img.src = img.dataset.src;
                                loaded++;
                            }
                            if (img.loading === 'lazy') {
                                img.loading = 'eager';
                                loaded++;
                            }
                        });
                        return loaded;
                    };
                """)
                
                # Scroll in smaller increments
                current_height = 0
                scroll_step = min(500, total_height / 20)
                
                while current_height < total_height:
                    driver.execute_script(f"window.scrollTo(0, {current_height});")
                    current_height += scroll_step
                    time.sleep(0.5)
                    
                    num_images = driver.execute_script("return window.forceLoadImages();")
                    if num_images > 0:
                        time.sleep(0.5)
                
                # Final scroll to bottom and pause
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time * 2)
                
                print("DEBUG: Finished scrolling")

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
                    
                    # print("Clicked accept button")

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

            def convert_chf_to_eur(chf_amount):
                """Convert CHF to EUR using a fixed conversion rate"""
                # Using an approximate conversion rate (you might want to use an API for real-time rates)
                CHF_TO_EUR_RATE = 1.05
                return int(chf_amount * CHF_TO_EUR_RATE)

            def clean_price(price_str):
                """Clean price string and convert to number"""
                if not price_str:
                    return None
                # Remove any spaces and replace Swiss thousand separator
                cleaned = price_str.replace(' ', '').replace("'", '')
                try:
                    return float(cleaned)
                except ValueError:
                    return None

            # Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
            found_yesterday = False
            page = 1

            # while page <= max_pages and not found_yesterday:  # Changed condition to <= instead of >
            while page <= max_pages:  # Changed condition to <= instead of >
                try:
                    page_url = f"{main_url}?page={page}" if page > 1 else main_url
                    # print(f"Scraping {page_url}...")
                    
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
                    articles = page_soup.find_all('a', class_=lambda x: x and 'style_link' in x)
                    # print(f"\nDEBUG: Found {len(articles)} total articles")

                    for idx, article in enumerate(articles):
                        try:
                            # Get the main product image container
                            img_containers = article.find_all('img', class_='MuiBox-root')
                            
                            # print(f"\nDEBUG: Article {idx + 1}:")
                            # print(f"- Number of img containers found: {len(img_containers)}")
                            
                            # Print details of the first image container if any exist
                            if img_containers:
                                first_img = img_containers[0]
                                # print(f"- First image src: {first_img.get('src', 'No src')}")
                                # print(f"- First image class: {first_img.get('class', 'No class')}")
                            else:
                                print("- No image containers found")
                            
                            # Original image extraction logic with debug
                            largest_image_url = None
                            for img in img_containers:
                                img_src = img.get('src', '')
                                if (img_src and 
                                    'img.ricardostatic.ch' in img_src and 
                                    'money-guard' not in img_src and 
                                    'ai-icon' not in img_src):
                                    largest_image_url = img_src
                                    break
                            
                            # print(f"- Final selected image URL: {largest_image_url}")
                            
                            # if not largest_image_url:
                            #     # If no image found, let's see the article's HTML
                            #     print(f"- Article HTML snippet: {article.prettify()[:200]}...")

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
                                
                            # Get price and convert to EUR
                            price = None
                            price_text = article.find(text=lambda t: t and '.00' in t)
                            if price_text:
                                price_chf = clean_price(price_text.strip())
                                price_eur = convert_chf_to_eur(price_chf) if price_chf is not None else None
                                price = {
                                    'chf': price_chf,
                                    'eur': price_eur
                                }
                            
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
                                    'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                })
                            
                        except Exception as e:
                            print(f"Error processing article {idx + 1}: {str(e)}")

                    # print(f"Found {len(page_data_list)} ads")
                    
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
                    listing['source'] = 'ricardo'
                    listing['scraped_at'] = current_time

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
        