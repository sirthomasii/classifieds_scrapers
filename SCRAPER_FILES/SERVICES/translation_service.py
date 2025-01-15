from deep_translator import GoogleTranslator
import json
import time
from queue import Queue
import threading
from pymongo import MongoClient
from datetime import datetime
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne

class TranslationService:
    def __init__(self):
        self.translation_queue = Queue()
        self.translator = GoogleTranslator(source='auto', target='en')
        self.translation_thread = None

    def start(self):
        """Start the translation worker thread"""
        self.translation_thread = threading.Thread(target=self._translation_worker)
        self.translation_thread.start()

    def stop(self):
        """Stop the translation worker thread"""
        self.translation_queue.put(None)  # Add poison pill
        if self.translation_thread:
            self.translation_queue.join()
            self.translation_thread.join()

    def add_to_queue(self, site_name, data):
        """Add data to translation queue"""
        self.translation_queue.put((site_name, data))

    def _split_into_chunks(self, titles, max_length=4500):
        """Split titles into chunks for translation"""
        chunks = []
        current_chunk = []
        current_length = 0
        separator_length = 5  # Length of " ||| "

        for title in titles:
            # Account for title length plus separator
            title_length = len(title) + separator_length
            
            # If adding this title would exceed max_length, start a new chunk
            if current_length + title_length > max_length:
                if current_chunk:  # Only append if there are items
                    chunks.append(current_chunk)
                current_chunk = [title]
                current_length = title_length
            else:
                current_chunk.append(title)
                current_length += title_length

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _translation_worker(self):
        """Worker that handles translations from the queue"""
        while True:
            try:
                # Get item from queue
                item = self.translation_queue.get()
                if item is None:  # Poison pill to stop the worker
                    break

                site_name, data = item
                print(f"Translating titles for {site_name}...")

                # Collect all titles with their references
                translations_needed = []
                title_refs = []  # Store direct references to title objects

                # Iterate through all pages and ads
                for page_data in data.values():
                    for ad in page_data:
                        if ad['title']['original']:
                            translations_needed.append(ad['title']['original'])
                            title_refs.append(ad['title'])  # Store reference to the title dict

                if translations_needed:
                    # Split titles into chunks and translate
                    chunks = self._split_into_chunks(translations_needed)
                    translated_titles = []

                    for chunk in chunks:
                        try:
                            # Use a unique separator that won't appear in titles
                            separator = " @# "
                            chunk_text = separator.join(chunk)
                            translated_chunk = self.translator.translate(chunk_text)
                            
                            # Split back using the unique separator
                            translated_titles.extend(translated_chunk.split(separator))
                        except Exception as e:
                            print(f"Translation error for chunk: {e}")
                            translated_titles.extend(chunk)

                    # Update original data structure using direct references
                    for title_obj, translation in zip(title_refs, translated_titles):
                        title_obj['english'] = translation

                    # Handle the translated data
                    self._handle_translated_data(site_name, data)

            except Exception as e:
                print(f"Error in translation worker: {e}")
            finally:
                self.translation_queue.task_done()

    def _handle_translated_data(self, site_name, translated_data):
        """Handle the translated data by uploading it to MongoDB"""
        self._upload_to_mongo(site_name, translated_data)

    def _upload_to_mongo(self, site_name, data):
        """Upload translated data to MongoDB with duplicate prevention"""
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
                        # Create filter for upsert
                        filter_doc = {
                            "link": item['link'],
                            "source": site_name
                        }
                        # Add timestamp for tracking updates
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

        except BulkWriteError as bwe:
            print(f"Some upserts failed: {bwe.details}")
        except Exception as e:
            print(f"Error uploading to MongoDB: {e}")
        finally:
            client.close()

def translate_listings(data, site_name):
    """Translate listings from a specific marketplace"""
    print(f"\nTranslating listings from {site_name}...")
    
    # Skip translation for English sites
    if site_name.lower() == 'gumtree':
        print("Skipping translation for Gumtree (already in English)")
        return data

    translator = GoogleTranslator(source='auto', target='en')
    
    # Collect all titles for batch translation
    all_titles = []
    title_map = {}  # To map translated titles back to their ads

    for page_num in data:
        for ad in data[page_num]:
            if ad['title']['original']:
                all_titles.append(ad['title']['original'])
                title_map[ad['title']['original']] = ad

    # Function to split titles into chunks
    def split_into_chunks(titles, max_length=5000):
        chunks = []
        current_chunk = []
        current_length = 0

        for title in titles:
            title_length = len(title) + 2  # Account for ". " separator
            if current_length + title_length > max_length:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0
            current_chunk.append(title)
            current_length += title_length

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # Translate titles in chunks
    try:
        chunks = split_into_chunks(all_titles)
        translated_titles = []

        for chunk in chunks:
            single_string = ". ".join(chunk)
            translated_chunk = translator.translate(single_string)
            translated_titles.extend(translated_chunk.split(". "))
            time.sleep(1)  # Be nice to the translation service

        # Map translations back to listings
        for original, translated in zip(all_titles, translated_titles[:len(all_titles)]):
            title_map[original]['title']['english'] = translated

        print(f"Successfully translated {len(translated_titles)} titles from {site_name}")
        return data

    except Exception as e:
        print(f"Translation error for {site_name}: {e}")
        # Return original data if translation fails
        return data