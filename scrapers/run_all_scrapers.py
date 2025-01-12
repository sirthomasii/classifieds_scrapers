import os
import importlib.util
import sys
from translation_service import TranslationService

def load_scraper(file_path):
    """Dynamically load a Python module from file path"""
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_scraper(scraper_path, max_pages, translation_service):
    """Run a single scraper with max_pages parameter"""
    try:
        site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
        print(f"\n=== Starting {site_name} scraper with max_pages={max_pages} ===")
        
        scraper = load_scraper(scraper_path)
        data = scraper.scrape(max_pages=max_pages)
        
        if not data:
            print(f"Warning: No data returned from {site_name} scraper")
            return
            
        # Skip translation for gumtree
        if 'gumtree' not in site_name.lower():
            translation_service.add_to_queue(site_name, data)
        print(f"=== Completed scraping for {site_name} ===\n")
        
    except Exception as e:
        print(f"Error in {site_name} scraper: {str(e)}")
        import traceback
        traceback.print_exc()

def main(max_pages = 30):
    # Get the directory containing the scrapers
    scrapers_dir = os.path.dirname(os.path.abspath(__file__))

    # Find all Python files containing "scraper" in the name, excluding leboncoin
    scraper_files = [
        os.path.join(scrapers_dir, f) 
        for f in os.listdir(scrapers_dir)
        if f.endswith('.py') 
        and 'scraper' in f.lower() 
        and 'leboncoin' not in f.lower()
        and f != 'run_all_scrapers.py'
    ]

    print(f"Found scrapers: {[os.path.basename(f) for f in scraper_files]}")
    print(f"Running with max_pages={max_pages}")

    # Initialize translation service
    translation_service = TranslationService()
    translation_service.start()

    # Run scrapers sequentially
    for scraper_path in scraper_files:
        run_scraper(scraper_path, max_pages, translation_service)

    # Stop translation service and wait for completion
    translation_service.stop()

if __name__ == "__main__":
    main()