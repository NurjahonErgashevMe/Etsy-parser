import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tops_service import TopsService
from services.google_sheets_service import GoogleSheetsService
from config.settings import config

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_export():
    print("🚀 Testing Google Sheets export...")
    
    tops_file = os.path.join(config.output_dir, "tops", "top-listings.json")
    if not os.path.exists(tops_file):
        print(f"❌ File not found: {tops_file}")
        return

    with open(tops_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get("listings", {})
    if not listings:
        print("❌ No listings found in top-listings.json")
        return
    
    print(f"📋 Found {len(listings)} top listings. Sending to Sheets...")
    
    sheets_service = GoogleSheetsService(config)
    spreadsheet_id = config.google_sheets_spreadsheet_id
    
    if not spreadsheet_id:
        print("❌ No spreadsheet ID in config")
        return

    sheets_service.add_top_listings_to_sheets(spreadsheet_id, listings)
    print("✅ Export complete.")

if __name__ == "__main__":
    test_export()
