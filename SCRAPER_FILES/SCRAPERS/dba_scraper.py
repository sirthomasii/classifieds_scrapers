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
    chrome_options.add_argument("--window-size=100,100")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--silent')  # Add this line to suppress DevTools messages
    try:
        # Create the driver with a timeout
        driver = uc.Chrome(
            options=chrome_options,
            driver_executable_path=None,  # Let it find the driver automatically
            suppress_welcome=True,        # Suppress welcome message
            use_subprocess=False          # Changed to False to avoid cleanup issues
        )
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        return None

def scrape(max_pages=2):
    driver = None
    try:
        driver = init_driver()
        if not driver:
            return {}
        
        # URL to scrape
        main_url = "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/side-"
        driver.get(main_url)
        
        # Wrap the main scraping code in a try-finally block to ensure cleanup
        try:
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
                
                # print("DEBUG: Finished scrolling")

            def accept_cookies(driver):
                """Find and click the accept cookies button"""
                try:
                    # print("Looking for cookie consent button...")

                    # Wait for iframe to be present and switch to it
                    iframe = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#sp_message_iframe_1237879"))
                    )
                    driver.switch_to.frame(iframe)

                    # Now find and click the button within the iframe
                    cookie_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((
                            By.CSS_SELECTOR, 
                            "button.message-button.sp_choice_type_ACCEPT_ALL[title='Tillad alle']"
                        ))
                    )

                    # Click the button
                    cookie_button.click()
                    
                    # Switch back to default content
                    driver.switch_to.default_content()
                    
                    # print("Clicked accept button")

                    # Wait for the banner to disappear (checking in main frame)
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.ID, "sp_message_container_1237879"))
                    )

                    return True

                except Exception as e:
                    print(f"Could not handle cookie popup: {e}")
                    # Make sure we switch back to default content even if there's an error
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                    return False


            # Remove the PAGES_TO_SCRAPE constant as we'll now use dynamic stopping
            found_yesterday = False
            page = 1
            
            # Handle cookie popup once before starting the loop
            accept_cookies(driver)

            while page <= max_pages:  # Changed condition to <= instead of >
                try:
                    page_url = f"{main_url}{page}/?soegfra=1050&radius=500"
                    # print(f"Scraping {page_url}...")
                    
                    driver.get(page_url)
                    
                    # Remove the duplicate cookie check
                    # if page == 1:  # Only try this on first page
                    #     accept_cookies(driver)
                    
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
                    articles = page_soup.find_all('tr', class_=lambda x: x and 'dbaListing' in x)
                    # print(f"\nDEBUG: Found {len(articles)} total articles")

                    for idx, article in enumerate(articles):
                        try:
                            # Get the main product image
                            img_element = article.find('img', class_='image-thumbnail')
                            largest_image_url = img_element.get('src') if img_element else None
                            
                            # Remove the S300X300 suffix to get full resolution image
                            if largest_image_url and '?class=S300X300' in largest_image_url:
                                largest_image_url = largest_image_url.replace('?class=S300X300', '')

                            # Check if ad is featured
                            featured_div = article.find('div', string='Featured')
                            is_featured = featured_div is not None
                                                            
                            # Get link
                            link = article.find('a', class_=lambda x: x and 'listingLink' in x)
                            link_url = link.get('href') if link else None  # Extract the href attribute

                            # Get title from headline span, handling nested font elements
                            title_span = article.find('span', class_='text')
                            if title_span:
                                # Get text from innermost font element, or fall back to direct text
                                font_elements = title_span.find_all('font')
                                if font_elements:
                                    full_title = font_elements[-1].get_text(strip=True)
                                else:
                                    full_title = title_span.get_text(strip=True)
                            else:
                                full_title = None
                            title = ' '.join(full_title.split()[:6]) if full_title else None
                                                            
                            # Get price
                            price = None
                            price_element = article.find('span', class_='price')
                            if price_element:
                                # Extract price text and clean it
                                price_text = price_element.get_text(strip=True)
                                try:
                                    # Remove 'kr.' and any whitespace
                                    cleaned_price = price_text.replace('kr.', '').strip()
                                    # Remove any thousand separators (commas) first
                                    cleaned_price = cleaned_price.replace(',', '')
                                    # Convert to float
                                    price_dkk = float(cleaned_price)
                                    # Convert DKK to EUR (1 DKK ≈ 0.134 EUR as of March 2024)
                                    price = int(price_dkk * 0.134)
                                except (ValueError, TypeError):
                                    price = None
                            
                            if not is_featured:
                                page_data_list.append({
                                    'title': {
                                        'original': title,
                                        'english': title,
                                    },
                                    'main_image': largest_image_url,
                                    'link': link_url,  # Use the extracted URL string instead of the Tag object
                                    'price': price,
                                    'timestamp': datetime.now().isoformat()
                                })
                            
                        except Exception as e:
                            print(f"Error processing article {idx + 1}: {str(e)}")

                    # Store this page's data in the main dictionary
                    all_pages_data[page] = page_data_list
                    
                    # Optional: Add a small delay between pages to be polite
                    time.sleep(2)

                    page += 1
                    
                    # Replace existing page limit check with max_pages parameter
                    if page > max_pages:
                        # print(f"Reached maximum page limit ({max_pages}), stopping...")
                        break

                except Exception as e:
                    print(f"Error in main loop: {e}")
                    break

            # After scraping
            current_time = datetime.now().isoformat()
            for page in all_pages_data.values():
                for listing in page:
                    listing['source'] = 'dba'
                    listing['scraped_at'] = current_time

            return all_pages_data

        finally:
            # Ensure the driver is properly quit
            if driver:
                try:
                    driver.close()  # Close all windows first
                    time.sleep(1)   # Give it a moment to close windows
                    driver.quit()   # Then quit the driver
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
        