import json
import os
import sys
from datetime import datetime
import time
from run_all_scrapers import main as run_scrapers

def parse_scraper_output(output):
    """Parse scraper output for completeness and new ads data"""
    completeness_data = {}
    new_ads_data = {}
    in_new_ads_section = False
    in_completeness_section = False
    
    # Debug: Print raw output
    print("\nDEBUG RAW OUTPUT:")
    print("----------------")
    print(output)
    print("----------------\n")
    
    for line in output.split('\n'):
        # Parse Completeness Report
        if "=== Scraper Completeness Report ===" in line:
            in_completeness_section = True
            in_new_ads_section = False
            continue
        if in_completeness_section and line.strip():
            if line.startswith('==='):
                in_completeness_section = False
                continue
            parts = line.split(':')
            if len(parts) == 2:
                site = parts[0].strip()
                stats = parts[1].strip()
                completeness_data[site] = stats
        
        # Parse New Ads Report
        if "=== New Ads Report ===" in line:
            in_new_ads_section = True
            in_completeness_section = False
            print("DEBUG: Found New Ads section")
            continue
        if in_new_ads_section and line.strip():
            if line.startswith('==='):  # Only skip section markers
                in_new_ads_section = False
                break
            parts = line.split(':')
            if len(parts) == 2:
                site = parts[0].strip()
                stats = parts[1].strip()
                new_ads_data[site] = stats
                print(f"DEBUG: Added new ads entry - {site}: {stats}")
        
    if not new_ads_data:
        print("\nWarning: No new ads data was captured in this run")
        print("DEBUG: in_new_ads_section =", in_new_ads_section)
    
    return completeness_data, new_ads_data

def main():
    """Run scrapers periodically and log results"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Save log file in logs directory
    log_file = os.path.join(logs_dir, "scraper_stats.json")
    
    # Load existing log if it exists and is not empty
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            log_data = json.loads(content) if content.strip() else []
    except (json.JSONDecodeError, FileNotFoundError):
        log_data = []
    
    while True:
        try:
            print(f"\n=== Starting scraper run at {datetime.now().isoformat()} ===")
            
            # Reset the upload service stats before running scrapers
            from SERVICES.upload_service import reset_stats
            reset_stats()
            
            # Run scrapers
            run_scrapers()
            
            # Get stats from upload service
            from SERVICES.upload_service import get_last_run_stats
            completeness_data, new_ads_data = get_last_run_stats()
            
            if not new_ads_data:
                print("\nWarning: No new ads data was parsed!")
            else:
                # Print the actual stats from the upload service
                print("\n=== Scraper Completeness Report ===")
                for site, stats in completeness_data.items():
                    print(f"{site}: {stats}")

                print("\n=== New Ads Report ===")
                for site, stats in new_ads_data.items():
                    print(f"{site}: {stats}")
            
            # Add to log with timestamp
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'completeness': completeness_data,
                'new_ads': new_ads_data
            }
            log_data.append(log_entry)
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            print(f"Logged data at {log_entry['timestamp']}")
            print("Waiting 2 minutes until next run...")
            
            # Wait 30 minutes
            time.sleep(120)
            
        except Exception as e:
            print(f"Error in scraper run: {e}")
            time.sleep(60)  # Wait a minute before retrying if there's an error

if __name__ == "__main__":
    main()