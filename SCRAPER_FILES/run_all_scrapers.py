import os
import importlib.util
import sys
from SERVICES.translation_service import TranslationService
from SERVICES.upload_service import upload_data_to_mongo
from SERVICES.database_service import DatabaseService
import subprocess
from datetime import datetime

# Define num pages per batch
SCRAPER_CONFIG = {
    'kleinanzeigen': 3,
    'blocket': 2,
    'gumtree': 2,
    'tori': 2,
    'olx': 2,
    'ricardo': 1,
    'dba': 1
}

class ScraperStats:
    def __init__(self):
        self.total_ads = 0
        self.complete_ads = 0  # ads with title, image, and link
        self.new_ads = 0      # ads successfully inserted into MongoDB
        self.data = None      # Store the scraped data
        self.category_stats = {}  # Add category stats storage

def calculate_completeness(data):
    """Calculate percentage of complete ads (having title, image, and link)"""
    total_ads = 0
    complete_ads = 0
    
    for page in data.values():
        for item in page:
            total_ads += 1
            if (item.get('link') and 
                item.get('main_image') and 
                item.get('title', {}).get('original')):
                complete_ads += 1
    
    return total_ads, complete_ads

def load_scraper(file_path):
    """Dynamically load a Python module from file path"""
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def check_duplicates(db_service, data):
    """Check percentage of duplicate links in a batch of data"""
    if not data:
        return 0
    
    # Extract all links from the batch
    links = []
    for page in data.values():
        links.extend(item['link'] for item in page if item.get('link'))
    
    return db_service.check_duplicate_links(links)

def run_scraper(scraper_path, translation_service):
    """Run a single scraper"""
    stats = ScraperStats()
    try:
        site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
        
        # Get batch size from config, default to 2 if not specified
        batch_size = SCRAPER_CONFIG.get(site_name, 2)
        
        print(f"\n=== Starting {site_name} scraper with batch_size={batch_size} ===")
        
        scraper = load_scraper(scraper_path)
        all_data = scraper.scrape(max_pages=batch_size)
        
        # Store the data in stats
        stats.data = all_data
        
        if not all_data:
            print(f"Warning: No data returned from {site_name} scraper")
            return stats
            
        # Calculate completeness stats
        stats.total_ads, stats.complete_ads = calculate_completeness(all_data)
        
        # Handle Gumtree separately since it's already in English
        if 'gumtree' in site_name.lower():
            stats.total_ads, stats.new_ads, stats.complete_ads, stats.category_stats = upload_data_to_mongo(site_name, all_data)
        else:
            # Store the data for translation and capture new_ads count
            translation_service.add_to_queue(site_name, all_data)
            # Initialize stats without uploading
            stats.total_ads = sum(len(page) for page in all_data.values())
            stats.complete_ads = sum(1 for page in all_data.values() 
                                    for item in page 
                                    if item.get('link') and 
                                       item.get('main_image') and 
                                       item.get('title', {}).get('original'))
            
            # Track categories without uploading
            for page in all_data.values():
                for item in page:
                    category = item.get('category', 'uncategorized')
                    if category not in stats.category_stats:
                        stats.category_stats[category] = {'total': 0, 'new': 0, 'complete': 0}
                    stats.category_stats[category]['total'] += 1
                    if (item.get('link') and 
                        item.get('main_image') and 
                        item.get('title', {}).get('original')):
                        stats.category_stats[category]['complete'] += 1

        print(f"=== Completed scraping for {site_name} ===\n")
        return stats
        
    except Exception as e:
        print(f"Error in {site_name} scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return stats

def main():
    scraper_results = {}
    # Get the directory containing the scrapers
    scrapers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SCRAPERS')

    # Find all Python files containing "scraper" in the name, excluding leboncoin
    # and only include scrapers that are in SCRAPER_CONFIG
    scraper_files = [
        os.path.join(scrapers_dir, f) 
        for f in os.listdir(scrapers_dir)
        if f.endswith('.py') 
        and 'scraper' in f.lower() 
        and 'leboncoin' not in f.lower()
        and f != '__init__.py'
        and os.path.splitext(f)[0].replace('_scraper', '') in SCRAPER_CONFIG
    ]

    # Sort scraper_files to ensure kleinanzeigen runs first
    scraper_files.sort(key=lambda x: 0 if 'kleinanzeigen' in x.lower() else 1)

    # Print configured scrapers that will be run
    print("Running scrapers with the following configurations:")
    for name, batch_size in SCRAPER_CONFIG.items():
        if any(name in f for f in scraper_files):
            print(f"- {name}: {batch_size}")

    # Initialize translation service
    translation_service = TranslationService()
    translation_service.start()

    # Run scrapers sequentially
    for scraper_path in scraper_files:
        site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
        stats = run_scraper(scraper_path, translation_service)
        scraper_results[site_name] = stats

    # Stop translation service and wait for completion
    translation_service.stop()

    # Call the upload service to upload translated JSONs to MongoDB
    print("Uploading translated JSONs to MongoDB...")
    subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "SERVICES", "upload_service.py")])
    print("Upload completed.")

    # Print final reports
    # print("\n=== Scraper Completeness Report ===")
    # for site, stats in scraper_results.items():
    #     if stats.total_ads > 0:
    #         completeness = (stats.complete_ads / stats.total_ads) * 100
    #         print(f"{site}: {completeness:.1f}% complete ads ({stats.complete_ads}/{stats.total_ads})")

    # print("\n=== New Ads Report ===")
    # for site, stats in scraper_results.items():
    #     if stats.total_ads > 0:
    #         if stats.category_stats:
    #             for category, cat_stats in stats.category_stats.items():
    #                 if cat_stats['total'] > 0:
    #                     new_percentage = (cat_stats['new'] / cat_stats['total']) * 100
    #                     print(f"{site} - {category}: {new_percentage:.1f}% new ads ({cat_stats['new']}/{cat_stats['total']})")
    #         else:
    #             new_percentage = (stats.new_ads / stats.total_ads) * 100
    #             print(f"{site}: {new_percentage:.1f}% new ads ({stats.new_ads}/{stats.total_ads})")

if __name__ == "__main__":
    main()