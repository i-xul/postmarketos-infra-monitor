# postmarketos-infra-monitor

A touch-friendly GTK monitoring application for Raspberry Pi and self-hosted infrastructure.

## Overview

This project aims to turn a postmarketOS-powered tablet into a dedicated infrastructure monitoring device.

The application displays telemetry from Raspberry Pi systems and self-hosted services in a tablet-friendly interface, with support for multiple devices and touch-based navigation.

## Current Features

- GTK-based native Linux application
- Runs on postmarketOS
- Tablet-friendly layout
- Multiple device views
- JSON-based telemetry data source
- Raspberry Pi test devices included
- Pi-hole DNS telemetry
- Fail2ban telemetry
- Device-specific dashboard views
- Automatic refresh (30 seconds)

## Screenshot

### Current Prototype

![Prototype UI](screenshots/prototype-v0.1.png)
![Prototype UI](screenshots/swipe-navigation-v0.2.png)

## Current Features

- Native GTK application for postmarketOS
- Touch swipe navigation
- Multi-host monitoring
- SSH-based telemetry collection
- Automatic refresh (30 seconds)
- CPU temperature monitoring
- CPU load monitoring
- RAM usage monitoring
- Uptime monitoring
- Fail2ban telemetry
- Offline host detection

## Project Goals

The long-term goal is to provide a lightweight monitoring dashboard for:

- Raspberry Pi systems
- Docker hosts
- Fail2ban status
- Service health
- Self-hosted infrastructure

The application is designed for dedicated monitoring tablets rather than traditional desktop use.

## Current Version

```text
v0.2
```

### Completed

- GTK-based native Linux application
- Runs on postmarketOS
- Multi-device support
- Touch swipe navigation
- Dashboard card layout
- Screenshot documentation
- GitHub repository documentation
- Bounded navigation (no infinite device looping)

## Roadmap

### v0.3 – Live Telemetry

Replace static JSON data with real telemetry collected from Raspberry Pi devices.

Example:

```text
Tablet
    ↓ SSH
Raspberry Pi 5
    ↓
CPU temperature
CPU load
RAM usage
Uptime
```

Possible telemetry sources:

```bash
vcgencmd measure_temp
uptime
free -m
df -h
```

Planned additions:

- Docker container status
- Fail2ban statistics
- Pi-hole metrics
- Service health checks
- MagicMirror status

### v0.4

- Offline device detection
- Automatic refresh
- Multi-host support
- Status indicators
- Device health monitoring

## Recommended Next Milestone

Implement live SSH telemetry collection from a Raspberry Pi device and display real-time system information in the dashboard.

## Tested Platform

- Samsung Galaxy Tab A 9.7 LTE (SM-T555)
- postmarketOS
- XFCE4
- Python 3
- GTK3

## Development Notes

The application is developed and tested directly on the target postmarketOS device.

Current prototype uses static JSON telemetry data for UI development before integrating real telemetry collection.

## Repository Structure

```text
postmarketos-infra-monitor/
├── data/
│   ├── raspi4.json
│   └── raspi5.json
├── screenshots/
├── src/
│   └── app.py
├── run.sh
└── README.md
```

## Running

Launch the application on the tablet:

```bash
./run.sh
```

Or manually:

```bash
DISPLAY=:0 python3 src/app.py
```

## License

MIT
