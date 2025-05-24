import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from io import StringIO

# Add the UDPQuake directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'UDPQuake'))

from main import main
from earthquake_service import EarthquakeEvent, EarthquakeResponse


class TestMain:
    """Test cases for main.py functionality."""
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_success_with_earthquakes(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function with successful earthquake data retrieval."""
        # Setup mock earthquakes
        mock_earthquake1 = MagicMock()
        mock_earthquake1.magnitude = 3.2
        mock_earthquake1.place = "5km NE of Los Angeles, CA"
        mock_earthquake1.time = datetime(2024, 1, 15, 14, 30, 22)
        mock_earthquake1.latitude = 34.0522
        mock_earthquake1.longitude = -118.2437
        mock_earthquake1.depth = 8.5
        mock_earthquake1.status = "reviewed"
        mock_earthquake1.url = "https://earthquake.usgs.gov/earthquakes/eventpage/test1"
        
        mock_earthquake2 = MagicMock()
        mock_earthquake2.magnitude = 4.5
        mock_earthquake2.place = "10km SW of San Francisco, CA"
        mock_earthquake2.time = datetime(2024, 1, 15, 15, 45, 10)
        mock_earthquake2.latitude = 37.7749
        mock_earthquake2.longitude = -122.4194
        mock_earthquake2.depth = 12.3
        mock_earthquake2.status = "automatic"
        mock_earthquake2.url = "https://earthquake.usgs.gov/earthquakes/eventpage/test2"
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.count = 2
        mock_response.events = [mock_earthquake1, mock_earthquake2]
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.min_latitude = 33.0
        mock_service.min_longitude = -120.0
        mock_service.max_latitude = 35.0
        mock_service.max_longitude = -116.0
        mock_service.fetch_earthquakes.return_value = mock_response
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify dotenv was loaded
        mock_load_dotenv.assert_called_once()
        
        # Verify service was created and called
        mock_service_class.assert_called_once()
        mock_service.fetch_earthquakes.assert_called_once()
        
        # Check the fetch_earthquakes call arguments
        call_args = mock_service.fetch_earthquakes.call_args
        assert 'min_magnitude' in call_args.kwargs
        assert call_args.kwargs['min_magnitude'] == 2.0
        assert 'start_time' in call_args.kwargs
        assert 'limit' in call_args.kwargs
        assert call_args.kwargs['limit'] == 50
        
        # Verify output
        output = mock_stdout.getvalue()
        assert "UDPQuake - Earthquake Monitor" in output
        assert "Found 2 earthquakes in the last hour" in output
        assert "Search bounds: 33.0,-120.0 to 35.0,-116.0" in output
        assert "M3.2 | 5km NE of Los Angeles, CA" in output
        assert "M4.5 | 10km SW of San Francisco, CA" in output
        assert "2024-01-15 14:30:22 UTC" in output
        assert "34.052, -118.244" in output
        assert "8.5km | Status: reviewed" in output
        assert "⚠️  1 significant earthquake(s) detected!" in output
        assert "🚨 M4.5 - 10km SW of San Francisco, CA" in output
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_success_no_earthquakes(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function with no earthquakes found."""
        # Setup mock response with no earthquakes
        mock_response = MagicMock()
        mock_response.count = 0
        mock_response.events = []
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.min_latitude = 33.0
        mock_service.min_longitude = -120.0
        mock_service.max_latitude = 35.0
        mock_service.max_longitude = -116.0
        mock_service.fetch_earthquakes.return_value = mock_response
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify output
        output = mock_stdout.getvalue()
        assert "UDPQuake - Earthquake Monitor" in output
        assert "Found 0 earthquakes in the last hour" in output
        assert "⚠️" not in output  # No significant earthquakes message
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_success_no_significant_earthquakes(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function with earthquakes but none significant (< 4.0 magnitude)."""
        # Setup mock earthquake with low magnitude
        mock_earthquake = MagicMock()
        mock_earthquake.magnitude = 2.1
        mock_earthquake.place = "2km E of Small Town, CA"
        mock_earthquake.time = datetime(2024, 1, 15, 14, 30, 22)
        mock_earthquake.latitude = 34.0
        mock_earthquake.longitude = -118.0
        mock_earthquake.depth = 5.0
        mock_earthquake.status = "automatic"
        mock_earthquake.url = "https://earthquake.usgs.gov/earthquakes/eventpage/test"
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.count = 1
        mock_response.events = [mock_earthquake]
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.min_latitude = 33.0
        mock_service.min_longitude = -120.0
        mock_service.max_latitude = 35.0
        mock_service.max_longitude = -116.0
        mock_service.fetch_earthquakes.return_value = mock_response
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify output
        output = mock_stdout.getvalue()
        assert "UDPQuake - Earthquake Monitor" in output
        assert "Found 1 earthquakes in the last hour" in output
        assert "M2.1 | 2km E of Small Town, CA" in output
        assert "⚠️" not in output  # No significant earthquakes message
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_service_creation_error(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function when EarthquakeService creation fails."""
        # Make service creation raise an exception
        mock_service_class.side_effect = Exception("Service initialization failed")
        
        # Run main function
        main()
        
        # Verify error handling
        output = mock_stdout.getvalue()
        assert "Error fetching earthquake data: Service initialization failed" in output
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_fetch_earthquakes_error(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function when fetch_earthquakes fails."""
        # Setup mock service that raises an exception
        mock_service = MagicMock()
        mock_service.fetch_earthquakes.side_effect = ConnectionError("Failed to connect to USGS")
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify error handling
        output = mock_stdout.getvalue()
        assert "Error fetching earthquake data: Failed to connect to USGS" in output
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('main.datetime')
    def test_main_time_calculation(self, mock_datetime_module, mock_service_class, mock_load_dotenv):
        """Test that the time calculation for one hour ago is correct."""
        # Setup fixed datetime
        fixed_time = datetime(2024, 1, 15, 16, 30, 0, tzinfo=timezone.utc)
        mock_datetime_module.now.return_value = fixed_time
        mock_datetime_module.timedelta = timedelta  # Use real timedelta
        mock_datetime_module.timezone = timezone  # Use real timezone
        
        # Setup mock service and response
        mock_response = MagicMock()
        mock_response.count = 0
        mock_response.events = []
        
        mock_service = MagicMock()
        mock_service.min_latitude = 33.0
        mock_service.min_longitude = -120.0
        mock_service.max_latitude = 35.0
        mock_service.max_longitude = -116.0
        mock_service.fetch_earthquakes.return_value = mock_response
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify the start_time parameter
        call_args = mock_service.fetch_earthquakes.call_args
        expected_time = (fixed_time - timedelta(hours=1)).isoformat()
        assert call_args.kwargs['start_time'] == expected_time
    
    @patch('main.load_dotenv')
    @patch('main.EarthquakeService')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_multiple_significant_earthquakes(self, mock_stdout, mock_service_class, mock_load_dotenv):
        """Test main function with multiple significant earthquakes."""
        # Setup multiple significant earthquakes
        earthquakes = []
        for i in range(3):
            mock_eq = MagicMock()
            mock_eq.magnitude = 4.5 + i * 0.5  # 4.5, 5.0, 5.5
            mock_eq.place = f"Location {i+1}, CA"
            mock_eq.time = datetime(2024, 1, 15, 14, 30, 22)
            mock_eq.latitude = 34.0 + i
            mock_eq.longitude = -118.0 - i
            mock_eq.depth = 8.0 + i
            mock_eq.status = "reviewed"
            mock_eq.url = f"https://earthquake.usgs.gov/earthquakes/eventpage/test{i}"
            earthquakes.append(mock_eq)
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.count = 3
        mock_response.events = earthquakes
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.min_latitude = 33.0
        mock_service.min_longitude = -120.0
        mock_service.max_latitude = 35.0
        mock_service.max_longitude = -116.0
        mock_service.fetch_earthquakes.return_value = mock_response
        mock_service_class.return_value = mock_service
        
        # Run main function
        main()
        
        # Verify output
        output = mock_stdout.getvalue()
        assert "⚠️  3 significant earthquake(s) detected!" in output
        assert "🚨 M4.5 - Location 1, CA" in output
        assert "🚨 M5.0 - Location 2, CA" in output
        assert "🚨 M5.5 - Location 3, CA" in output


class TestMainIntegration:
    """Integration tests for main.py."""
    
    @patch('main.load_dotenv')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_real_service_mock_http(self, mock_stdout, mock_load_dotenv):
        """Test main with real EarthquakeService but mocked HTTP."""
        with patch('http.client.HTTPSConnection') as mock_connection:
            # Setup mock HTTP response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = """{
                "metadata": {"generated": 1748040061000, "count": 1},
                "features": [{
                    "id": "test_event",
                    "properties": {
                        "mag": 3.5,
                        "place": "Test Location, CA",
                        "time": 1748036384780,
                        "type": "earthquake",
                        "status": "reviewed",
                        "url": "https://test.url"
                    },
                    "geometry": {"coordinates": [-118.0, 34.0, 10.0]}
                }]
            }""".encode('utf-8')
            
            mock_conn = MagicMock()
            mock_conn.getresponse.return_value = mock_response
            mock_connection.return_value = mock_conn
            
            # Run main function
            main()
            
            # Verify some output
            output = mock_stdout.getvalue()
            assert "UDPQuake - Earthquake Monitor" in output
            assert "Test Location, CA" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])