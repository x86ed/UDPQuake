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
            mock_send_position.assert_called_once_with(latitude, longitude, -10500.0)
            assert mock_sleep.call_count == 3
        
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
            
            # Check position is sent with depth of 0
            mock_send_position.assert_called_once_with(latitude, longitude, 0.0)
        
        # Clean up
        if 'mudp' in sys.modules:
            del sys.modules['mudp']