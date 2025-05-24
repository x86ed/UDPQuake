# UDPQuake

A Raspberry Pi service that monitors USGS earthquake feeds and broadcasts seismic event data to Meshtastic mesh networks via UDP.

## Overview

UDPQuake is a Python service designed to run on Raspberry Pi nodes to provide real-time earthquake monitoring and alerting for mesh networks. The service subscribes to USGS earthquake data feeds and automatically pushes relevant seismic information to connected Meshtastic devices, enabling distributed earthquake awareness in off-grid or emergency communication scenarios.

## Features

- 🌍 Real-time USGS earthquake feed monitoring
- 📡 UDP broadcast to Meshtastic mesh networks
- 🔧 Configurable magnitude and distance thresholds
- 🚨 Automated alerting for significant seismic events
- 📊 Lightweight design optimized for Raspberry Pi
- 🔄 Automatic reconnection and error handling
- 📝 Comprehensive logging

## Hardware Requirements

- Raspberry Pi (3B+ or newer recommended)
- Meshtastic-compatible radio module (e.g., ESP32 with LoRa)
- Internet connection (WiFi or Ethernet)
- MicroSD card (16GB+ recommended)

## Software Requirements

- Python 3.12+
- Internet connectivity for USGS feed access
- Network access to Meshtastic devices

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/UDPQuake.git
cd UDPQuake/UDPQuake
```

### 2. Install Dependencies

```bash
pip install -e .
```

### 3. Configure the Service

Create a configuration file:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to match your setup:

```yaml
usgs:
  feed_url: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
  update_interval: 300  # seconds
  
filters:
  min_magnitude: 3.0
  max_distance_km: 500  # from your location
  location:
    latitude: 37.7749
    longitude: -122.4194
    
meshtastic:
  udp_host: "192.168.1.100"
  udp_port: 4403
  
logging:
  level: INFO
  file: "/var/log/udpquake.log"
```

### 4. Test the Service

Run the service manually to test:

```bash
python main.py
```

### 5. Install as System Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/udpquake.service
```

Add the following content:

```ini
[Unit]
Description=UDPQuake Seismic Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/UDPQuake/UDPQuake
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable udpquake
sudo systemctl start udpquake
```

## Configuration

### USGS Feed Options

- **feed_url**: USGS GeoJSON feed URL (hourly, daily, or weekly)
- **update_interval**: How often to check for new earthquakes (seconds)

### Filter Settings

- **min_magnitude**: Minimum earthquake magnitude to report
- **max_distance_km**: Maximum distance from your location to report
- **location**: Your coordinates for distance calculations

### Meshtastic Integration

- **udp_host**: IP address of your Meshtastic device
- **udp_port**: UDP port for Meshtastic communication (typically 4403)

## Usage

Once installed and configured, UDPQuake runs automatically as a background service. It will:

1. Poll the USGS earthquake feed at configured intervals
2. Filter earthquakes based on magnitude and distance
3. Format earthquake data for mesh transmission
4. Send UDP packets to connected Meshtastic devices
5. Log all activities for monitoring

### Manual Control

```bash
# Start the service
sudo systemctl start udpquake

# Stop the service
sudo systemctl stop udpquake

# Check service status
sudo systemctl status udpquake

# View logs
sudo journalctl -u udpquake -f
```

## Message Format

Earthquake alerts sent to the mesh include:

```
🚨 EARTHQUAKE ALERT
Magnitude: 4.2
Location: 15km SW of San Francisco, CA
Depth: 8.3km
Time: 2024-01-15 14:30:22 UTC
Distance from node: 23km
```

## Monitoring and Logs

- Service logs: `sudo journalctl -u udpquake`
- Application logs: `/var/log/udpquake.log` (if configured)
- Status monitoring: `sudo systemctl status udpquake`

## Troubleshooting

### Common Issues

1. **No earthquake data received**
   - Check internet connectivity
   - Verify USGS feed URL is accessible
   - Review filter settings (magnitude/distance thresholds)

2. **Meshtastic not receiving messages**
   - Verify UDP host/port configuration
   - Check network connectivity to Meshtastic device
   - Ensure Meshtastic device is in correct mode

3. **Service won't start**
   - Check Python dependencies: `pip list`
   - Verify configuration file syntax
   - Review systemd service file permissions

### Debug Mode

Run with verbose logging:

```bash
python main.py --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](../LICENSE) file for details.

## Acknowledgments

- [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) for providing real-time earthquake data
- [Meshtastic](https://meshtastic.org/) for the mesh networking platform
- The open-source community for inspiration and support

## Support

- 📧 Email: support@udpquake.org
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/UDPQuake/issues)
- 💬 Discussion: [GitHub Discussions](https://github.com/yourusername/UDPQuake/discussions)

---

**⚠️ Important**: This service is designed for informational purposes. Always rely on official emergency services and warning systems for critical earthquake information.