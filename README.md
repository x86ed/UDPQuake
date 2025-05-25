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

## Setup and Installation

This project uses [UV](https://docs.astral.sh/uv/) for fast Python package management. Follow these steps for a complete setup:

### Prerequisites

- Python 3.12 or newer
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/) installed
- Internet connection for USGS feed access and dependency installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/UDPQuake.git
cd UDPQuake
```

### 2. Create Virtual Environment

```bash
uv venv
source .venv/bin/activate
```

### 3. Install Runtime Dependencies

```bash
uv pip install -e .
```

This installs the core dependencies:

- `requests` - For USGS earthquake API calls
- `python-dotenv` - For environment variable management

### 4. Install Development Dependencies (Optional)

If you plan to contribute or run tests:

```bash
uv pip install -e ".[dev]"
```

This adds development tools:

- `pytest` - For running unit tests
- `pytest-cov` - For test coverage reporting
- `black` - Code formatter
- `isort` - Import sorter
- `mypy` - Type checker

### 5. Verify Installation

Run the comprehensive unit tests to ensure everything is working:

```bash
pytest tests/ -v
```

You should see all tests pass in under a second.

### 6. Configure the Service

UDPQuake uses environment variables for configuration. Create a `.env` file in the project root:

```bash
touch .env
```

Edit the `.env` file to configure your setup:

```bash
# USGS Earthquake Service Configuration
USGS_HOST=earthquake.usgs.gov
EARTHQUAKE_MIN_LATITUDE=33.0
EARTHQUAKE_MIN_LONGITUDE=-120.0
EARTHQUAKE_MAX_LATITUDE=35.0
EARTHQUAKE_MAX_LONGITUDE=-116.0

# Optional: Override default coordinate bounds for your region
# Example for Southern California (default values shown above)
# For Northern California, you might use:
# EARTHQUAKE_MIN_LATITUDE=36.0
# EARTHQUAKE_MIN_LONGITUDE=-124.0
# EARTHQUAKE_MAX_LATITUDE=42.0
# EARTHQUAKE_MAX_LONGITUDE=-119.0
```

**Available Environment Variables:**

- `USGS_HOST` - USGS API hostname (default: `earthquake.usgs.gov`)
- `EARTHQUAKE_MIN_LATITUDE` - Southern boundary (default: `33.0`)
- `EARTHQUAKE_MIN_LONGITUDE` - Western boundary (default: `-120.0`)
- `EARTHQUAKE_MAX_LATITUDE` - Northern boundary (default: `35.0`)
- `EARTHQUAKE_MAX_LONGITUDE` - Eastern boundary (default: `-116.0`)

### 7. Test the Service

Run the service manually to test:

```bash
python -m udpquake
```

### 8. Install as System Service

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
WorkingDirectory=/home/pi/UDPQuake
ExecStart=/home/pi/UDPQuake/.venv/bin/python -m udpquake
Restart=always
RestartSec=10
Environment=PATH=/home/pi/UDPQuake/.venv/bin

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

UDPQuake is configured using environment variables defined in a `.env` file. Here are the available configuration options:

### USGS Service Configuration

- **USGS_HOST**: USGS API hostname (default: `earthquake.usgs.gov`)
- **EARTHQUAKE_MIN_LATITUDE**: Southern boundary for earthquake queries (default: `33.0`)
- **EARTHQUAKE_MIN_LONGITUDE**: Western boundary for earthquake queries (default: `-120.0`)
- **EARTHQUAKE_MAX_LATITUDE**: Northern boundary for earthquake queries (default: `35.0`)
- **EARTHQUAKE_MAX_LONGITUDE**: Eastern boundary for earthquake queries (default: `-116.0`)

### Regional Configuration Examples

**Southern California (default):**

```bash
EARTHQUAKE_MIN_LATITUDE=33.0
EARTHQUAKE_MIN_LONGITUDE=-120.0
EARTHQUAKE_MAX_LATITUDE=35.0
EARTHQUAKE_MAX_LONGITUDE=-116.0
```

**Northern California:**

```bash
EARTHQUAKE_MIN_LATITUDE=36.0
EARTHQUAKE_MIN_LONGITUDE=-124.0
EARTHQUAKE_MAX_LATITUDE=42.0
EARTHQUAKE_MAX_LONGITUDE=-119.0
```

**Pacific Northwest:**

```bash
EARTHQUAKE_MIN_LATITUDE=42.0
EARTHQUAKE_MIN_LONGITUDE=-125.0
EARTHQUAKE_MAX_LATITUDE=49.0
EARTHQUAKE_MAX_LONGITUDE=-116.0
```

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

```sh
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
   - Check Python dependencies: `uv pip list`
   - Verify environment variables in `.env` file
   - Review systemd service file permissions

### Debug Mode

For debugging, you can run the service directly to see console output:

```bash
python -m udpquake
```

Or check the systemd service logs:

```bash
sudo journalctl -u udpquake -f
```

## Development

### Version Management

This project uses [bump2version](https://github.com/c4urself/bump2version) for automated version management. Versions are automatically updated in both `src/udpquake/__init__.py` and `pyproject.toml`.

#### Version Bumping Examples

```bash
# Bump patch version (2.0.0-dev → 2.0.1-dev)
bumpversion patch

# Bump minor version (2.0.0-dev → 2.1.0-dev)
bumpversion minor

# Bump major version (2.0.0-dev → 3.0.0-dev)
bumpversion major

# Release from dev to production (2.0.0-dev → 2.0.0)
bumpversion --new-version "2.0.0" release

# Release stages: dev → alpha → beta → prod
bumpversion release  # dev → alpha
bumpversion release  # alpha → beta
bumpversion release  # beta → prod
```

#### Version Format

- Development: `X.Y.Z-dev`
- Alpha: `X.Y.Z-alpha`
- Beta: `X.Y.Z-beta`
- Production: `X.Y.Z`

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v

# Run specific test file
pytest tests/test_mudp.py -v

# Run with coverage report
pytest tests/ --cov=src/udpquake --cov-report=html
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

- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/UDPQuake/issues)
- 💬 Discussion: [GitHub Discussions](https://github.com/yourusername/UDPQuake/discussions)

---

**⚠️ Important**: This service is designed for informational purposes. Always rely on official emergency services and warning systems for critical earthquake information.
