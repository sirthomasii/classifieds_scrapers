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

                    # Save the translated data
                    output_path = f'../next-frontend/public/jsons/{site_name}_ads.json'
                    print(f"Saving translated data to {output_path}")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

            except Exception as e:
                print(f"Error in translation worker: {e}")
            finally:
                self.translation_queue.task_done()