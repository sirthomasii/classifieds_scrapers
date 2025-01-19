from deep_translator import GoogleTranslator
import json
import time
from queue import Queue
import threading
from pymongo import MongoClient
from datetime import datetime
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from .upload_service import upload_data_to_mongo

class TranslationService:
    def __init__(self):
        self.translation_queue = Queue()
        self.translator = GoogleTranslator(source='auto', target='en')
        self.translation_thread = None
        self.results = {}  # Initialize results dictionary

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
        # Initialize results for this site
        self.results[site_name] = {}
        # Initialize category stats from the data
        for page in data.values():
            for item in page:
                category = item.get('category', 'uncategorized')
                if category not in self.results[site_name]:
                    self.results[site_name][category] = {'total': 0, 'new': 0, 'complete': 0}
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
                item = self.translation_queue.get()
                if item is None:  # Poison pill
                    break

                site_name, data = item
                
                # Use a very unique separator that won't appear in titles
                SEPARATOR = "§‡†★"  # Combination of rare Unicode characters
                
                # Collect all titles with their references
                translations_needed = []
                title_refs = []

                # Iterate through all pages and ads
                for page_data in data.values():
                    for ad in page_data:
                        if ad['title']['original']:
                            translations_needed.append(ad['title']['original'].strip())
                            title_refs.append(ad['title'])

                if translations_needed:
                    chunks = self._split_into_chunks(translations_needed)
                    translated_titles = []

                    for chunk in chunks:
                        try:
                            chunk_text = SEPARATOR.join(chunk)
                            translated_chunk = self.translator.translate(chunk_text)
                            translated_titles.extend(translated_chunk.split(SEPARATOR))
                            time.sleep(1)  # Rate limiting
                        except Exception as e:
                            print(f"Translation error for chunk: {e}")
                            translated_titles.extend(chunk)  # Use original on error

                    # Update original data structure
                    for title_obj, translation in zip(title_refs, translated_titles):
                        title_obj['english'] = translation.strip()

                    # Handle the translated data
                    _, new_ads, _, category_stats = upload_data_to_mongo(site_name, data)
                    
                    # Update category stats
                    for category, stats in category_stats.items():
                        self.results[site_name][category] = stats

            except Exception as e:
                print(f"Error in translation worker: {e}")
            finally:
                self.translation_queue.task_done()

    def _handle_translated_data(self, site_name, data):
        """Handle the translated data - either save to file or upload to MongoDB"""
        upload_data_to_mongo(site_name, data)

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