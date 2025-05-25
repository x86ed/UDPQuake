import sys
import hashlib
import pytest
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
    
    def test_setup_node_with_defaults(self):
        """Test that setup_node works with default channel and key parameters."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.node') as mock_node:
            
            from udpquake.mudp import setup_node, MCAST_GRP, MCAST_PORT
            
            # Test data with defaults
            id_str = "987654321"
            long_name = "Default Test"
            short_name = "4.2"
            
            # Call the function with defaults
            setup_node(id_str, long_name, short_name)
            
            # Verify the multicast setup was called correctly
            mock_conn.setup_multicast.assert_called_once_with(MCAST_GRP, MCAST_PORT)
            
            # Verify node configuration with defaults
            assert mock_node.node_id == f"!{id_str}"
            assert mock_node.long_name == long_name
            assert mock_node.short_name == short_name
            assert mock_node.channel == "LongFast"  # Default
            assert mock_node.key == "AQ=="  # Default
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_above_threshold(self):
        """Test that send_quake sends text message for earthquakes above magnitude 3.5."""
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
            
            # Test data - magnitude above threshold
            mag = 4.5
            place = "Test Location Above Threshold"
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
    
    def test_send_quake_below_threshold(self):
        """Test that send_quake does NOT send text message for earthquakes below magnitude 3.5."""
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
            
            # Test data - magnitude below threshold
            mag = 3.2
            place = "Test Location Below Threshold"
            when = 1621234567890
            latitude = 34.5678
            longitude = -118.1234
            depth = 8.0
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify calls
            mock_conn.setup_multicast.assert_called_once_with(MCAST_GRP, MCAST_PORT)
            mock_send_nodeinfo.assert_called_once()
            # Text message should NOT be sent for magnitude below 3.5
            mock_send_text_message.assert_not_called()
            
            # Position should still be sent
            expected_altitude = int(max(-10000, min(0, -(depth * 1000))))
            mock_send_position.assert_called_once_with(latitude, longitude, altitude=expected_altitude)
            # Should only sleep twice (after nodeinfo and after position, not after text message)
            assert mock_sleep.call_count == 2
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_exactly_at_threshold(self):
        """Test that send_quake does NOT send text message for magnitude exactly 3.5."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_text_message') as mock_send_text_message, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake
            
            # Test data - magnitude exactly at threshold
            mag = 3.5
            place = "Test Location At Threshold"
            when = 1621234567890
            latitude = 34.0
            longitude = -118.0
            depth = 5.0
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Text message should NOT be sent for magnitude exactly 3.5 (only > 3.5)
            mock_send_text_message.assert_not_called()
            
            # Position should still be sent
            mock_send_position.assert_called_once()
        
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
            
            # Test data
            mag = 4.2
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
    
    def test_send_quake_long_place_name_truncation(self):
        """Test that long place names are truncated to 20 characters."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.node') as mock_node, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake
            
            # Test data with very long place name
            mag = 2.8  # Below threshold, so no text message
            place = "This is a very long place name that should be truncated"
            when = 1621234567000
            latitude = 35.0
            longitude = -117.0
            depth = 3.0
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify place name was truncated to 20 characters
            assert mock_node.long_name == place[:20]
            assert len(mock_node.long_name) == 20
        
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
            
            # Make send_position raise an exception
            mock_send_position.side_effect = Exception("Network error")
            
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
            
            # Test data with invalid timestamp (too large)
            mag = 4.5
            place = "Invalid Time Test"
            when = 9999999999999999  # This should trigger OverflowError
            latitude = 34.0
            longitude = -117.0
            depth = 3.0
            
            # Call the function
            send_quake(mag, place, when, latitude, longitude, depth)
            
            # Verify warning was printed for invalid timestamp
            warning_printed = False
            for call in mock_print.call_args_list:
                args = call[0][0] if call[0] else ""
                if "Warning: Invalid timestamp" in str(args):
                    warning_printed = True
                    break
            assert warning_printed, "Expected warning about invalid timestamp"
            
            # Should still send text message (mag > 3.5) with "Unknown time"
            mock_send_text_message.assert_called_once()
            message = mock_send_text_message.call_args[0][0]
            assert "Unknown time" in message
        
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
            
            # Test data without depth parameter (should default to 0.0)
            mag = 2.5  # Below threshold
            place = "Default Depth Test"
            when = 1621234567000
            latitude = 34.0
            longitude = -117.0
            
            # Call the function without depth parameter
            send_quake(mag, place, when, latitude, longitude)
            
            # Verify altitude calculation with default depth (0.0)
            expected_altitude = int(max(-10000, min(0, -(0.0 * 1000))))  # Should be 0
            mock_send_position.assert_called_once_with(latitude, longitude, altitude=expected_altitude)
            assert expected_altitude == 0
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']
    
    def test_send_quake_altitude_clamping(self):
        """Test that altitude is properly clamped between -10000 and 0 meters."""
        # Mock the external mudp module
        mock_mudp = Mock()
        sys.modules['mudp'] = mock_mudp
        
        # Patch the imported objects in the module
        with patch('udpquake.mudp.conn') as mock_conn, \
             patch('udpquake.mudp.send_nodeinfo') as mock_send_nodeinfo, \
             patch('udpquake.mudp.send_position') as mock_send_position, \
             patch('time.sleep') as mock_sleep:
            
            from udpquake.mudp import send_quake
            
            # Test cases for altitude clamping
            test_cases = [
                (15.0, -10000),  # 15km depth should clamp to -10000m
                (5.0, -5000),    # 5km depth should be -5000m
                (0.0, 0),        # 0km depth should be 0m
                (25.0, -10000),  # 25km depth should clamp to -10000m
            ]
            
            for depth, expected_altitude in test_cases:
                mock_send_position.reset_mock()
                
                send_quake(2.0, "Altitude Test", 1621234567000, 34.0, -117.0, depth)
                
                mock_send_position.assert_called_once_with(34.0, -117.0, altitude=expected_altitude)
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])