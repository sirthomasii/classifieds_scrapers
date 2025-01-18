from pymongo import MongoClient
from datetime import datetime

def upload_data_to_mongo(site_name, data):
    """Upload translated data to MongoDB"""
    # Initialize counters
    total_ads = 0
    new_ads = 0
    complete_ads = 0

    # Track stats by category
    category_stats = {}

    if not data:
        return total_ads, new_ads, complete_ads

    client = MongoClient("mongodb+srv://sirthomasii:ujvkc8W1eeYP9axW@fleatronics-1.lppod.mongodb.net/?retryWrites=true&w=majority&appName=fleatronics-1")
    db = client['fleatronics']
    collection = db['listings']

    # Create a unique compound index
    collection.create_index([
        ("link", 1),
        ("source", 1)
    ], unique=True)

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

    # Print stats for each category
    # for category, stats in category_stats.items():
    #     new_percentage = (stats['new'] / stats['total'] * 100) if stats['total'] > 0 else 0
    #     print(f"{site_name} - {category}: {new_percentage:.1f}% new ads ({stats['new']}/{stats['total']})")

    client.close()
    return total_ads, new_ads, complete_ads, category_stats

# This script is now a module and doesn't need a main function