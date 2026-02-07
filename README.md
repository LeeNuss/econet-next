# ecoNEXT

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for Plum heat pump controllers via the [econext-gateway](https://github.com/LeeNuss/econext-gateway).

## Overview

This integration connects to an econext-gateway running on your local network, providing real-time monitoring and control of your GM3 protocol based heat pump controllers (ecoMAX360i).

## Features

- Temperature sensors (thermostat, calculated, room setpoint, DHW, outdoor)
- Climate entities for heating circuits with comfort/eco presets
- Number entities for editable parameters (setpoints, hysteresis, heating curves)
- Select entities for operating modes and circuit types
- Switch entities for enabling/disabling functions
- Binary sensors for alarm states
- Button entities for heat pump commands

## Requirements

- Home Assistant 2024.1.0 or newer
- A running [econext-gateway](https://github.com/LeeNuss/econext-gateway) instance connected to your controller via RS-485

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > three-dot menu > **Custom repositories**
3. Add `https://github.com/LeeNuss/econext` as type **Integration**
4. Click **Download** and restart Home Assistant

### Manual

Copy the `custom_components/econext` folder to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **ecoNEXT**
3. Enter the IP address and port (default: 8000) of your gateway

## Schedule Card

For weekly heating schedule management, install the [econext-schedule-card](https://github.com/LeeNuss/econext-schedule-card) Lovelace card:

1. Open HACS > **Frontend** > three-dot menu > **Custom repositories**
2. Add `https://github.com/LeeNuss/econext-schedule-card` as type **Dashboard**
3. Click **Download** and reload your browser

## Supported Devices

- Plum ecoMAX controllers (ecoMAX360i and similar)
- ecoTRONIC heat pump controllers
- Other devices using the GM3 serial protocol
