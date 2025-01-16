import os
import importlib.util
import sys
from SERVICES.translation_service import TranslationService
from pymongo import MongoClient, UpdateOne
import subprocess
from datetime import datetime

# Define max pages per scraper
MULTIPLIER = 5

SCRAPER_CONFIG = {
    'blocket': 1*MULTIPLIER,
    'gumtree': 2*MULTIPLIER,
    'kleinanzeigen': 2*MULTIPLIER,
    'olx': 1*MULTIPLIER,
    'ricardo': 1*MULTIPLIER
}

def load_scraper(file_path):
    """Dynamically load a Python module from file path"""
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def upload_to_mongo(site_name, data):
    """Upload data directly to MongoDB without translation"""
    try:
        client = MongoClient("mongodb+srv://sirthomasii:ujvkc8W1eeYP9axW@fleatronics-1.lppod.mongodb.net/?retryWrites=true&w=majority&appName=fleatronics-1")
        db = client['fleatronics']
        collection = db['listings']

        # Create a unique compound index
        collection.create_index([
            ("link", 1),
            ("source", 1)
        ], unique=True)

        # Flatten and prepare data for upsert
        all_listings = []
        for page in data.values():
            for item in page:
                if item['link']:  # Only process items with valid links
                    filter_doc = {
                        "link": item['link'],
                        "source": site_name
                    }
                    item['last_updated'] = datetime.now().isoformat()
                    all_listings.append(UpdateOne(
                        filter_doc,
                        {'$set': item},
                        upsert=True
                    ))

        if all_listings:
            result = collection.bulk_write(all_listings, ordered=False)
            print(f"MongoDB update results for {site_name}:")
            print(f"- Inserted: {result.upserted_count}")
            print(f"- Modified: {result.modified_count}")
            print(f"- Matched: {result.matched_count}")

    except Exception as e:
        print(f"Error uploading to MongoDB: {e}")
    finally:
        client.close()

def run_scraper(scraper_path, translation_service):
    """Run a single scraper with custom max_pages parameter"""
    try:
        site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
        
        # Get max_pages from config, default to 1 if not specified
        max_pages = SCRAPER_CONFIG.get(site_name, 1)
        
        print(f"\n=== Starting {site_name} scraper with max_pages={max_pages} ===")
        
        scraper = load_scraper(scraper_path)
        data = scraper.scrape(max_pages=max_pages)
        
        if not data:
            print(f"Warning: No data returned from {site_name} scraper")
            return
            
        # Handle Gumtree separately since it's already in English
        if 'gumtree' in site_name.lower():
            upload_to_mongo(site_name, data)
        else:
            translation_service.add_to_queue(site_name, data)
            
        print(f"=== Completed scraping for {site_name} ===\n")
        
    except Exception as e:
        print(f"Error in {site_name} scraper: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    # Get the directory containing the scrapers
    scrapers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SCRAPERS')

    # Find all Python files containing "scraper" in the name, excluding leboncoin
    scraper_files = [
        os.path.join(scrapers_dir, f) 
        for f in os.listdir(scrapers_dir)
        if f.endswith('.py') 
        and 'scraper' in f.lower() 
        and 'leboncoin' not in f.lower()
        and f != '__init__.py'
    ]

    print(f"Found scrapers: {[os.path.basename(f) for f in scraper_files]}")
    print(f"Scraper configurations:")
    for name, pages in SCRAPER_CONFIG.items():
        print(f"- {name}: {pages} pages")

    # Initialize translation service
    translation_service = TranslationService()
    translation_service.start()

    # Run scrapers sequentially
    for scraper_path in scraper_files:
        run_scraper(scraper_path, translation_service)

    # Stop translation service and wait for completion
    translation_service.stop()

    # Call the upload service to upload translated JSONs to MongoDB
    print("Uploading translated JSONs to MongoDB...")
    subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "SERVICES", "upload_service.py")])
    print("Upload completed.")

if __name__ == "__main__":
    main()