import os
import importlib.util
import sys
from .translation_service import TranslationService
from .upload_service import upload_data_to_mongo
from .database_service import DatabaseService
from .cleanup_service import CleanupService
import subprocess
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Define num pages per batch
SCRAPER_CONFIG = {
    'kleinanzeigen': 4,
    'blocket': 2,
    'gumtree': 2,
    'tori': 3,
    'olx': 2,
    'ricardo': 1,
    'dba': 1
}

class ScraperService:
    def __init__(self):
        self.translation_service = TranslationService()
        self.cleanup_service = CleanupService()
        self.scraper_results = {}

    def check_collection_exists(self):
        """Check if the fleatronics collection exists and has documents"""
        load_dotenv()
        mongo_uri = os.getenv('MONGODB_URI')
        if not mongo_uri:
            raise ValueError("MONGODB_URI environment variable not set")
            
        client = MongoClient(mongo_uri)
        db = client['fleatronics']
        
        try:
            collection_exists = 'listings' in db.list_collection_names()
            has_documents = db.listings.count_documents({}) > 0 if collection_exists else False
            return collection_exists and has_documents
        finally:
            client.close()

    def get_adjusted_config(self):
        """Get scraper config with adjusted batch sizes if needed"""
        is_first_run = not self.check_collection_exists()
        
        if is_first_run:
            print("\nFirst run detected - increasing batch sizes for initial data collection")
            return {site: pages * 20 for site, pages in SCRAPER_CONFIG.items()}
        
        return SCRAPER_CONFIG

    def load_scraper(self, file_path):
        """Dynamically load a Python module from file path"""
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def run_single_scraper(self, scraper_path):
        """Run a single scraper"""
        stats = ScraperStats()
        try:
            site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
            
            current_config = self.get_adjusted_config()
            batch_size = current_config.get(site_name, 2)
            
            print(f"\n=== Starting {site_name} scraper with batch_size={batch_size} ===")
            
            scraper = self.load_scraper(scraper_path)
            all_data = scraper.scrape(max_pages=batch_size)
            
            stats.data = all_data
            
            if not all_data:
                print(f"Warning: No data returned from {site_name} scraper")
                return stats
                
            stats.total_ads, stats.complete_ads = calculate_completeness(all_data)
            
            if 'gumtree' in site_name.lower():
                stats.total_ads, stats.new_ads, stats.complete_ads, stats.category_stats = upload_data_to_mongo(site_name, all_data)
            else:
                self.translation_service.add_to_queue(site_name, all_data)
                stats.total_ads = sum(len(page) for page in all_data.values())
                stats.complete_ads = sum(1 for page in all_data.values() 
                                        for item in page 
                                        if item.get('link') and 
                                           item.get('main_image') and 
                                           item.get('title', {}).get('original'))
                
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

    def run_all_scrapers(self):
        """Run all scrapers sequentially"""
        try:
            # Run cleanup first
            cleanup_stats = self.cleanup_service.cleanup_old_listings()
            print(f"\nCleanup completed: {cleanup_stats['listings_deleted']} old listings removed")
            
            current_config = self.get_adjusted_config()
            
            # Get scrapers directory path
            scrapers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SCRAPERS')

            # Find all valid scraper files
            scraper_files = [
                os.path.join(scrapers_dir, f) 
                for f in os.listdir(scrapers_dir)
                if f.endswith('.py') 
                and 'scraper' in f.lower() 
                and 'leboncoin' not in f.lower()
                and f != '__init__.py'
                and os.path.splitext(f)[0].replace('_scraper', '') in current_config
            ]

            # Sort to ensure kleinanzeigen runs first, randomize the rest
            import random
            scraper_files.sort(key=lambda x: -1 if 'kleinanzeigen' in x.lower() else random.random() + 1)

            # Print configurations
            print("Running scrapers with the following configurations:")
            for name, batch_size in current_config.items():
                if any(name in f for f in scraper_files):
                    print(f"- {name}: {batch_size}")

            # Start translation service
            self.translation_service.start()

            # Run each scraper
            for scraper_path in scraper_files:
                site_name = os.path.basename(scraper_path).replace('_scraper.py', '')
                stats = self.run_single_scraper(scraper_path)
                self.scraper_results[site_name] = stats

            # Stop translation service
            self.translation_service.stop()

            # Upload translated data
            print("Uploading translated JSONs to MongoDB...")
            subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_service.py")])
            print("Upload completed.")

        finally:
            self.cleanup_service.close()

class ScraperStats:
    def __init__(self):
        self.total_ads = 0
        self.complete_ads = 0
        self.new_ads = 0
        self.data = None
        self.category_stats = {}

def calculate_completeness(data):
    """Calculate percentage of complete ads"""
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

def run_scrapers():
    """Main entry point for running scrapers"""
    service = ScraperService()
    service.run_all_scrapers()

if __name__ == "__main__":
    run_scrapers() 