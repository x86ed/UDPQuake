from datetime import datetime
import time
from mudp import (
    conn,
    node,
    listen_for_packets,
    send_nodeinfo,
    send_text_message,
    send_position,
)

MCAST_GRP = "224.0.0.69"
MCAST_PORT = 4403


def setup_node(id: str, long_name: str, short_name: str, channel: str = "LongFast", key:str = "AQ=="):
    node.node_id = f"!{id}"
    node.long_name = long_name
    node.short_name = short_name
    node.channel = channel
    node.key = key
    conn.setup_multicast(MCAST_GRP, MCAST_PORT)

def send_quake(mag: float, place:str, when:int, latitude: float, longitude: float, depth: float = 0.0):
    """Send a quake message with position."""
    # Use a simple incrementing ID or hash of the earthquake data
    import hashlib
    earthquake_hash = hashlib.md5(f"{mag}{place}{when}".encode()).hexdigest()[:8]
    
    setup_node(earthquake_hash, place[:20], str(mag))  # Limit place name length
    send_nodeinfo()
    time.sleep(3)
    
    # Convert timestamp to human readable datetime
    # When is expected to be in milliseconds
    try:
        dt = datetime.fromtimestamp(when / 1000)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, OSError) as e:
        # Fallback if timestamp is invalid
        formatted_time = "Unknown time"
        print(f"Warning: Invalid timestamp {when}: {e}")
    
    # Create human readable message
    message = f"🚨 EARTHQUAKE ALERT 🚨\n"
    message += f"{formatted_time}\n"
    message += f"{place}\n"
    message += f"Mag: {mag:.1f} Depth: {depth:.1f} km"
    
    try:
        if mag > 3.5:
            send_text_message(message)
            time.sleep(3)
        
        # Send position with reasonable altitude (negative depth in meters, limited range)
        altitude_meters = int(max(-10000, min(0, -(depth * 1000))))  # Clamp between -10km and 0, convert to int
        send_position(latitude, longitude, altitude=altitude_meters)
        time.sleep(3)
        print(f"Successfully sent earthquake alert for M{mag:.1f} at {place}")
    except Exception as e:
        print(f"Error while sending message: {e}")
        # Continue execution, don't crash the service