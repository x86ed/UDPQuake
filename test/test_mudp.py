import pytest
import sys
import os
from unittest.mock import patch, Mock, call
import time
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the modules we need before importing
sys.modules['mudp'] = Mock()
sys.modules['mudp.conn'] = Mock()
sys.modules['mudp.node'] = Mock()

# Now import the module to test
from UDPQuake.mudp import setup_node, send_quake, MCAST_GRP, MCAST_PORT

class TestMUDP:
    
    @patch('UDPQuake.mudp.conn')
    @patch('UDPQuake.mudp.node')
    def test_setup_node(self, mock_node, mock_conn):
        """Test that setup_node correctly configures the node and connection."""
        # Test data
        id_str = "123456789"
        long_name = "Test Earthquake"
        short_name = "5.5"
        channel = "TestChannel"
        key = "TestKey=="
        
        # Call the function
        setup_node(id_str, long_name, short_name, channel, key)
        
        # Assertions
        assert mock_node.node_id == "!" + id_str
        assert mock_node.long_name == long_name
        assert mock_node.short_name == short_name
        assert mock_node.channel == channel
        assert mock_node.key == key
        mock_conn.setup_multicast.assert_called_once_with(MCAST_GRP, MCAST_PORT)
    
    @patch('UDPQuake.mudp.setup_node')
    @patch('UDPQuake.mudp.send_text_message')
    @patch('UDPQuake.mudp.send_position')
    @patch('UDPQuake.mudp.time.sleep')
    def test_send_quake(self, mock_sleep, mock_send_position, mock_send_text, mock_setup_node):
        """Test that send_quake correctly formats and sends the earthquake data."""
        # Test data
        mag = "5.5"
        place = "Test Location"
        when = 1621234567890  # Example timestamp in milliseconds
        latitude = 34.5678
        longitude = -118.1234
        depth = 10.5
        
        # Expected datetime conversion
        expected_dt = datetime.fromtimestamp(when / 1000)
        expected_time = expected_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Expected message format
        expected_message = (
            f"🚨 EARTHQUAKE ALERT 🚨\n"
            f"{expected_time}\n"
            f"{place}\n"
            f"Mag: {mag} Depth: {depth:.1f} km"
        )
        
        # Call the function
        send_quake(mag, place, when, latitude, longitude, depth)
        
        # Assertions
        mock_setup_node.assert_called_once_with(when, place, mag)
        mock_send_text.assert_called_once_with(expected_message)
        mock_send_position.assert_called_once_with(latitude, longitude, -10500.0)  # depth * 1000, negated
        
        # Verify sleep calls
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list == [call(3), call(3), call(3)]
    
    @patch('UDPQuake.mudp.setup_node')
    @patch('UDPQuake.mudp.send_text_message')
    @patch('UDPQuake.mudp.send_position')
    @patch('UDPQuake.mudp.time.sleep')
    def test_send_quake_default_depth(self, mock_sleep, mock_send_position, mock_send_text, mock_setup_node):
        """Test send_quake with default depth parameter."""
        # Test with default depth (0.0)
        mag = "4.2"
        place = "Another Place"
        when = 1621234567000
        latitude = 36.7777
        longitude = -122.3333
        
        # Call without specifying depth
        send_quake(mag, place, when, latitude, longitude)
        
        # Check position is sent with depth of 0
        mock_send_position.assert_called_once_with(latitude, longitude, 0.0)