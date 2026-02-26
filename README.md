# weather-nws

US weather forecasts via National Weather Service (NWS) API with automatic fallback to global weather for non-US locations. Supports hourly forecasts, air quality, station observations, astronomical times, aviation forecasts, and fire weather.

## Features

| Feature | Description | Flag |
|---------|-------------|------|
| 🌦️ **NWS Forecast** | Detailed 12-hour forecast with accumulation data | *(default)* |
| ⏰ **Hourly Forecast** | Time-specific hourly breakdown (auto-detected) | `--hourly` |
| 💨 **Air Quality** | EPA AirNow AQI with health recommendations | `--aqi` |
| 🌡️ **Station Observations** | Current conditions vs forecast comparison | `--current` |
| ☀️ **Astronomical Times** | Sunrise/sunset, twilight, moon phase | `--astro` |
| ✈️ **Aviation Forecast** | Terminal Aerodrome Forecast (TAF) | `--taf` |
| 🔥 **Fire Weather** | Fire danger and red flag warnings | `--fire` |
| 🌍 **Global Fallback** | Automatic wttr.in for non-US locations | *(auto)* |

## Quick Start

```bash
# Basic forecast
python3 scripts/get_weather.py "New York, NY"

# With air quality
python3 scripts/get_weather.py "Boston" --aqi

# Station observation vs forecast
python3 scripts/get_weather.py "Seattle" --current

# Sunrise/sunset times
python3 scripts/get_weather.py "Denver" --astro

# Combine features
python3 scripts/get_weather.py "San Diego" --aqi --current --astro
```

## Hourly Auto-Detection

Time-specific queries automatically switch to hourly mode:

```bash
python3 scripts/get_weather.py "Seattle at 5 PM"      # Auto-detected
python3 scripts/get_weather.py "Chicago tonight"       # Auto-detected
python3 scripts/get_weather.py "Miami tomorrow morning" # Auto-detected
```

## AirNow API Key (Optional)

The AirNow API works without a key but has rate limits. For reliable access:

1. Request a free key at: https://docs.airnowapi.org/account/request/
2. Set environment variable: `export AIRNOW_API_KEY="your-key"`

## OpenClaw Skill

This repository is an [OpenClaw](https://openclaw.ai) skill. Install via:

```bash
openclaw skill install weather-nws
```

Or clone to your OpenClaw skills directory:

```bash
cd ~/clawd/skills
git clone https://github.com/patelhiren/weather-nws.git
```

## Requirements

- Python 3.7+
- `python-dateutil` (optional, for enhanced parsing)
- Internet connection
- No API keys required for basic NWS/wttr.in usage

## How It Works

1. Geocodes location to lat/lon (OpenStreetMap Nominatim)
2. Detects if location is in US
3. **For US:** Fetches from NWS API with optional AirNow AQI
4. **For non-US:** Falls back to wttr.in global weather
5. Returns consistent, emoji-enhanced formatted output

## Documentation

- **[SKILL.md](SKILL.md)** — Full usage documentation with examples
- **[references/nws-api.md](references/nws-api.md)** — NWS API endpoint reference
- **[references/airnow-api.md](references/airnow-api.md)** — AirNow API documentation

## Example Output

```
🌦️ **Seattle, WA Forecast**

**☁️ Tonight**
Rain likely. Low around 42. South wind 5-10 mph.

**☀️ Friday**
Partly sunny. High near 52. West wind around 5 mph.

🌡️ **Observed Conditions**
Actually 45°F (3° warmer than 42° forecast)
☔ Rain, Mist
💨 S 7 mph • 💧 89% humidity • 📊 Pressure 29.82 inHg

💨 **Air Quality — Seattle, WA**
Current:
🟢 AQI 35 — Good
Primary pollutant: PM2.5
💡 Air quality is satisfactory. Enjoy your outdoor activities!

☀️ **Astronomical Times — Seattle, WA**
🌅 Sunrise: 6:48 AM (in 10h)
🌇 Sunset: 5:32 PM (in 9h)
💡 Civil Twilight: 6:18 AM – 6:02 PM
⏱️ Daylight: 10h 44m
🌙 Moon: 🌓 First Quarter (50.0%)
```

## Changelog

See [SKILL.md#changelog](SKILL.md#changelog) for version history.

## License

MIT
