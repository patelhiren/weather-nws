#!/usr/bin/env python3
"""
Unified weather fetcher with US (NWS) priority and global fallback (wttr.in)
Provides consistent, actionable output format.
"""

import sys
import json
import urllib.request
import urllib.parse
import subprocess
from datetime import datetime

def geocode_location(location):
    """Convert location string to lat/lon using Nominatim (OSM)"""
    try:
        encoded = urllib.parse.quote(location)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ClawdWeather/1.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon']), data[0].get('display_name', location)
    except Exception as e:
        print(f"Geocoding error: {e}", file=sys.stderr)
    return None, None, location

def is_us_location(lat, lon):
    """Check if coordinates are roughly within US bounds"""
    # US approximate bounds: lat 24-49, lon -125 to -66
    return 24 <= lat <= 49 and -125 <= lon <= -66

def get_nws_gridpoint(lat, lon):
    """Get NWS gridpoint for lat/lon"""
    try:
        url = f"https://api.weather.gov/points/{lat},{lon}"
        req = urllib.request.Request(url, headers={'User-Agent': 'ClawdWeather/1.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['properties']
    except Exception as e:
        print(f"NWS gridpoint error: {e}", file=sys.stderr)
    return None

def get_nws_forecast(gridpoint):
    """Get detailed forecast from NWS"""
    try:
        forecast_url = gridpoint.get('forecast')
        if not forecast_url:
            return None
            
        req = urllib.request.Request(forecast_url, headers={'User-Agent': 'ClawdWeather/1.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['properties']
    except Exception as e:
        print(f"NWS forecast error: {e}", file=sys.stderr)
    return None

def get_nws_alerts(gridpoint):
    """Get active alerts for the zone"""
    try:
        zone = gridpoint.get('forecastZone', '').split('/')[-1]
        if not zone:
            return []
            
        url = f"https://api.weather.gov/alerts/active?zone={zone}"
        req = urllib.request.Request(url, headers={'User-Agent': 'ClawdWeather/1.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('features', [])
    except Exception as e:
        print(f"NWS alerts error: {e}", file=sys.stderr)
    return []

def get_wttr_forecast(location):
    """Get forecast from wttr.in as fallback"""
    try:
        # Clean location for URL
        clean_loc = location.replace(' ', '+')
        
        # Get 3-day forecast in text format
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{clean_loc}?format=v2'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"wttr.in error: {e}", file=sys.stderr)
    return None

def get_wttr_current(location):
    """Get current conditions from wttr.in"""
    try:
        clean_loc = location.replace(' ', '+')
        
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{clean_loc}?format=%C|%t|%w|%h|%p'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            parts = result.stdout.strip().split('|')
            return {
                'condition': parts[0] if len(parts) > 0 else 'Unknown',
                'temp': parts[1] if len(parts) > 1 else '',
                'wind': parts[2] if len(parts) > 2 else '',
                'humidity': parts[3] if len(parts) > 3 else '',
                'precip': parts[4] if len(parts) > 4 else ''
            }
    except Exception as e:
        print(f"wttr.in current error: {e}", file=sys.stderr)
    return None

def format_nws_output(forecast, alerts, location_name):
    """Format NWS forecast into clean, actionable output"""
    output = []
    
    # Header with alerts
    if alerts:
        alert_titles = [a['properties']['event'] for a in alerts[:2]]
        output.append(f"🚨 **{location_name} — Alert Active**")
        output.append(f"⚠️  {', '.join(alert_titles)}")
    else:
        output.append(f"🌦️ **{location_name} Forecast**")
    
    output.append("")
    
    # Get periods (today, tonight, tomorrow)
    periods = forecast.get('periods', [])[:4]  # Get first 4 periods
    
    for period in periods:
        name = period.get('name', '')
        desc = period.get('detailedForecast', '')
        
        if not desc:
            continue
            
        # Emoji based on forecast
        icon = "🌤️"
        lower = desc.lower()
        if 'snow' in lower or 'blizzard' in lower:
            icon = "❄️"
        elif 'rain' in lower or 'shower' in lower:
            icon = "🌧️"
        elif 'sun' in lower or 'clear' in lower:
            icon = "☀️"
        elif 'cloud' in lower:
            icon = "☁️"
        elif 'wind' in lower or 'blowing' in lower:
            icon = "💨"
        
        output.append(f"**{icon} {name}**")
        output.append(desc)
        output.append("")
    
    # Bottom line if severe weather
    if alerts:
        output.append("**⚡ Bottom line:**")
        for alert in alerts[:1]:
            props = alert['properties']
            headline = props.get('headline', '')
            instr = props.get('instruction', '')
            if instr:
                # Take first sentence of instruction
                instr_short = instr.split('.')[0] + '.' if '.' in instr else instr[:100]
                output.append(f"{headline}")
                output.append(f"→ {instr_short}")
    
    return "\n".join(output)

def format_wttr_output(forecast_text, current, location_name):
    """Format wttr.in output into consistent structure"""
    output = []
    output.append(f"🌦️ **{location_name} Forecast** (Global source)")
    output.append("")
    
    if current:
        output.append(f"**Now:** {current.get('condition', '')} {current.get('temp', '')}")
        output.append(f"Wind: {current.get('wind', '')} | Humidity: {current.get('humidity', '')}")
        output.append("")
    
    if forecast_text:
        # Include the ASCII art forecast but note it's from global source
        output.append("**3-Day Outlook:**")
        output.append("```")
        output.append(forecast_text)
        output.append("```")
    else:
        output.append("*Forecast data unavailable for this location.*")
    
    return "\n".join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: get_weather.py 'Location Name' [--source nws|wttr|auto]")
        sys.exit(1)
    
    location = sys.argv[1]
    source_pref = 'auto'
    
    if '--source' in sys.argv:
        idx = sys.argv.index('--source')
        if idx + 1 < len(sys.argv):
            source_pref = sys.argv[idx + 1]
    
    # Step 1: Geocode
    lat, lon, display_name = geocode_location(location)
    
    if lat is None or lon is None:
        print(f"❌ Could not locate: {location}")
        sys.exit(1)
    
    # Step 2: Determine source
    use_nws = False
    if source_pref == 'nws':
        use_nws = True
    elif source_pref == 'wttr':
        use_nws = False
    elif source_pref == 'auto':
        use_nws = is_us_location(lat, lon)
    
    # Step 3: Fetch from appropriate source
    if use_nws:
        gridpoint = get_nws_gridpoint(lat, lon)
        
        if gridpoint:
            forecast = get_nws_forecast(gridpoint)
            alerts = get_nws_alerts(gridpoint)
            
            if forecast:
                print(format_nws_output(forecast, alerts, display_name))
                return
            else:
                print("⚠️  NWS forecast unavailable, falling back to global weather...")
        else:
            print("⚠️  NWS gridpoint not found, falling back to global weather...")
    
    # Step 4: Fallback to wttr.in
    forecast_text = get_wttr_forecast(location)
    current = get_wttr_current(location)
    
    if forecast_text or current:
        print(format_wttr_output(forecast_text, current, display_name))
    else:
        print(f"❌ Unable to fetch weather for: {location}")
        sys.exit(1)

if __name__ == '__main__':
    main()
