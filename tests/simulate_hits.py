import sys
import os
import json
import random
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tops_service import TopsService
from config.settings import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_hits():
    print("🚀 Starting simulation of hits...")
    
    tops_service = TopsService()
    listings_file = os.path.join(config.output_dir, "tops", "new_perspective_listings.json")
    
    if not os.path.exists(listings_file):
        print(f"❌ File not found: {listings_file}")
        return

    with open(listings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get("listings", {})
    
    # If no listings found, generate mock ones for testing
    if not listings:
        print("⚠️ No listings found in file. Generating 20 mock listings for simulation...")
        listings = {}
        for i in range(20):
            lid = f"mock_listing_{i}"
            start_date = (datetime.now() - timedelta(days=65)).strftime("%d.%m.%Y_%H.%M")
            listings[lid] = {
                start_date: {
                    "listing_id": lid,
                    "url": f"https://www.etsy.com/listing/{lid}",
                    "views": random.randint(10, 100),
                    "num_favorers": random.randint(0, 10),
                    "est_reviews": random.randint(0, 5),
                    "listing_age_in_months": 0
                }
            }
    
    # Pick 15-20 random listings
    count = min(len(listings), 20)
    selected_ids = random.sample(list(listings.keys()), count)
    print(f"📋 Selected {len(selected_ids)} listings for simulation.")
    
    # Prepare future date
    # We need a date that is definitely > 60 days from the start date of these listings
    # Let's find the earliest start date to be safe, or just add 65 days to today
    # But wait, the logic compares current_date vs first_snapshot_date.
    # So we need to pass a "future" current_date to the check function.
    
    # Let's modify the listings in memory to have a "hit" snapshot
    modified_data = {"listings": {}}
    
    # We will use a fixed future date for the simulation check
    future_date = datetime.now() + timedelta(days=65)
    future_date_str = future_date.strftime("%d.%m.%Y_%H.%M")
    
    for lid in selected_ids:
        snapshots = listings[lid]
        if not snapshots:
            continue
            
        timestamps = sorted(snapshots.keys())
        first_ts = timestamps[0]
        first_data = snapshots[first_ts]
        
        # Calculate start date
        try:
            first_dt = datetime.strptime(first_ts, "%d.%m.%Y_%H.%M")
        except:
            continue
            
        # Ensure the first date is old enough relative to our future date
        # (It will be, since we added 65 days to NOW, and first_dt is <= NOW)
        
        # Create a "hit" snapshot at future_date
        # Views > 1200 growth, Likes >= 40 growth
        start_views = first_data.get("views", 0)
        start_likes = first_data.get("num_favorers", 0)
        
        target_views = start_views + random.randint(1300, 2000)
        target_likes = start_likes + random.randint(50, 100)
        
        hit_snapshot = first_data.copy()
        hit_snapshot["views"] = target_views
        hit_snapshot["num_favorers"] = target_likes
        hit_snapshot["est_reviews"] = first_data.get("est_reviews", 0) + random.randint(1, 10)
        
        # Add to modified data
        modified_data["listings"][lid] = snapshots.copy()
        modified_data["listings"][lid][future_date_str] = hit_snapshot
        
        print(f"✨ Prepared hit for {lid}: Views {start_views}->{target_views}, Likes {start_likes}->{target_likes}")

    print(f"\n📅 Running check with simulated date: {future_date_str}")
    
    # Run the check
    # Note: This will call _send_tops_to_sheets internally if hits are found
    potential_tops = tops_service._check_listings_age(modified_data, future_date_str)
    
    print(f"\n✅ Simulation complete.")
    print(f"🔥 Found {len(potential_tops)} potential tops (should match selected count).")
    print("📊 Check Google Sheets 'Top Listings' tab for new rows.")

if __name__ == "__main__":
    simulate_hits()
