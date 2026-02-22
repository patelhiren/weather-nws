---
name: weather-nws
description: "US weather forecasts via National Weather Service (NWS) with automatic fallback to global weather for non-US locations. Provides detailed accumulation data, watches/warnings, and actionable timing. Use for: US-based weather queries, winter storm forecasts, precipitation accumulation estimates, severe weather alerts. Automatically falls back to global weather via wttr.in for international locations."
homepage: https://api.weather.gov/
metadata: {"clawdhub":{"emoji":"🌦️"}}
---

# Weather NWS Skill

Get detailed US weather forecasts from the National Weather Service with automatic global fallback.

## When to Use

✅ **USE this skill when:**

- "What's the weather in [US city]?"
- "How much snow is expected?"
- "Winter storm forecast for [location]"
- "Will it rain tomorrow in [US city]?"
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
```

## Output Format

The script provides consistent output regardless of source:

**Header:** Location and current alert status
**Today → Tonight → Tomorrow:** Structured timeline
**Accumulation:** Specific snow/rain amounts when available
**Bottom Line:** Actionable summary with timing

## Implementation

The script handles:
1. Geocoding location to lat/long
2. Detecting if location is in US
3. Calling NWS API for US locations (detailed accumulation)
4. Falling back to wttr.in for non-US (basic forecast)
5. Formatting consistent output with emojis and structure

## Limitations

- **NWS:** US only, requires internet, rate limited
- **wttr.in:** Global, less detail on accumulation, no official watches/warnings

## Examples

**US winter storm query:**
```
python3 ./scripts/get_weather.py "Boston, MA"
```
→ Returns NWS data with accumulation estimates

**International location:**
```
python3 ./scripts/get_weather.py "Toronto, Canada"
```
→ Automatically uses wttr.in, notes it's non-US

## References

See [references/nws-api.md](references/nws-api.md) for NWS API endpoint details.
