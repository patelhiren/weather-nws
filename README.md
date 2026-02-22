# weather-nws

US weather forecasts via National Weather Service (NWS) API with automatic fallback to global weather for non-US locations.

## Features

- **US Locations:** Detailed forecasts from NWS with accumulation data, watches/warnings
- **Non-US Locations:** Automatic fallback to wttr.in global weather
- **Smart Detection:** Automatically selects the best source based on location
- **Clean Output:** Structured, emoji-enhanced format with actionable timing

## Quick Start

```bash
python3 scripts/get_weather.py "New York, NY"
```

## OpenClaw Skill

This repository is an [OpenClaw](https://openclaw.ai) skill. Install via:

```bash
openclaw skill install weather-nws
```

## How It Works

1. Geocodes location to lat/lon
2. Detects if location is in US
3. For US → NWS API (detailed accumulation + alerts)
4. For non-US → wttr.in (global coverage)
5. Returns consistent, formatted output

## Documentation

See [SKILL.md](SKILL.md) for full usage instructions and [references/nws-api.md](references/nws-api.md) for NWS API details.

## License

MIT
