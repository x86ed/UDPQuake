import pytest
import sys
from unittest.mock import Mock, patch
from datetime import datetime


class TestMUDP:
    
    def test_mudp_constants(self):
        """Test mudp constants are accessible."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Need to clear module cache and re-import to get constants
        if 'udpquake.mudp' in sys.modules:
            del sys.modules['udpquake.mudp']
        
        from udpquake.mudp import MCAST_GRP, MCAST_PORT
        assert MCAST_GRP == "224.0.0.69"
        assert MCAST_PORT == 4403
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_setup_node(self):
        """Test that setup_node correctly configures the node and connection."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.node') as mock_node:
            
            from udpquake.mudp import setup_node, MCAST_GRP, MCAST_PORT
            
            # Test data
            id_str = "123456789"
            long_name = "Test Earthquake"
            short_name = "5.5"
            channel = "TestChannel"
            key = "TestKey=="
            
            # Call the function
            setup_node(id_str, long_name, short_name, channel, key)
            
            # Verify the multicast setup was called correctly
            mock_conn.setup_multicast.assert_called_once_with(MCAST_GRP, MCAST_PORT)
            
            # Verify node configuration
            assert mock_node.node_id == f"!{id_str}"
            assert mock_node.long_name == long_name
            assert mock_node.short_name == short_name
            assert mock_node.channel == channel
            assert mock_node.key == key
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake(self):
        """Test that send_quake correctly formats and sends the earthquake data."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_text_message') as mock_send_text_message, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake, MCAST_GRP, MCAST_PORT
            
            # Test data
            mag = 5.5
            place = "Test Location"
            when = 1621234567890
            latitude = 34.5678
            longitude = -118.1234
            depth = 10.5
            
            # Expected message
            expected_dt = datetime.fromtimestamp(when / 1000)
            expected_time = expected_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            expected_message = (
                f"🚨 EARTHQUAKE ALERT 🚨\n"
                f"{expected_time}\n"
                f"{place}\n"
                f"Mag: {mag:.1f} Depth: {depth:.1f} km"
            )
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify calls
            mock_conn.setup_multicast.assert_called_once_with(MCAST_GRP, MCAST_PORT)
            mock_send_nodeinfo.assert_called_once()
            mock_send_text_message.assert_called_once_with(expected_message)
            
            # Verify altitude is converted to integer and clamped properly
            expected_altitude = int(max(-10000, min(0, -(depth * 1000))))  # -10500 clamped to -10000
            mock_send_position.assert_called_once_with(latitude, longitude, altitude=expected_altitude)
            assert mock_sleep.call_count == 3
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_hash_node_id(self):
        """Test that send_quake uses hash-based node ID generation."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.node') as mock_node, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_text_message') as mock_send_text_message, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake
            import hashlib
            
            # Test data
            mag = 3.2
            place = "Hash Test Location"
            when = 1621234567000
            latitude = 36.0
            longitude = -119.0
            depth = 5.0
            
            # Calculate expected hash
            expected_hash = hashlib.md5(f"{mag}{place}{when}".encode()).hexdigest()[:8]
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify node configuration uses hash
            assert mock_node.node_id == f"!{expected_hash}"
            assert mock_node.long_name == place[:20]  # Truncated to 20 chars
            assert mock_node.short_name == str(mag)
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_error_handling(self):
        """Test error handling in send_quake function."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_text_message') as mock_send_text_message, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            from udpquake.mudp import send_quake
            
            # Make send_text_message raise an exception
            mock_send_text_message.side_effect = Exception("Network error")
            
            # Test data
            mag = 4.0
            place = "Error Test"
            when = 1621234567000
            latitude = 35.0
            longitude = -118.0
            depth = 8.0
            
            # Call the function - should not raise exception
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify error was printed
            mock_print.assert_called_with("Error while sending message: Network error")
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_invalid_timestamp(self):
        """Test handling of invalid timestamp in send_quake."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_text_message') as mock_send_text_message, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            from udpquake.mudp import send_quake
            
            # Test data with invalid timestamp (infinity will trigger OverflowError)
            mag = 2.5
            place = "Invalid Time Test"
            when = float('inf')  # This should trigger OverflowError
            latitude = 34.0
            longitude = -117.0
            depth = 3.0
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify warning was printed for invalid timestamp  
            mock_print.assert_called()
            args_list = [str(call) for call in mock_print.call_args_list]
            warning_found = any(f"Warning: Invalid timestamp {when}:" in arg for arg in args_list)
            assert warning_found, f"Expected warning not found in print calls: {args_list}"
            
            # Verify message still sent with fallback time
            mock_send_text_message.assert_called_once()
            call_args = mock_send_text_message.call_args[0][0]
            assert "Unknown time" in call_args
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_default_depth(self):
        """Test send_quake with default depth parameter."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake
            
            # Test data
            mag = 4.2
            place = "Another Place"
            when = 1621234567000
            latitude = 36.7777
            longitude = -122.3333
            
            # Call without specifying depth
            send_quake(mag, place, when, latitude, longitude)
            
            # Check position is sent with depth of 0 converted to altitude
            expected_altitude = int(max(-10000, min(0, -(0.0 * 1000))))  # 0 depth = 0 altitude
            mock_send_position.assert_called_once_with(latitude, longitude, altitude=expected_altitude)
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
