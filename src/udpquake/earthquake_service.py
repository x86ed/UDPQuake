import http.client
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode

@dataclass
class EarthquakeEvent:
    """Represents a single earthquake event."""
    id: str
    magnitude: float
    place: str
    time: datetime
    latitude: float
    longitude: float
    depth: float
    event_type: str
    status: str
    url: str
    felt_reports: Optional[int] = None
    
    @classmethod
    def from_feature(cls, feature: Dict) -> 'EarthquakeEvent':
        """Create an EarthquakeEvent from a GeoJSON feature."""
        properties = feature['properties']
        coordinates = feature['geometry']['coordinates']
        
        return cls(
            id=feature['id'],
            magnitude=properties.get('mag', 0.0),
            place=properties.get('place', ''),
            time=datetime.fromtimestamp(properties.get('time', 0) / 1000),
            longitude=coordinates[0],
            latitude=coordinates[1],
            depth=coordinates[2],
            event_type=properties.get('type', ''),
            status=properties.get('status', ''),
            url=properties.get('url', ''),
            felt_reports=properties.get('felt')
        )

@dataclass
class EarthquakeResponse:
    """Represents the complete earthquake data response."""
    events: List[EarthquakeEvent]
    metadata: Dict
    count: int
    generated_time: datetime
    
    @classmethod
    def from_geojson(cls, data: Dict) -> 'EarthquakeResponse':
        """Create an EarthquakeResponse from USGS GeoJSON data."""
        metadata = data.get('metadata', {})
        features = data.get('features', [])
        
        events = [EarthquakeEvent.from_feature(feature) for feature in features]
        
        return cls(
            events=events,
            metadata=metadata,
            count=metadata.get('count', len(events)),
            generated_time=datetime.fromtimestamp(metadata.get('generated', 0) / 1000)
        )

class EarthquakeService:
    """Service for fetching earthquake data from USGS."""
    
    def __init__(self):
        """Initialize the service with environment variables."""
        self.min_latitude = float(os.getenv('EARTHQUAKE_MIN_LATITUDE', '33.0'))
        self.min_longitude = float(os.getenv('EARTHQUAKE_MIN_LONGITUDE', '-120.0'))
        self.max_latitude = float(os.getenv('EARTHQUAKE_MAX_LATITUDE', '35.0'))
        self.max_longitude = float(os.getenv('EARTHQUAKE_MAX_LONGITUDE', '-116.0'))
        self.base_host = os.getenv('USGS_HOST', 'earthquake.usgs.gov')
        
    def _build_query_path(self, **kwargs) -> str:
        """Build the query path with parameters."""
        params = {
            'format': 'geojson',
            'minlatitude': kwargs.get('min_lat', self.min_latitude),
            'minlongitude': kwargs.get('min_lon', self.min_longitude),
            'maxlatitude': kwargs.get('max_lat', self.max_latitude),
            'maxlongitude': kwargs.get('max_lon', self.max_longitude),
        }
        
        # Add optional parameters
        if 'min_magnitude' in kwargs:
            params['minmagnitude'] = kwargs['min_magnitude']
        if 'max_magnitude' in kwargs:
            params['maxmagnitude'] = kwargs['max_magnitude']
        if 'start_time' in kwargs:
            params['starttime'] = kwargs['start_time']
        if 'end_time' in kwargs:
            params['endtime'] = kwargs['end_time']
        if 'limit' in kwargs:
            params['limit'] = kwargs['limit']
            
        query_string = urlencode(params)
        return f"/fdsnws/event/1/query?{query_string}"
    
    def fetch_earthquakes(self, **kwargs) -> EarthquakeResponse:
        """
        Fetch earthquake data from USGS.
        
        Args:
            **kwargs: Optional parameters to override defaults:
                - min_lat, max_lat, min_lon, max_lon: Coordinate bounds
                - min_magnitude, max_magnitude: Magnitude filters
                - start_time, end_time: Time range (ISO format)
                - limit: Maximum number of results
                
        Returns:
            EarthquakeResponse: Parsed earthquake data
            
        Raises:
            ConnectionError: If unable to connect to USGS
            ValueError: If response is invalid
        """
        try:
            conn = http.client.HTTPSConnection(self.base_host)
            path = self._build_query_path(**kwargs)
            
            conn.request("GET", path, "", {})
            response = conn.getresponse()
            
            if response.status != 200:
                raise ConnectionError(f"HTTP {response.status}: {response.reason}")
                
            data = response.read().decode("utf-8")
            conn.close()
            
            json_data = json.loads(data)
            return EarthquakeResponse.from_geojson(json_data)
            
        except ConnectionError:
            # Re-raise ConnectionError without wrapping it
            raise
        except json.JSONDecodeError as e:
            # Handle JSON decode errors specifically first (before ValueError)
            raise ValueError(f"Invalid JSON response: {e}")
        except ValueError:
            # Re-raise other ValueError instances without wrapping them  
            raise
        except http.client.HTTPException as e:
            raise ConnectionError(f"Failed to connect to USGS: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")
    
    def get_recent_earthquakes(self, min_magnitude: float = 2.0, limit: int = 100) -> EarthquakeResponse:
        """
        Get recent earthquakes above a minimum magnitude.
        
        Args:
            min_magnitude: Minimum earthquake magnitude
            limit: Maximum number of results
            
        Returns:
            EarthquakeResponse: Recent earthquake data
        """
        return self.fetch_earthquakes(min_magnitude=min_magnitude, limit=limit)
    
    def get_earthquakes_in_region(self, min_lat: float, max_lat: float, 
                                 min_lon: float, max_lon: float, **kwargs) -> EarthquakeResponse:
        """
        Get earthquakes in a specific geographic region.
        
        Args:
            min_lat, max_lat, min_lon, max_lon: Geographic bounds
            **kwargs: Additional query parameters
            
        Returns:
            EarthquakeResponse: Earthquake data for the region
        """
        return self.fetch_earthquakes(
            min_lat=min_lat, max_lat=max_lat,
            min_lon=min_lon, max_lon=max_lon,
            **kwargs
        )

if __name__ == "__main__":
    # Example usage
    service = EarthquakeService()
    
    try:
        # Get recent earthquakes with default bounds from environment
        earthquakes = service.get_recent_earthquakes(min_magnitude=1.0)
        
        print(f"Found {earthquakes.count} earthquakes")
        print(f"Data generated: {earthquakes.generated_time}")
        
        for eq in earthquakes.events[:5]:  # Show first 5
            print(f"M{eq.magnitude:.1f} - {eq.place} at {eq.time}")
            
    except Exception as e:
        print(f"Error: {e}")