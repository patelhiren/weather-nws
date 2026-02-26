# AirNow API Reference

## Overview

The EPA AirNow API provides air quality index (AQI) data for US locations. AQI measures five major pollutants: ground-level ozone, particle pollution (PM2.5 and PM10), carbon monoxide, sulfur dioxide, and nitrogen dioxide.

**Base URL:** `https://api.airnowapi.org/`

**Official docs:** https://www.airnowapi.org/aq101/

## Authentication

**Optional API Key:** While some endpoints work without authentication, an API key is recommended for reliable access and higher rate limits.

**Get a key:** https://www.airnowapi.org/aq101/

**Environment variable:** Set `AIRNOW_API_KEY` for automatic use

```bash
export AIRNOW_API_KEY="your_api_key_here"
```

## Endpoints

### 1. Current Observations — Get current AQI

```
GET /aq/current/observation/latLong/
  ?latitude={lat}
  &longitude={lon}
  &format=application/json
  [&API_KEY={key}]
```

**Response:**
```json
[
  {
    "DateObserved": "2026-02-22",
    "HourObserved": 15,
    "LocalTimeZone": "EST",
    "ReportingArea": "Boston",
    "StateCode": "MA",
    "Latitude": 42.36,
    "Longitude": -71.05,
    "ParameterName": "PM2.5",
    "AQI": 45,
    "Category": {
      "Number": 1,
      "Name": "Good"
    }
  }
]
```

### 2. Forecast — Get predicted AQI

```
GET /aq/forecast/latLong/
  ?latitude={lat}
  &longitude={lon}
  &format=application/json
  [&API_KEY={key}]
```

**Response:**
```json
[
  {
    "DateIssue": "2026-02-22",
    "DateForecast": "2026-02-23",
    "ReportingArea": "Boston",
    "StateCode": "MA",
    "Latitude": 42.36,
    "Longitude": -71.05,
    "ParameterName": "PM2.5",
    "AQI": 52,
    "Category": {
      "Number": 2,
      "Name": "Moderate"
    },
    "ActionDay": false
  }
]
```

### 3. Historical — Get past observations

```
GET /aq/observation/latLong/historical/
  ?latitude={lat}
  &longitude={lon}
  &date={YYYY-MM-DD}
  &format=application/json
  [&API_KEY={key}]
```

## AQI Categories and Color Coding

| AQI Range | Category | Emoji | Color | Health Implication |
|-----------|----------|-------|-------|-------------------|
| 0–50 | Good | 🟢 | Green | Air quality is satisfactory; little to no risk |
| 51–100 | Moderate | 🟡 | Yellow | Acceptable for most; moderate concern for sensitive groups |
| 101–150 | Unhealthy for Sensitive Groups | 🟠 | Orange | Sensitive groups may experience health effects |
| 151–200 | Unhealthy | 🔴 | Red | Everyone may begin to experience health effects |
| 201–300 | Very Unhealthy | 🟣 | Purple | Health alert: risk of serious effects for everyone |
| 301–500 | Hazardous | 🔵 | Maroon | Emergency conditions: entire population likely affected |

## Pollutant Codes

| Code | Full Name | Primary Sources |
|------|-----------|-----------------|
| PM2.5 | Fine Particulate Matter | Vehicles, combustion, industry |
| PM10 | Coarse Particulate Matter | Dust, pollen, mold |
| O3 | Ground-Level Ozone | Sunlight + vehicle emissions |
| CO | Carbon Monoxide | Vehicle exhaust, fireplaces |
| SO2 | Sulfur Dioxide | Power plants, industry |
| NO2 | Nitrogen Dioxide | Vehicle exhaust, industry |

## Rate Limits

**With API key:** Higher limits, more reliable  
**Without key:** Lower limits, may be rate-limited

Recommend: 
- Cache current observations for ~1 hour
- Cache forecasts for ~6 hours
- Max 1 request/5 seconds

## Attribution

**Required:** When displaying AirNow data, include attribution:
> "Air quality data provided by the EPA AirNow program"

Or link to: https://www.airnow.gov/

## Limitations

1. **US only** — No international coverage
2. **Sparse coverage** — Rural areas may lack monitoring stations
3. **~Hourly updates** — Current data may be 30-60 minutes delayed
4. **Forecast accuracy** — Predictions vary; use as guidance only
5. **Single pollutant focus** — Primary AQI is the highest category among reported pollutants

## Error Handling

**No data available:**
```json
[]
```

**Invalid coordinates:** HTTP 400

**Rate limited:** HTTP 429

**Missing API key for some endpoints:** HTTP 401

## Example Usage

```python
import urllib.request
import json

lat, lon = 42.36, -71.05
url = f"https://api.airnowapi.org/aq/current/observation/latLong/?latitude={lat}&longitude={lon}&format=application/json"

req = urllib.request.Request(url, headers={'User-Agent': 'MyApp/1.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read())
    if data:
        aqi = data[0]['AQI']
        category = data[0]['Category']['Name']
        print(f"AQI: {aqi} - {category}")
```
