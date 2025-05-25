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
    setup_node(str(when), place, str(mag))
    send_nodeinfo()
    time.sleep(3)
    # Convert timestamp to human readable datetime
    dt = datetime.fromtimestamp(when / 1000)  # Assuming when is in milliseconds
    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Create human readable message
    message = f"🚨 EARTHQUAKE ALERT 🚨\n"
    message += f"{formatted_time}\n"
    message += f"{place}\n"
    message += f"Mag: {mag:.1f} Depth: {depth:.1f} km"
    send_text_message(message)
    time.sleep(3)
    send_position(latitude,longitude, 0-(depth*1000))
    time.sleep(3)