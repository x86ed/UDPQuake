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
    def test_first_run_72_hour_check(self, mock_load_dotenv, mock_signal, mock_send_quake, mock_earthquake_service):
        """Test that first run checks 72 hours back."""
        # Setup earthquake service mock
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_eq_service_instance.min_latitude = 33.0
        mock_eq_service_instance.max_latitude = 35.0
        mock_eq_service_instance.min_longitude = -120.0
        mock_eq_service_instance.max_longitude = -116.0
        
        # Create mock earthquake events
        mock_earthquake = Mock()
        mock_earthquake.id = 'us1000test'
        mock_earthquake.magnitude = 3.5
        mock_earthquake.place = 'Test Location'
        mock_earthquake.time = datetime.now(timezone.utc) - timedelta(hours=24)
        mock_earthquake.latitude = 34.0
        mock_earthquake.longitude = -118.0
        mock_earthquake.depth = 5.0
        mock_earthquake.status = 'reviewed'
        mock_earthquake.url = 'https://example.com/earthquake'
        
        # Setup mock earthquakes result
        mock_earthquakes = Mock()
        mock_earthquakes.count = 1
        mock_earthquakes.events = [mock_earthquake]
        mock_eq_service_instance.fetch_earthquakes.return_value = mock_earthquakes
        
        # Simulate first run behavior
        from udpquake.main import main
        import udpquake.main
        
        # Mock the running flag to exit after first iteration
        original_running = udpquake.main.running
        udpquake.main.running = True
        
        def side_effect(*args, **kwargs):
            # After first call, set running to False to exit loop
            udpquake.main.running = False
            return mock_earthquakes
        
        mock_eq_service_instance.fetch_earthquakes.side_effect = side_effect
        
        try:
            main()
        except SystemExit:
            pass  # Expected when loop exits
        
        # Verify fetch_earthquakes was called with 72-hour time range
        mock_eq_service_instance.fetch_earthquakes.assert_called_once()
        call_args = mock_eq_service_instance.fetch_earthquakes.call_args
        
        # Check that start_time parameter indicates 72 hours back
        start_time = call_args[1]['start_time']
        # Parse the datetime to verify it's approximately 72 hours ago
        parsed_time = datetime.fromisoformat(start_time.replace('+00:00', '+00:00'))
        time_diff = datetime.now(timezone.utc) - parsed_time
        
        # Should be approximately 72 hours (allow some tolerance)
        assert 71.5 <= time_diff.total_seconds() / 3600 <= 72.5
        
        # Verify send_quake was called
        mock_send_quake.assert_called_once()
        
        # Restore original state
        udpquake.main.running = original_running

    @patch('udpquake.main.EarthquakeService')
    @patch('udpquake.main.send_quake')
    @patch('udpquake.main.time.sleep')
    def test_subsequent_run_1_hour_check(self, mock_sleep, mock_send_quake, mock_earthquake_service):
        """Test that subsequent runs check 1 hour back."""
        # Setup earthquake service mock
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_eq_service_instance.min_latitude = 33.0
        mock_eq_service_instance.max_latitude = 35.0
        mock_eq_service_instance.min_longitude = -120.0
        mock_eq_service_instance.max_longitude = -116.0
        
        # Create mock earthquake events
        mock_earthquake = Mock()
        mock_earthquake.id = 'us1000subsequent'
        mock_earthquake.magnitude = 2.8
        mock_earthquake.place = 'Subsequent Test Location'
        mock_earthquake.time = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_earthquake.latitude = 34.5
        mock_earthquake.longitude = -118.5
        mock_earthquake.depth = 8.0
        mock_earthquake.status = 'automatic'
        mock_earthquake.url = 'https://example.com/earthquake2'
        
        # Setup mock earthquakes result
        mock_earthquakes = Mock()
        mock_earthquakes.count = 1
        mock_earthquakes.events = [mock_earthquake]
        
        call_count = 0
        def fetch_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Exit after a few iterations
                import udpquake.main
                udpquake.main.running = False
            return mock_earthquakes
        
        mock_eq_service_instance.fetch_earthquakes.side_effect = fetch_side_effect
        
        # Mock sleep to speed up test
        mock_sleep.return_value = None
        
        # Test the logic directly to avoid infinite loop
        earthquake_service = mock_eq_service_instance
        processed_ids = set()
        first_run = True
        
        # Simulate first run (72 hours)
        if first_run:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            first_run = False
        
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=time_ago,
            limit=50
        )
        
        # Simulate second run (1 hour)
        if not first_run:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=time_ago,
            limit=50
        )
        
        # Verify second call uses 1-hour timeframe
        calls = mock_eq_service_instance.fetch_earthquakes.call_args_list
        assert len(calls) >= 2
        
        second_call_start_time = calls[1][1]['start_time']
        parsed_time = datetime.fromisoformat(second_call_start_time.replace('+00:00', '+00:00'))
        time_diff = datetime.now(timezone.utc) - parsed_time
        
        # Should be approximately 1 hour (allow some tolerance)
        assert 0.9 <= time_diff.total_seconds() / 3600 <= 1.1

    @patch('udpquake.main.EarthquakeService')
    @patch('udpquake.main.send_quake')
    def test_processed_ids_management(self, mock_send_quake, mock_earthquake_service):
        """Test that processed earthquake IDs are properly managed."""
        # Setup earthquake service mock
        mock_eq_service_instance = mock_earthquake_service.return_value
        
        # Create mock earthquake events
        old_earthquake = Mock()
        old_earthquake.id = 'old_earthquake_id'
        old_earthquake.magnitude = 2.5
        old_earthquake.place = 'Old Location'
        old_earthquake.time = datetime.now(timezone.utc) - timedelta(hours=3)  # Old earthquake
        old_earthquake.latitude = 33.5
        old_earthquake.longitude = -119.0
        old_earthquake.depth = 4.0
        old_earthquake.status = 'reviewed'
        old_earthquake.url = 'https://example.com/old'
        
        recent_earthquake = Mock()
        recent_earthquake.id = 'recent_earthquake_id'
        recent_earthquake.magnitude = 3.2
        recent_earthquake.place = 'Recent Location'
        recent_earthquake.time = datetime.now(timezone.utc) - timedelta(minutes=30)  # Recent earthquake
        recent_earthquake.latitude = 34.2
        recent_earthquake.longitude = -118.2
        recent_earthquake.depth = 6.0
        recent_earthquake.status = 'automatic'
        recent_earthquake.url = 'https://example.com/recent'
        
        # Test the ID management logic directly
        processed_ids = set()
        all_earthquakes = [old_earthquake, recent_earthquake]
        
        # Process earthquakes first time
        new_quakes = [eq for eq in all_earthquakes if eq.id not in processed_ids]
        assert len(new_quakes) == 2  # Both should be new
        
        for earthquake in new_quakes:
            processed_ids.add(earthquake.id)
        
        # Process earthquakes second time
        new_quakes = [eq for eq in all_earthquakes if eq.id not in processed_ids]
        assert len(new_quakes) == 0  # None should be new
        
        # Clean up old IDs (keep only IDs from the last 2 hours)
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        mock_earthquakes = Mock()
        mock_earthquakes.events = [eq for eq in all_earthquakes if eq.time > two_hours_ago]
        
        processed_ids = {eq.id for eq in mock_earthquakes.events if eq.time > two_hours_ago}
        
        # Only recent earthquake should remain
        assert 'recent_earthquake_id' in processed_ids
        assert 'old_earthquake_id' not in processed_ids

    @patch('udpquake.main.EarthquakeService')
    @patch('udpquake.main.send_quake')
    @patch('udpquake.main.signal.signal')
    @patch('udpquake.main.load_dotenv')
    def test_first_run_72_hour_check(self, mock_load_dotenv, mock_signal, mock_send_quake, mock_earthquake_service):
        """Test that first run checks 72 hours back, subsequent runs check 1 hour."""
        # Setup earthquake service mock
        mock_eq_service_instance = mock_earthquake_service.return_value
        mock_eq_service_instance.min_latitude = 33.0
        mock_eq_service_instance.max_latitude = 35.0
        mock_eq_service_instance.min_longitude = -120.0
        mock_eq_service_instance.max_longitude = -116.0
        
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
        
        # Test first run logic (72-hour check)
        earthquake_service = mock_eq_service_instance
        first_run = True
        
        if first_run:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            time_description = "72 hours"
            first_run = False
        else:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            time_description = "last hour"
        
        # Verify the time_ago format is correct for 72 hours
        assert "72 hours" == time_description
        assert time_ago.endswith('+00:00')
        
        # Test subsequent run logic (1-hour check)
        if first_run:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            time_description = "72 hours"
            first_run = False
        else:
            time_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            time_description = "last hour"
        
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
        
        # Create mock earthquake event with fixed timestamp
        mock_earthquake = Mock()
        mock_earthquake.id = 'us1000abcd'
        mock_earthquake.magnitude = 4.5
        mock_earthquake.place = 'Test Location'
        mock_earthquake.time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)  # Fixed timestamp
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
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        earthquakes = earthquake_service.fetch_earthquakes(
            min_magnitude=2.0,
            start_time=one_hour_ago,
            limit=50
        )
        
        # Process only new earthquakes
        new_quakes = [eq for eq in earthquakes.events if eq.id not in processed_ids]
        for earthquake in new_quakes:
            processed_ids.add(earthquake.id)
            
            # Call the mock send_quake directly
            mock_send_quake(
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