import time
import signal
from .earthquake_service import EarthquakeService
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from mudp import (send_nodeinfo)

from .mudp import send_quake, setup_node

# Global variable to control the main loop
running = True

def signal_handler(sig, frame):
    """Handle keyboard interrupts gracefully"""
    global running
    print("\nShutting down UDPQuake...")
    running = False

def main():
    """Main application entry point."""
    global running
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load environment variables
    load_dotenv()
    
    print(f"UDPQuake - Earthquake Monitor")
    print(f"Fetching earthquake data every minute. Press Ctrl+C to exit.")
    print("-" * 60) # Allow some time for node info to propagate
    
    # Initialize the earthquake service
    earthquake_service = EarthquakeService()
    
    # Track processed earthquake IDs to avoid duplicates
    processed_ids = set()
    
    # Flag to track if this is the first run
    first_run = True
    
    while running:
        try:
            # On first run, check last 72 hours; subsequent runs check last hour
            if first_run:
                time_ago = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
                time_description = "72 hours"
                first_run = False
            else:
                time_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
                time_description = "last hour"
            
            earthquakes = earthquake_service.fetch_earthquakes(
                min_magnitude=2.0,
                start_time=time_ago,
                limit=50
            )
            
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found {earthquakes.count} earthquakes in the {time_description}")
            print(f"Search bounds: {earthquake_service.min_latitude},{earthquake_service.min_longitude} to {earthquake_service.max_latitude},{earthquake_service.max_longitude}")
            
            # Process only new earthquakes
            new_quakes = [eq for eq in earthquakes.events if eq.id not in processed_ids]
            if new_quakes:
                print(f"New earthquakes detected: {len(new_quakes)}")
                
                for earthquake in new_quakes:
                    # Add to processed set
                    processed_ids.add(earthquake.id)
                    
                    print(f"M{earthquake.magnitude:.1f} | {earthquake.place}")
                    print(f"  Time: {earthquake.time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    print(f"  Location: {earthquake.latitude:.3f}, {earthquake.longitude:.3f}")
                    print(f"  Depth: {earthquake.depth:.1f}km | Status: {earthquake.status}")
                    print(f"  URL: {earthquake.url}")
                    print()
                    
                    send_quake(
                        mag=earthquake.magnitude,
                        place=earthquake.place,
                        when=int(earthquake.time.timestamp() * 1000),  # Convert to milliseconds
                        latitude=earthquake.latitude,
                        longitude=earthquake.longitude,
                        depth=earthquake.depth
                    )
                    
                # Example: Filter for significant earthquakes (magnitude > 4.0)
                significant = [eq for eq in new_quakes if eq.magnitude >= 4.0]
                if significant:
                    print(f"⚠️  {len(significant)} significant earthquake(s) detected!")
                    for eq in significant:
                        print(f"  🚨 M{eq.magnitude:.1f} - {eq.place}")
            else:
                print("No new earthquakes detected.")
            
            # Clean up old IDs (keep only IDs from the last 2 hours to manage memory)
            two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
            processed_ids = {eq.id for eq in earthquakes.events 
                            if eq.time > two_hours_ago}
                
        except Exception as e:
            print(f"Error fetching earthquake data: {e}")
        
        # Wait for 60 seconds before next check
        for _ in range(60):
            if not running:
                break
            time.sleep(1)  # Check every second if we need to exit

if __name__ == "__main__":
    main()
