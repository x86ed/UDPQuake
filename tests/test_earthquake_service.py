import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from udpquake.earthquake_service import EarthquakeEvent, EarthquakeResponse, EarthquakeService


class TestEarthquakeEvent:
    """Test cases for EarthquakeEvent dataclass."""
    
    def test_from_feature_complete_data(self):
        """Test creating EarthquakeEvent from complete feature data."""
        feature = {
            "id": "ci40974079",
            "properties": {
                "mag": 1.65,
                "place": "5 km SE of Home Gardens, CA",
                "time": 1748036384780,
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci40974079",
                "type": "earthquake",
                "status": "automatic",
                "felt": 5
            },
            "geometry": {
                "coordinates": [-117.4886667, 33.843, 2.65]
            }
        }
        
        event = EarthquakeEvent.from_feature(feature)
        
        assert event.id == "ci40974079"
        assert event.magnitude == 1.65
        assert event.place == "5 km SE of Home Gardens, CA"
        assert event.latitude == 33.843
        assert event.longitude == -117.4886667
        assert event.depth == 2.65
        assert event.event_type == "earthquake"
        assert event.status == "automatic"
        assert event.felt_reports == 5
        assert isinstance(event.time, datetime)
        # Verify timezone-aware datetime
        assert event.time.tzinfo is not None
        assert event.time.tzinfo == timezone.utc
    
    def test_from_feature_missing_data(self):
        """Test creating EarthquakeEvent with missing optional data."""
        feature = {
            "id": "test123",
            "properties": {},
            "geometry": {
                "coordinates": [-118.0, 34.0, 10.0]
            }
        }
        
        event = EarthquakeEvent.from_feature(feature)
        
        assert event.id == "test123"
        assert event.magnitude == 0.0
        assert event.place == ""
        assert event.latitude == 34.0
        assert event.longitude == -118.0
        assert event.depth == 10.0
        assert event.felt_reports is None


    def test_from_feature_timezone_aware_datetime(self):
        """Test that EarthquakeEvent creates timezone-aware datetime objects."""
        feature = {
            "id": "test_tz",
            "properties": {
                "time": 1748036384780  # Unix timestamp in milliseconds
            },
            "geometry": {
                "coordinates": [-118.0, 34.0, 10.0]
            }
        }
        
        event = EarthquakeEvent.from_feature(feature)
        
        # Verify timezone-aware datetime
        assert event.time.tzinfo is not None
        assert event.time.tzinfo == timezone.utc
        
        # Verify correct conversion from milliseconds
        expected_time = datetime.fromtimestamp(1748036384780 / 1000, tz=timezone.utc)
        assert event.time == expected_time
    
    def test_from_feature_invalid_timestamp(self):
        """Test handling of invalid timestamp values."""
        feature = {
            "id": "test_invalid",
            "properties": {
                "time": 0  # Edge case: timestamp of 0
            },
            "geometry": {
                "coordinates": [-118.0, 34.0, 10.0]
            }
        }
        
        event = EarthquakeEvent.from_feature(feature)
        
        # Should handle timestamp of 0 gracefully
        expected_time = datetime.fromtimestamp(0, tz=timezone.utc)
        assert event.time == expected_time
        assert event.time.tzinfo == timezone.utc

    def test_datetime_timezone_handling(self):
        """Test that datetime objects are properly timezone-aware."""
        feature = {
            "id": "timezone_test",
            "properties": {
                "mag": 3.0,
                "place": "Timezone Test Location",
                "time": 1640995200000,  # 2022-01-01 00:00:00 UTC in milliseconds
                "type": "earthquake",
                "status": "reviewed"
            },
            "geometry": {
                "coordinates": [-118.0, 34.0, 10.0]
            }
        }
        
        event = EarthquakeEvent.from_feature(feature)
        
        # Verify the datetime is timezone-aware and in UTC
        assert event.time.tzinfo is not None
        assert event.time.tzinfo == timezone.utc
        
        # Verify the specific time conversion
        expected_time = datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert event.time == expected_time

    def test_datetime_microseconds_handling(self):
        """Test proper handling of datetime without microseconds."""
        # Test the datetime formatting used in the service
        now = datetime.now(timezone.utc)
        
        # Format without microseconds (as done in the service)
        formatted = now.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Should not contain microseconds
        assert '.' not in formatted
        
        # Should be parseable back to datetime
        parsed = datetime.fromisoformat(formatted.replace('+00:00', '+00:00'))
        
        # Should be very close to original (within 1 second due to microsecond truncation)
        time_diff = abs((now - parsed.replace(tzinfo=timezone.utc)).total_seconds())
        assert time_diff < 1.0


class TestEarthquakeResponse:
    """Test cases for EarthquakeResponse dataclass."""
    
    def test_from_geojson_complete(self):
        """Test creating EarthquakeResponse from complete GeoJSON data."""
        geojson_data = {
            "type": "FeatureCollection",
            "metadata": {
                "generated": 1748040061000,
                "count": 2,
                "status": 200
            },
            "features": [
                {
                    "id": "event1",
                    "properties": {
                        "mag": 3.5,
                        "place": "Test Location 1",
                        "time": 1748036384780,
                        "type": "earthquake",
                        "status": "reviewed"
                    },
                    "geometry": {"coordinates": [-118.0, 34.0, 5.0]}
                },
                {
                    "id": "event2",
                    "properties": {
                        "mag": 2.1,
                        "place": "Test Location 2",
                        "time": 1748036000000,
                        "type": "earthquake",
                        "status": "automatic"
                    },
                    "geometry": {"coordinates": [-117.0, 33.5, 8.2]}
                }
            ]
        }
        
        response = EarthquakeResponse.from_geojson(geojson_data)
        
        assert len(response.events) == 2
        assert response.count == 2
        assert isinstance(response.generated_time, datetime)
        assert response.metadata["status"] == 200
        
        # Check first event
        event1 = response.events[0]
        assert event1.id == "event1"
        assert event1.magnitude == 3.5
        assert event1.place == "Test Location 1"
    
    def test_from_geojson_empty(self):
        """Test creating EarthquakeResponse from empty data."""
        geojson_data = {
            "metadata": {"generated": 1748040061000},
            "features": []
        }
        
        response = EarthquakeResponse.from_geojson(geojson_data)
        
        assert len(response.events) == 0
        assert response.count == 0


class TestEarthquakeService:
    """Test cases for EarthquakeService class."""
    
    @patch.dict(os.environ, {
        'EARTHQUAKE_MIN_LATITUDE': '32.0',
        'EARTHQUAKE_MIN_LONGITUDE': '-119.0',
        'EARTHQUAKE_MAX_LATITUDE': '36.0',
        'EARTHQUAKE_MAX_LONGITUDE': '-115.0',
        'USGS_HOST': 'test.earthquake.usgs.gov'
    })
    def test_init_with_env_vars(self):
        """Test service initialization with environment variables."""
        service = EarthquakeService()
        
        assert service.min_latitude == 32.0
        assert service.min_longitude == -119.0
        assert service.max_latitude == 36.0
        assert service.max_longitude == -115.0
        assert service.base_host == 'test.earthquake.usgs.gov'
    
    def test_init_with_defaults(self):
        """Test service initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            service = EarthquakeService()
            
            assert service.min_latitude == 33.0
            assert service.min_longitude == -120.0
            assert service.max_latitude == 35.0
            assert service.max_longitude == -116.0
            assert service.base_host == 'earthquake.usgs.gov'
    
    def test_build_query_path_defaults(self):
        """Test building query path with default parameters."""
        service = EarthquakeService()
        path = service._build_query_path()
        
        expected_params = [
            "format=geojson",
            "minlatitude=33.0",
            "minlongitude=-120.0",
            "maxlatitude=35.0",
            "maxlongitude=-116.0"
        ]
        
        for param in expected_params:
            assert param in path
        
        # Verify URL encoding is used
        assert path.startswith("/fdsnws/event/1/query?")
        
    def test_build_query_path_url_encoding(self):
        """Test that URL encoding is properly applied to query parameters."""
        service = EarthquakeService()
        path = service._build_query_path(
            start_time="2024-01-01T00:00:00+00:00"
        )
        
        # URL encoding should handle special characters properly (colons and plus signs get encoded)
        assert "starttime=2024-01-01T00%3A00%3A00%2B00%3A00" in path
    
    def test_build_query_path_datetime_formatting(self):
        """Test that datetime parameters are properly formatted."""
        service = EarthquakeService()
        test_datetime = datetime(2024, 1, 15, 12, 30, 45, 123456, timezone.utc)
        formatted_time = test_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        path = service._build_query_path(start_time=formatted_time)
        
        # Verify the datetime format doesn't include microseconds and is URL encoded
        assert "2024-01-15T12%3A30%3A45%2B00%3A00" in path
        assert "123456" not in path  # Microseconds should be stripped
    
    def test_build_query_path_with_overrides(self):
        """Test building query path with parameter overrides."""
        service = EarthquakeService()
        path = service._build_query_path(
            min_magnitude=2.5,
            max_magnitude=6.0,
            limit=50,
            start_time="2024-01-01T00:00:00"
        )
        
        expected_params = [
            "minmagnitude=2.5",
            "maxmagnitude=6.0", 
            "limit=50",
            "starttime=2024-01-01T00%3A00%3A00"  # URL encoded version
        ]
        
        for param in expected_params:
            assert param in path
    
    @patch('http.client.HTTPSConnection')
    def test_fetch_earthquakes_success(self, mock_connection):
        """Test successful earthquake data fetch."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "metadata": {
                "generated": 1748040061000,
                "count": 1
            },
            "features": [
                {
                    "id": "test_event",
                    "properties": {
                        "mag": 4.2,
                        "place": "Test earthquake",
                        "time": 1748036384780,
                        "type": "earthquake",
                        "status": "reviewed",
                        "url": "https://test.url"
                    },
                    "geometry": {"coordinates": [-118.0, 34.0, 10.0]}
                }
            ]
        }).encode('utf-8')
        
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_connection.return_value = mock_conn
        
        service = EarthquakeService()
        result = service.fetch_earthquakes(min_magnitude=3.0)
        
        assert isinstance(result, EarthquakeResponse)
        assert len(result.events) == 1
        assert result.events[0].magnitude == 4.2
        assert result.events[0].place == "Test earthquake"
        
        # Verify connection was called correctly
        mock_connection.assert_called_once_with('earthquake.usgs.gov')
        mock_conn.request.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('http.client.HTTPSConnection')
    def test_fetch_earthquakes_http_error(self, mock_connection):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_connection.return_value = mock_conn
        
        service = EarthquakeService()
        
        with pytest.raises(ConnectionError, match="HTTP 404: Not Found"):
            service.fetch_earthquakes()
    
    @patch('http.client.HTTPSConnection')
    def test_fetch_earthquakes_connection_error(self, mock_connection):
        """Test handling of connection errors."""
        mock_connection.side_effect = Exception("Connection failed")
        
        service = EarthquakeService()
        
        with pytest.raises(RuntimeError, match="Unexpected error"):
            service.fetch_earthquakes()
    
    @patch('http.client.HTTPSConnection')
    def test_fetch_earthquakes_invalid_json(self, mock_connection):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"Invalid JSON"
        
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_connection.return_value = mock_conn
        
        service = EarthquakeService()
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            service.fetch_earthquakes()
    
    @patch.object(EarthquakeService, 'fetch_earthquakes')
    def test_get_recent_earthquakes(self, mock_fetch):
        """Test get_recent_earthquakes method."""
        mock_response = MagicMock()
        mock_fetch.return_value = mock_response
        
        service = EarthquakeService()
        result = service.get_recent_earthquakes(min_magnitude=3.5, limit=25)
        
        assert result == mock_response
        mock_fetch.assert_called_once_with(min_magnitude=3.5, limit=25)
    
    @patch.object(EarthquakeService, 'fetch_earthquakes')
    def test_get_earthquakes_in_region(self, mock_fetch):
        """Test get_earthquakes_in_region method."""
        mock_response = MagicMock()
        mock_fetch.return_value = mock_response
        
        service = EarthquakeService()
        result = service.get_earthquakes_in_region(
            min_lat=32.0, max_lat=36.0,
            min_lon=-120.0, max_lon=-116.0,
            min_magnitude=2.0
        )
        
        assert result == mock_response
        mock_fetch.assert_called_once_with(
            min_lat=32.0, max_lat=36.0,
            min_lon=-120.0, max_lon=-116.0,
            min_magnitude=2.0
        )


class TestIntegration:
    """Integration tests using real data format."""
    
    def test_real_data_format(self):
        """Test with actual USGS data format from your SoCal.json file."""
        real_feature = {
            "type": "Feature",
            "properties": {
                "mag": 1.65,
                "place": "5 km SE of Home Gardens, CA",
                "time": 1748036384780,
                "updated": 1748037048560,
                "tz": None,
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci40974079",
                "detail": "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=ci40974079&format=geojson",
                "felt": None,
                "cdi": None,
                "mmi": None,
                "alert": None,
                "status": "automatic",
                "tsunami": 0,
                "sig": 42,
                "net": "ci",
                "code": "40974079",
                "ids": ",ci40974079,",
                "sources": ",ci,",
                "types": ",focal-mechanism,nearby-cities,origin,phase-data,scitech-link,",
                "nst": 60,
                "dmin": 0.0444,
                "rms": 0.18,
                "gap": 30,
                "magType": "ml",
                "type": "earthquake",
                "title": "M 1.7 - 5 km SE of Home Gardens, CA"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-117.4886667, 33.843, 2.65]
            },
            "id": "ci40974079"
        }
        
        event = EarthquakeEvent.from_feature(real_feature)
        
        assert event.id == "ci40974079"
        assert event.magnitude == 1.65
        assert event.place == "5 km SE of Home Gardens, CA"
        assert event.longitude == -117.4886667
        assert event.latitude == 33.843
        assert event.depth == 2.65
        assert event.event_type == "earthquake"
        assert event.status == "automatic"
        assert event.felt_reports is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])