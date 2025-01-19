from pymongo import MongoClient
from datetime import datetime, timedelta
from os import getenv, makedirs, path
from dotenv import load_dotenv
import logging
import time

class CleanupService:
    def __init__(self):
        # Ensure logs directory exists
        logs_dir = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'logs')
        makedirs(logs_dir, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(path.join(logs_dir, 'cleanup.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Connect to MongoDB
        load_dotenv()
        mongo_uri = getenv('MONGODB_URI')
        if not mongo_uri:
            raise ValueError("MONGODB_URI environment variable not set")
            
        self.client = MongoClient(mongo_uri)
        self.db = self.client['fleatronics']
        self.collection = self.db['listings']

    def cleanup_old_listings(self, months_old=2):
        """Delete listings older than specified months"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30 * months_old)
            
            # Find listings to delete
            query = {
                "scraped_at": {
                    "$lt": cutoff_date.isoformat()
                }
            }
            
            # Get count before deletion for logging
            old_count = self.collection.count_documents(query)
            
            # Delete old listings
            result = self.collection.delete_many(query)
            
            # Log the results
            self.logger.info(
                f"Cleanup completed: {result.deleted_count} listings older than "
                f"{months_old} months deleted ({cutoff_date.isoformat()})"
            )
            
            # Return statistics
            return {
                'cutoff_date': cutoff_date.isoformat(),
                'listings_found': old_count,
                'listings_deleted': result.deleted_count
            }
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise
        
    def close(self):
        """Close the MongoDB connection"""
        self.client.close()

def run_cleanup_service():
    """Run the cleanup service as a standalone process"""
    cleanup_service = None
    try:
        cleanup_service = CleanupService()
        
        while True:
            try:
                # Run cleanup
                stats = cleanup_service.cleanup_old_listings(months_old=2)
                
                # Log results
                cleanup_service.logger.info(
                    f"Cleanup run completed:\n"
                    f"- Cutoff date: {stats['cutoff_date']}\n"
                    f"- Listings found: {stats['listings_found']}\n"
                    f"- Listings deleted: {stats['listings_deleted']}"
                )
                
                # Wait 24 hours before next cleanup
                time.sleep(24 * 60 * 60)
                
            except Exception as e:
                cleanup_service.logger.error(f"Error during cleanup cycle: {str(e)}")
                # Wait 1 hour before retry on error
                time.sleep(60 * 60)
                
    except Exception as e:
        if cleanup_service and cleanup_service.logger:
            cleanup_service.logger.error(f"Fatal error in cleanup service: {str(e)}")
        else:
            print(f"Fatal error in cleanup service: {str(e)}")
        
    finally:
        if cleanup_service:
            cleanup_service.close()

if __name__ == "__main__":
    run_cleanup_service() 