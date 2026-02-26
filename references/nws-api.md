# NWS API Reference

## Overview

The National Weather Service API provides detailed US weather forecasts, alerts, and observations.

**Base URL:** `https://api.weather.gov/`

## Key Endpoints

### 1. Point Lookup — Get gridpoint for lat/lon
- `GET /points/{latitude},{longitude}`
- Returns: Gridpoint ID, forecast office, zone IDs

### 2. Forecast — Detailed 12-hour text forecast
- `GET /gridpoints/{office}/{gridX},{gridY}/forecast`
- From point lookup → `forecast` property
- Returns: ~7 periods (today, tonight, next few days)

### 3. **Hourly Forecast** — Hour-by-hour data
- `GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly`
- Returns: ~**156 periods** (7 days of hourly data)
- **Use for:** Precise timing queries ("at 8 PM", "tonight at")

### 4. **Grid Data** — Structured raw forecast data
- `GET /gridpoints/{office}/{gridX},{gridY}`
- Returns: Raw grid values without text interpretation
- **Use for:** Structured accumulations (snowfall, ice, precip probability)

### 5. Active Alerts — Watches/warnings
- `GET /alerts/active?zone={zoneId}`
- Zone from point lookup → `forecastZone`

## Response Structure

### Standard Forecast Period Object

```json
{
  "name": "Tonight",
  "startTime": "2026-02-22T18:00:00-05:00",
  "endTime": "2026-02-23T06:00:00-05:00",
  "isDaytime": false,
  "temperature": 29,
  "temperatureUnit": "F",
  "probabilityOfPrecipitation": {
    "value": 100,
    "unitCode": "percent"
  },
  "detailedForecast": "Snow. The snow could be heavy at times. Low around 29...",
  "shortForecast": "Snow"
}
```

### Hourly Forecast Period Object

```json
{
  "startTime": "2026-02-22T18:00:00-05:00",
  "endTime": "2026-02-22T19:00:00-05:00",
  "isDaytime": false,
  "temperature": 29,
  "windSpeed": "15 mph",
  "windDirection": "NE",
  "shortForecast": "Snow",
  "probabilityOfPrecipitation": {
    "value": 95,
    "unitCode": "percent"
  }
}
```

### Grid Data Object (Structured Accumulations)

```json
{
  "properties": {
    "probabilityOfPrecipitation": {
      "uom": "wmoUnit:percent",
      "values": [
        {"validTime": "2026-02-22T18:00:00+00:00/PT1H", "value": 95},
        {"validTime": "2026-02-22T19:00:00+00:00/PT1H", "value": 90}
      ]
    },
    "snowfallAmount": {
      "uom": "wmoUnit:m",
      "values": [
        {"validTime": "2026-02-22T18:00:00+00:00/PT6H", "value": 0.2032},
        {"validTime": "2026-02-23T00:00:00+00:00/PT6H", "value": 0.254}
      ]
    },
    "iceAccumulation": {
      "uom": "wmoUnit:m",
      "values": [
        {"validTime": "2026-02-22T18:00:00+00:00/PT6H", "value": 0.00254}
      ]
    },
    "quantitativePrecipitation": {
      "uom": "wmoUnit:m",
      "values": [
        {"validTime": "2026-02-22T18:00:00+00:00/PT6H", "value": 0.01524}
      ]
    }
  }
}
```

**Key grid data fields:**
| Field | Unit | Description |
|-------|------|-------------|
| `probabilityOfPrecipitation` | percent | Chance of precipitation (0-100) |
| `snowfallAmount` | meters | Snow accumulation (convert to inches × 39.37) |
| `iceAccumulation` | meters | Ice accumulation (convert to inches × 39.37) |
| `quantitativePrecipitation` | meters | Liquid precipitation amount |

### Alert Object

```json
{
  "properties": {
    "event": "Winter Storm Warning",
    "headline": "Winter Storm Warning issued February 21 at 9:45PM EST...",
    "instruction": "Travel could be very difficult to impossible...",
    "severity": "Severe",
    "urgency": "Expected"
  }
}
```

## Hourly Forecast Details

**Endpoint:** `/gridpoints/{wfo}/{x},{y}/forecast/hourly`

**Returns:** ~156 periods (7 days × 24 hours)

**Use cases:**
- "What time does the rain start?"
- "Will it be snowing at 8 PM?"
- "When will the precipitation stop?"

**Limitations:**
- Hourly data may have gaps for some forecast offices
- Max 7 days forward
- Temperature unit matches office preference (usually F)

## Structured Grid Data Details

**Endpoint:** `/gridpoints/{wfo}/{x},{y}`

**Use for:** Precise accumulation amounts without parsing text

**Unit conversion:**
- Meters to inches: `value × 39.37`
- Example: 0.2032m snow = 8 inches

**Time format:** ISO 8601 with duration
- `2026-02-22T18:00:00+00:00/PT6H` = 6-hour period starting at 18:00 UTC

## Rate Limiting

Recommend: Max 1 request/2 seconds. Cache gridpoints.

**Be nice:**
- Don't hammer the API
- Cache point lookups (they rarely change)
- Respect HTTP errors and back off

## User Agent

Required: Include `User-Agent` header with any identifier.

Example: `User-Agent: ClawdWeather/1.0`
