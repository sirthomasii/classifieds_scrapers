from pymongo import MongoClient

def upload_data_to_mongo(site_name, data):
    """Upload translated data to MongoDB"""
    client = MongoClient("mongodb+srv://sirthomasii:ujvkc8W1eeYP9axW@fleatronics-1.lppod.mongodb.net/?retryWrites=true&w=majority&appName=fleatronics-1")
    db = client['fleatronics']
    collection = db['listings']

    all_listings = [item for page in data.values() for item in page]
    if all_listings:
        collection.insert_many(all_listings)
        print(f"Successfully inserted {len(all_listings)} listings from {site_name} into MongoDB")

# This script is now a module and doesn't need a main function