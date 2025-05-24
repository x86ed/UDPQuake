import os
from earthquake_service import EarthquakeService
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize the earthquake service
        earthquake_service = EarthquakeService()
        
        # Get earthquakes from the last hour with magnitude > 2.0
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=one_hour_ago,
            limit=50
        )
        
        print(f"UDPQuake - Earthquake Monitor")
        print(f"Found {earthquakes.count} earthquakes in the last hour")
        print(f"Search bounds: {earthquake_service.min_latitude},{earthquake_service.min_longitude} to {earthquake_service.max_latitude},{earthquake_service.max_longitude}")
        print("-" * 60)
        
        for earthquake in earthquakes.events:
            print(f"M{earthquake.magnitude:.1f} | {earthquake.place}")
            print(f"  Time: {earthquake.time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  Location: {earthquake.latitude:.3f}, {earthquake.longitude:.3f}")
            print(f"  Depth: {earthquake.depth:.1f}km | Status: {earthquake.status}")
            print(f"  URL: {earthquake.url}")
            print()
            
        # Example: Filter for significant earthquakes (magnitude > 4.0)
        significant = [eq for eq in earthquakes.events if eq.magnitude >= 4.0]
        if significant:
            print(f"⚠️  {len(significant)} significant earthquake(s) detected!")
            for eq in significant:
                print(f"  🚨 M{eq.magnitude:.1f} - {eq.place}")
        
    except Exception as e:
        print(f"Error fetching earthquake data: {e}")

if __name__ == "__main__":
    main()
