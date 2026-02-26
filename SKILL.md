---
name: weather-nws
description: "US weather forecasts via National Weather Service (NWS) with automatic fallback to global weather for non-US locations. Provides detailed accumulation data, watches/warnings, and actionable timing. Use for: US-based weather queries, winter storm forecasts, precipitation accumulation estimates, severe weather alerts. Automatically falls back to global weather via wttr.in for international locations."
homepage: https://api.weather.gov/
metadata: {"clawdhub":{"emoji":"🌦️"}}
---

# Weather NWS Skill

Get detailed US weather forecasts from the National Weather Service with automatic global fallback.

## What This Skill Does

This skill operates in **5 modes** to match your query:

| Mode | When It Activates | What You Get |
|------|-------------------|--------------|
| 🌦️ **Standard Forecast** | Default (no time specified) | 12-hour forecast with today/tonight/tomorrow |
| ⏰ **Hourly Forecast** | Time-specific query detected | Hour-by-hour breakdown (~156 periods, 7 days) |
| 🌨️ **Winter Storm** | Keywords like "snow," "storm" | 12-hour + structured accumulation data |
| 💨 **AQI Report** | `--aqi` flag included | Current + forecast air quality index |
| 🌍 **Global Fallback** | Non-US location | wttr.in data (less detailed) |

### Hourly Auto-Detection

The skill automatically detects time-specific language and switches to hourly forecast:

```
"Boston at 8 PM"        → ⏰ Hourly mode
"Boston tonight"         → ⏰ Hourly mode
"Boston tomorrow morning" → ⏰ Hourly mode
"Boston at 5:30"         → ⏰ Hourly mode
"When will it stop raining?" → ⏰ Hourly mode
```

**Patterns detected:**
- `at 8 PM`, `at 5:30`, etc.
- `tonight`, `this afternoon`
- `tomorrow morning/afternoon/night`
- `when will...`, `how long until...`

### Air Quality (`--aqi`)

Adds AirNow AQI data to any forecast:

```
python3 ./scripts/get_weather.py "Boston" --aqi
```

**Output includes:**
- Current AQI with color-coded emoji (🟢 🟡 🟠 🔴 🟣 🔵)
- Primary pollutant (PM2.5, O3, etc.)
- Health recommendation based on category
- 3-day AQI forecast

**AQI Categories:**
| Range | Category | Emoji | Recommendation |
|-------|----------|-------|------------------|
| 0-50 | Good | 🟢 | Enjoy outdoor activities |
| 51-100 | Moderate | 🟡 | Sensitive groups limit exertion |
| 101-150 | Unhealthy for Sensitive Groups | 🟠 | Children/elderly limit outdoor activities |
| 151-200 | Unhealthy | 🔴 | Everyone reduce outdoor exertion |
| 201-300 | Very Unhealthy | 🟣 | Avoid outdoor activities |
| 301-500 | Hazardous | 🔵 | Stay indoors — health alert |

## When to Use

✅ **USE this skill when:**

- "What's the weather in [US city]?"
- "How much snow is expected?"
- "Winter storm forecast for [location]"
- "Will it rain tomorrow in [US city]?"
- "What time will the rain stop?"
- "Air quality in [city] today"
- Any US-based weather query

🔄 **Automatic fallback:**

- Non-US locations → wttr.in
- NWS API unavailable → wttr.in
- Both sources fail → clear error message

## Quick Start

```bash
# Run the unified weather script
python3 ./scripts/get_weather.py "New York, NY"

# Force specific source if needed (normally auto-detected)
python3 ./scripts/get_weather.py "London, UK" --source wttr

# Get hourly forecast (auto-detected or forced)
python3 ./scripts/get_weather.py "Boston at 8 PM"
python3 ./scripts/get_weather.py "Chicago" --hourly

# Include air quality
python3 ./scripts/get_weather.py "Seattle" --aqi
```

## Output Format

The script provides consistent output regardless of source:

**Header:** Location and current alert status  
**Today → Tonight → Tomorrow:** Structured timeline  
**Accumulations:** Specific snow/rain amounts when available (structured from grid data)  
**Hourly (if requested):** Time → temp → conditions → precipitation probability  
**AQI (if requested):** Current + forecast air quality with health guidance  
**Bottom Line:** Actionable summary with timing

## Implementation

The script handles:
1. Geocoding location to lat/long
2. Detecting if location is in US
3. Detecting temporal queries and auto-switching to hourly
4. Calling NWS API for US locations (detailed accumulation)
5. Getting structured grid data for snow/ice amounts when relevant
6. Fetching AirNow AQI data when `--aqi` flag is used
7. Falling back to wttr.in for non-US (basic forecast)
8. Formatting consistent output with emojis and structure

## How It Decides

| Scenario | Action |
|----------|--------|
| Location in US, no time specified | NWS 12-hour forecast + alerts |
| Location in US, time detected | NWS hourly forecast (~156 periods) |
| Location in US, winter keywords | NWS 12-hour + structured accumulation data |
| `--aqi` flag included | NWS/AirNow AQI data appended |
| Location outside US | wttr.in global fallback |
| NWS API fails | wttr.in fallback for US too |

## Limitations

| Source | Limitations |
|--------|-------------|
| **NWS** | US only, requires internet, rate limited to ~1 req/2 sec |
| **NWS Hourly** | ~156 periods max (7 days), some gaps possible |
| **NWS Grid Data** | Structured accumulations only available for forecast office coverage area |
| **AirNow AQI** | US only, may have gaps in rural areas, requires API key for best results |
| **wttr.in** | Global, less detail on accumulation, no official watches/warnings |

**Known gaps:**
- International locations don't get AQI (no global AirNow equivalent)
- Grid data accumulations may not load for some remote US areas
- Hourly forecast is time-restricted (7 days forward max)

## Examples

**US winter storm query:**
```
python3 ./scripts/get_weather.py "Boston, MA"
```
→ Returns NWS data with accumulation estimates if snow keywords detected

**Hourly forecast:**
```
python3 ./scripts/get_weather.py "New York at 8 PM"
```
→ Returns hours around 8 PM with precipitation probability

**Air quality check:**
```
python3 ./scripts/get_weather.py "Los Angeles" --aqi
```
→ Returns weather + current/forecast AQI

**International location:**
```
python3 ./scripts/get_weather.py "Toronto, Canada"
```
→ Automatically uses wttr.in, notes it's non-US

## References

- [NWS API Reference](references/nws-api.md) — NWS API endpoint details
- [AirNow API Reference](references/airnow-api.md) — EPA AirNow API documentation
