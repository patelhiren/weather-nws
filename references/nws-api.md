# NWS API Reference

## Overview

The National Weather Service API provides detailed US weather forecasts, alerts, and observations.

**Base URL:** `https://api.weather.gov/`

**Key Endpoints:**

1. **Point Lookup** — Get gridpoint for lat/lon
   - `GET /points/{latitude},{longitude}`
   - Returns: Gridpoint ID, forecast office, zone IDs

2. **Forecast** — Detailed text forecast
   - `GET /gridpoints/{office}/{gridX},{gridY}/forecast`
   - From point lookup → `forecast` property
\xa0
3. **Hourly Forecast** — Hour-by-hour data
   - `GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly`

4. **Active Alerts** — Watches/warnings
   - `GET /alerts/active?zone={zoneId}`
   - Zone from point lookup → `forecastZone`

## Response Structure

### Forecast Period Object

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
  "detailedForecast": "Snow. The snow could be heavy at times. Low around 29. Blustery...",
  "shortForecast": "Snow"
}
```

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

## Accumulation Data

Snow accumulation is embedded in `detailedForecast` as text:
- "New snow accumulation of 13 to 19 inches possible"
- "New precipitation amounts between a tenth and quarter of an inch"

No structured snow total fields exist — must parse from text.

## Rate Limiting

Recommend: Max 1 request/2 seconds. Cache gridpoints.

## User Agent

Required: Include `User-Agent` header with any identifier.
