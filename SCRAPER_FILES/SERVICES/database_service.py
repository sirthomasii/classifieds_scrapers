from pymongo import MongoClient

class DatabaseService:
    def __init__(self):
        self.client = MongoClient("mongodb+srv://sirthomasii:ujvkc8W1eeYP9axW@fleatronics-1.lppod.mongodb.net/?retryWrites=true&w=majority&appName=fleatronics-1")
        self.db = self.client['fleatronics']
        self.collection = self.db['listings']

    def check_duplicate_links(self, links, return_new_only=False):
        """Check which links already exist in the database"""
        if not links:
            return [] if return_new_only else []
        
        # Query MongoDB for existing links
        existing_links = set(
            doc['link'] for doc in self.collection.find(
                {'link': {'$in': links}}, 
                {'link': 1}
            )
        )
        
        if return_new_only:
            # Return list of new links (not in database)
            return [link for link in links if link not in existing_links]
        else:
            # Return list of duplicates (in database)
            return [link for link in links if link in existing_links]

    def close(self):
        """Close the MongoDB connection"""
        self.client.close() 