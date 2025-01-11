from deep_translator import GoogleTranslator
import json
import time
from queue import Queue
import threading

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

    def _split_into_chunks(self, titles, max_length=5000):
        """Split titles into chunks for translation"""
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

                # Collect all titles and their references
                all_titles = []
                title_map = {}  # Maps original titles to their locations in data

                # Iterate through all pages and ads
                for page_num in data:
                    for ad in data[page_num]:
                        if ad['title']['original']:
                            original_title = ad['title']['original']
                            all_titles.append(original_title)
                            title_map[original_title] = ad['title']  # Store reference to title dict

                if all_titles:
                    # Split titles into chunks and translate
                    chunks = self._split_into_chunks(all_titles)
                    for chunk in chunks:
                        try:
                            # Join titles with separator and translate
                            chunk_text = ". ".join(chunk)
                            translated_chunk = self.translator.translate(chunk_text)
                            
                            # Split back into individual titles
                            translated_titles = translated_chunk.split(". ")
                            
                            # Update original ads with translations
                            for original, translated in zip(chunk, translated_titles):
                                if original in title_map:
                                    title_map[original]['english'] = translated
                        except Exception as e:
                            print(f"Translation error for chunk: {e}")
                            # If translation fails, use original text
                            for original in chunk:
                                if original in title_map:
                                    title_map[original]['english'] = original

                    # Save the translated data
                    output_path = f'../next-frontend/public/jsons/{site_name}_ads.json'
                    print(f"Saving translated data to {output_path}")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

            except Exception as e:
                print(f"Error in translation worker: {e}")
            finally:
                self.translation_queue.task_done()