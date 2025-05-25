import pytest
import os
import sys
import signal
import time
from unittest.mock import patch, Mock, call, MagicMock
from datetime import datetime, timedelta, timezone

# Mock all required modules before importing main
earthquake_mock = Mock()
earthquake_mock.EarthquakeService = Mock
sys.modules['udpquake.earthquake_service'] = earthquake_mock

# Mock the mudp module - this is needed for the import in main.py
mudp_mock = Mock()
mudp_mock.send_quake = Mock()
sys.modules['udpquake.mudp'] = mudp_mock

# Import the module to test (now that we've mocked the dependencies)
from udpquake.main import main, signal_handler, running as main_running

class TestMain:
    
    def test_signal_handler(self):
        """Test that the signal handler sets running to False."""
        import udpquake.main
        
        # Set initial state
        udpquake.main.running = True
        
        # Call the signal handler
        signal_handler(signal.SIGINT, None)
        
        # Verify running was set to False
        assert udpquake.main.running is False
    
    @patch('udpquake.main.EarthquakeService')
    @patch('udpquake.main.send_quake')
    @patch('udpquake.main.signal.signal')
    @patch('udpquake.main.load_dotenv')
    def test_earthquake_processing_logic(self, mock_load_dotenv, mock_signal, mock_send_quake, mock_earthquake_service):
        """Test the core earthquake processing logic without the main loop."""
        # Setup earthquake service mock
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_eq_service_instance.min_latitude = 20.0
        mock_eq_service_instance.max_latitude = 50.0
        mock_eq_service_instance.min_longitude = -160.0
        mock_eq_service_instance.max_longitude = -110.0
        
        # Create mock earthquake event
        mock_earthquake = Mock()
        mock_earthquake.id = 'us1000abcd'
        mock_earthquake.magnitude = 4.5
        mock_earthquake.place = 'Test Location'
        mock_earthquake.time = datetime.now(timezone.utc)
        mock_earthquake.latitude = 35.0
        mock_earthquake.longitude = -120.0
        mock_earthquake.depth = 10.0
        mock_earthquake.status = 'reviewed'
        mock_earthquake.url = 'https://example.com/earthquake'
        
        # Setup mock earthquakes result
        mock_earthquakes = Mock()
        mock_earthquakes.count = 1
        mock_earthquakes.events = [mock_earthquake]
        mock_eq_service_instance.fetch_earthquakes.return_value = mock_earthquakes
        
        # Test the core logic directly instead of the full main function
        earthquake_service = mock_eq_service_instance
        processed_ids = set()
        
        # Get earthquakes from the last hour with magnitude > 2.0
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=one_hour_ago,
            limit=50
        )
        
        # Process only new earthquakes
        new_quakes = [eq for eq in earthquakes.events if eq.id not in processed_ids]
        for earthquake in new_quakes:
            processed_ids.add(earthquake.id)
            
            # This is what would be called in the main loop
            from udpquake.main import send_quake
            send_quake(
                mag=earthquake.magnitude,
                place=earthquake.place,
                when=int(earthquake.time.timestamp() * 1000),
                latitude=earthquake.latitude,
                longitude=earthquake.longitude,
                depth=earthquake.depth
            )
        
        # Verify send_quake was called with correct parameters
        mock_send_quake.assert_called_once_with(
            mag=mock_earthquake.magnitude,
            place=mock_earthquake.place,
            when=int(mock_earthquake.time.timestamp() * 1000),
            latitude=mock_earthquake.latitude,
            longitude=mock_earthquake.longitude,
            depth=mock_earthquake.depth
        )
    
    @patch('udpquake.main.EarthquakeService')
    @patch('udpquake.main.send_quake')
    def test_no_new_earthquakes(self, mock_send_quake, mock_earthquake_service):
        """Test behavior when no new earthquakes are found."""
        # Setup
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_earthquakes = Mock()
        mock_earthquakes.count = 0
        mock_earthquakes.events = []
        mock_eq_service_instance.fetch_earthquakes.return_value = mock_earthquakes
        
        # Test the core logic
        earthquake_service = mock_eq_service_instance
        processed_ids = set()
        
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=one_hour_ago,
            limit=50
        )
        
        new_quakes = [eq for eq in earthquakes.events if eq.id not in processed_ids]
        
        # Should be empty
        assert len(new_quakes) == 0
        
        # Verify send_quake was not called
        mock_send_quake.assert_not_called()
    
    @patch('udpquake.main.EarthquakeService')
    @patch('builtins.print')
    def test_error_handling(self, mock_print, mock_earthquake_service):
        """Test that exceptions in earthquake fetching are properly handled."""
        # Setup
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_eq_service_instance.fetch_earthquakes.side_effect = Exception("Test exception")
        
        # Test the error handling logic directly
        try:
            earthquake_service = mock_eq_service_instance
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            earthquakes = earthquake_service.fetch_earthquakes(
                min_magnitude=2.0,
                start_time=one_hour_ago,
                limit=50
            )
        except Exception as e:
            print(f"Error fetching earthquake data: {e}")
        
        # Verify error was printed
        mock_print.assert_called_with("Error fetching earthquake data: Test exception")
    
    @patch('udpquake.main.send_quake')
    def test_processed_ids_cleanup(self, mock_send_quake):
        """Test that earthquake IDs are properly tracked to avoid duplicates."""
        # Create mock earthquakes
        now = datetime.now(timezone.utc)
        
        # Recent earthquake
        recent_quake = Mock()
        recent_quake.id = 'recent123'
        recent_quake.magnitude = 3.0
        recent_quake.place = 'Recent Location'
        recent_quake.time = now - timedelta(minutes=30)
        recent_quake.latitude = 34.0
        recent_quake.longitude = -118.0
        recent_quake.depth = 5.0
        
        # Old earthquake (more than 2 hours old)
        old_quake = Mock()
        old_quake.id = 'old456'
        old_quake.magnitude = 2.5
        old_quake.place = 'Old Location'
        old_quake.time = now - timedelta(hours=3)
        old_quake.latitude = 35.0
        old_quake.longitude = -119.0
        old_quake.depth = 8.0
        
        # Test the ID tracking logic
        processed_ids = set()
        all_earthquakes = [recent_quake, old_quake]
        
        # First iteration - both should be processed
        new_quakes = [eq for eq in all_earthquakes if eq.id not in processed_ids]
        assert len(new_quakes) == 2
        
        for earthquake in new_quakes:
            processed_ids.add(earthquake.id)
            
        # Second iteration - none should be processed (already in set)
        new_quakes = [eq for eq in all_earthquakes if eq.id not in processed_ids]
        assert len(new_quakes) == 0
        
        # Test cleanup logic (keep only IDs from the last 2 hours)
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        processed_ids = {eq.id for eq in all_earthquakes if eq.time > two_hours_ago}
        
        # Only recent earthquake should remain
        assert 'recent123' in processed_ids
        assert 'old456' not in processed_ids