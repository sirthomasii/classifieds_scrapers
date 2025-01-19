from pymongo import MongoClient
from datetime import datetime
from os import getenv
from dotenv import load_dotenv

# Store last run stats
_last_run_stats = {'completeness': {}, 'new_ads': {}}

def reset_stats():
    """Reset the statistics for a new scraper run"""
    global _last_run_stats
    _last_run_stats = {'completeness': {}, 'new_ads': {}}

def upload_data_to_mongo(site_name, data):
    """Upload translated data to MongoDB"""
    load_dotenv()
    mongo_uri = getenv('MONGODB_URI')
    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable not set")
        
    client = MongoClient(mongo_uri)
    db = client['fleatronics']
    collection = db['listings']

    # Create a unique compound index
    collection.create_index([
        ("link", 1),
        ("source", 1)
    ], unique=True)

    total_ads = 0
    new_ads = 0
    complete_ads = 0

    # Track stats by category
    category_stats = {}

    if not data:
        return total_ads, new_ads, complete_ads

    all_listings = [item for page in data.values() for item in page]
    for item in all_listings:
        total_ads += 1
        category = item.get('category', 'uncategorized')

        # Initialize category stats if not exists
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'new': 0, 'complete': 0}
        category_stats[category]['total'] += 1

        if (item.get('link') and 
            item.get('main_image') and 
            item.get('title', {}).get('original')):
            complete_ads += 1
            category_stats[category]['complete'] += 1

        try:
            if not collection.find_one({"link": item["link"], "source": site_name}):
                item["source"] = site_name
                item["scraped_at"] = datetime.now().isoformat()
                collection.insert_one(item)
                new_ads += 1
                category_stats[category]['new'] += 1
        except Exception as e:
            print(f"Error inserting document: {e}")

    # Store stats for this run
    _last_run_stats['completeness'][site_name] = f"{(complete_ads / total_ads * 100):.1f}% complete ads ({complete_ads}/{total_ads})"
    for category, stats in category_stats.items():
        site_category = f"{site_name} - {category}"
        new_percentage = (stats['new'] / stats['total'] * 100) if stats['total'] > 0 else 0
        _last_run_stats['new_ads'][site_category] = f"{new_percentage:.1f}% new ads ({stats['new']}/{stats['total']})"

    client.close()
    return total_ads, new_ads, complete_ads, category_stats

def get_last_run_stats():
    """Get stats from the last run"""
    return _last_run_stats['completeness'], _last_run_stats['new_ads']

# This script is now a module and doesn't need a main function