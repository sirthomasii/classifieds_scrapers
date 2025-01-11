import subprocess
import sys
import os
from datetime import datetime

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_scraper(script_name):
    """Run a scraper script and return success/failure status"""
    print(f"\n{'='*50}")
    print(f"Running {script_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Check if the script completed successfully
        if result.returncode == 0:
            # Check if the expected output file was created
            site_name = script_name.split('_')[0].split('/')[-1]
            output_file = f'../next-frontend/public/jsons/{site_name}_ads.json'
            
            if os.path.exists(output_file):
                return True, "Success"
            else:
                return False, f"Output file {output_file} not created"
        else:
            return False, f"Script failed with error:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 minutes"
    except Exception as e:
        return False, f"Failed to run script: {str(e)}"

def main():
    # List of scrapers to run
    scrapers = [
        "scrapers/blocket_scraper.py",
        "scrapers/gumtree_scraper.py",
        "scrapers/kleinanzeigen_scraper.py"
    ]
    
    # Store results
    results = {}
    
    # Run each scraper
    for scraper in scrapers:
        success, message = run_scraper(scraper)
        results[scraper] = {
            'status': 'Success' if success else 'Failed',
            'message': message
        }
    
    # Print summary
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    
    for scraper, result in results.items():
        print(f"\n{os.path.basename(scraper)}:")
        print(f"Status: {result['status']}")
        if result['status'] == 'Failed':
            print(f"Error: {result['message']}")

if __name__ == "__main__":
    main()