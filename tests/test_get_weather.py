#!/usr/bin/env python3
"""
Comprehensive unit tests for get_weather.py
Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import get_weather as gw


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(payload):
    body = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _mock_urlopen_text(text):
    mock_resp = MagicMock()
    mock_resp.read.return_value = text.encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _nominatim_response(lat, lon, name):
    return [{"lat": str(lat), "lon": str(lon), "display_name": name}]


def _make_alert(severity="Severe", urgency="Immediate", certainty="Observed",
                event="Winter Storm Warning", headline="Winter Storm Warning",
                description="Heavy snow expected.", instruction="Stay off roads.",
                onset="2026-03-04T06:00:00-05:00", expires="2026-03-05T12:00:00-05:00",
                response="Prepare"):
    return {
        "properties": {
            "event": event, "severity": severity, "urgency": urgency,
            "certainty": certainty, "headline": headline, "description": description,
            "instruction": instruction, "onset": onset, "expires": expires,
            "response": response,
        }
    }


def _make_nws_periods(n=4):
    return [
        {
            "name": f"Period {i+1}",
            "detailedForecast": "Sunny with a high near 60.",
            "shortForecast": "Sunny",
            "temperature": 60 + i,
            "temperatureUnit": "F",
            "windSpeed": "10 mph",
            "windDirection": "NW",
            "startTime": f"2026-03-0{i+3}T06:00:00-05:00",
        }
        for i in range(n)
    ]


def _make_hourly_periods(n=24):
    base = datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc)
    return [
        {
            "startTime": (base + timedelta(hours=i)).isoformat(),
            "temperature": 55 + i % 10,
            "temperatureUnit": "F",
            "shortForecast": "Partly Cloudy",
            "probabilityOfPrecipitation": {"value": 10},
            "windSpeed": "8 mph",
            "windDirection": "W",
        }
        for i in range(n)
    ]


_NWS_GRIDPOINT_PROPS = {
    "gridId": "OKX",
    "gridX": 34,
    "gridY": 38,
    "forecast": "https://api.weather.gov/gridpoints/OKX/34,38/forecast",
    "forecastHourly": "https://api.weather.gov/gridpoints/OKX/34,38/forecast/hourly",
    "forecastGridData": "https://api.weather.gov/gridpoints/OKX/34,38",
    "observationStations": "https://api.weather.gov/gridpoints/OKX/34,38/stations",
    "forecastZone": "https://api.weather.gov/zones/forecast/NYZ072",
    "fireWeatherZone": "https://api.weather.gov/zones/fire/NYZ072",
    "astronomicalData": {
        "sunrise": "2026-03-03T06:30:00-05:00",
        "sunset": "2026-03-03T18:30:00-05:00",
        "civilTwilightBegin": "2026-03-03T06:05:00-05:00",
        "civilTwilightEnd": "2026-03-03T18:55:00-05:00",
    }
}

_NWS_STATIONS = {
    "features": [{"properties": {"stationIdentifier": "KJFK"}}]
}

_NWS_OBSERVATION = {
    "properties": {
        "temperature": {"value": 15.0, "unitCode": "wmoUnit:degC"},
        "windSpeed": {"value": 20.0, "unitCode": "wmoUnit:km_h-1"},
        "windDirection": {"value": 270.0},
        "relativeHumidity": {"value": 65.0},
        "dewpoint": {"value": 8.0, "unitCode": "wmoUnit:degC"},
        "barometricPressure": {"value": 101325.0},
        "visibility": {"value": 16000.0},
        "textDescription": "Mostly Cloudy",
    }
}


# ---------------------------------------------------------------------------
# 1. US Location Detection
# ---------------------------------------------------------------------------

class TestIsUsLocation(unittest.TestCase):

    def test_conus_center(self):
        self.assertTrue(gw.is_us_location(39.0, -98.0))   # Kansas

    def test_conus_northeast(self):
        self.assertTrue(gw.is_us_location(40.7, -74.0))   # New York

    def test_conus_west(self):
        self.assertTrue(gw.is_us_location(34.0, -118.2))  # Los Angeles

    def test_conus_south(self):
        self.assertTrue(gw.is_us_location(29.7, -95.4))   # Houston

    def test_alaska(self):
        self.assertTrue(gw.is_us_location(61.2, -149.9))  # Anchorage

    def test_hawaii(self):
        self.assertTrue(gw.is_us_location(21.3, -157.8))  # Honolulu

    def test_non_us_korea(self):
        self.assertFalse(gw.is_us_location(37.5, 127.0))  # Seoul

    def test_non_us_uk(self):
        self.assertFalse(gw.is_us_location(51.5, -0.1))   # London

    def test_non_us_australia(self):
        self.assertFalse(gw.is_us_location(-33.9, 151.2)) # Sydney

    def test_non_us_northern_canada(self):
        self.assertFalse(gw.is_us_location(60.0, -100.0)) # Canada (north of CONUS)

    def test_boundary_conus_south(self):
        self.assertTrue(gw.is_us_location(24.5, -80.0))   # Florida Keys area


# ---------------------------------------------------------------------------
# 2. Temporal Query Detection
# ---------------------------------------------------------------------------

class TestIsTemporalQuery(unittest.TestCase):

    def test_tonight(self):
        self.assertTrue(gw.is_temporal_query("Chicago tonight"))

    def test_tonight_at_time(self):
        self.assertTrue(gw.is_temporal_query("NYC tonight at 9"))

    def test_tomorrow_morning(self):
        self.assertTrue(gw.is_temporal_query("Seattle tomorrow morning"))

    def test_tomorrow_afternoon(self):
        self.assertTrue(gw.is_temporal_query("Denver tomorrow afternoon"))

    def test_tomorrow_night(self):
        self.assertTrue(gw.is_temporal_query("Austin tomorrow night"))

    def test_tomorrow_generic(self):
        self.assertTrue(gw.is_temporal_query("Miami tomorrow"))

    def test_at_time_ampm(self):
        self.assertTrue(gw.is_temporal_query("Boston at 8 PM"))

    def test_time_ampm_no_at(self):
        self.assertTrue(gw.is_temporal_query("Boston 6am"))

    def test_when_will(self):
        self.assertTrue(gw.is_temporal_query("when will it stop raining in Austin"))

    def test_stop_raining(self):
        self.assertTrue(gw.is_temporal_query("Boston stop raining"))

    def test_start_snowing(self):
        self.assertTrue(gw.is_temporal_query("Denver start snowing"))

    def test_hhmm_format(self):
        self.assertTrue(gw.is_temporal_query("Boston 14:30"))

    def test_plain_city_not_temporal(self):
        self.assertFalse(gw.is_temporal_query("Chicago, IL"))

    def test_plain_with_state(self):
        self.assertFalse(gw.is_temporal_query("Portland, OR"))

    def test_five_digit_zip_not_temporal(self):
        self.assertFalse(gw.is_temporal_query("90210"))


# ---------------------------------------------------------------------------
# 3. Strip Temporal Qualifiers
# ---------------------------------------------------------------------------

class TestStripTemporalQualifiers(unittest.TestCase):

    def test_strips_tonight(self):
        result = gw.strip_temporal_qualifiers("Chicago tonight")
        self.assertNotIn("tonight", result.lower())
        self.assertIn("Chicago", result)

    def test_strips_tomorrow_morning(self):
        result = gw.strip_temporal_qualifiers("Seattle tomorrow morning")
        self.assertNotIn("tomorrow morning", result.lower())

    def test_strips_at_time(self):
        result = gw.strip_temporal_qualifiers("Boston at 8 PM")
        self.assertNotIn("at 8 PM", result)

    def test_preserves_plain_city(self):
        result = gw.strip_temporal_qualifiers("Portland, OR")
        self.assertEqual(result.strip(), "Portland, OR")

    def test_strips_tomorrow(self):
        result = gw.strip_temporal_qualifiers("Denver tomorrow")
        self.assertNotIn("tomorrow", result.lower())


# ---------------------------------------------------------------------------
# 4. Geocode Location
# ---------------------------------------------------------------------------

class TestGeocodeLocation(unittest.TestCase):

    def test_plain_city(self):
        payload = _nominatim_response(41.88, -87.63, "Chicago, IL, USA")
        with patch('urllib.request.urlopen', return_value=_mock_urlopen(payload)):
            lat, lon, name = gw.geocode_location("Chicago, IL")
        self.assertAlmostEqual(lat, 41.88)
        self.assertAlmostEqual(lon, -87.63)
        self.assertEqual(name, "Chicago, IL, USA")

    def test_zip_appends_usa(self):
        """Bare 5-digit zip must be sent to Nominatim with ', USA' appended."""
        payload = _nominatim_response(34.09, -118.36, "90210, Beverly Hills, CA, USA")
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured['url'] = req.full_url if hasattr(req, 'full_url') else str(req)
            return _mock_urlopen(payload)

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            lat, lon, _ = gw.geocode_location("90210")

        self.assertIn("USA", captured['url'])
        self.assertAlmostEqual(lat, 34.09)

    def test_zip_plus4_appends_usa(self):
        payload = _nominatim_response(34.09, -118.36, "90210, Beverly Hills, CA, USA")
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured['url'] = req.full_url if hasattr(req, 'full_url') else str(req)
            return _mock_urlopen(payload)

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            gw.geocode_location("90210-1234")

        self.assertIn("USA", captured['url'])

    def test_zip_with_state_not_further_modified(self):
        """'90210, CA' is not a bare zip — regex should not match it."""
        payload = _nominatim_response(34.09, -118.36, "Beverly Hills, CA, USA")
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured['url'] = req.full_url if hasattr(req, 'full_url') else str(req)
            return _mock_urlopen(payload)

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            gw.geocode_location("90210, CA")

        # Should NOT double-append USA
        self.assertNotIn("USA%2C+USA", captured['url'])

    def test_empty_nominatim_response_returns_none(self):
        with patch('urllib.request.urlopen', return_value=_mock_urlopen([])):
            lat, lon, name = gw.geocode_location("UnknownPlaceXYZ")
        self.assertIsNone(lat)
        self.assertIsNone(lon)

    def test_network_error_returns_none(self):
        with patch('urllib.request.urlopen', side_effect=Exception("network error")):
            lat, lon, name = gw.geocode_location("Chicago")
        self.assertIsNone(lat)
        self.assertIsNone(lon)


# ---------------------------------------------------------------------------
# 5. Unit Conversions
# ---------------------------------------------------------------------------

class TestUnitConversions(unittest.TestCase):

    # Celsius → Fahrenheit
    def test_c_to_f_freezing(self):
        self.assertAlmostEqual(gw.convert_c_to_f(0), 32.0)

    def test_c_to_f_boiling(self):
        self.assertAlmostEqual(gw.convert_c_to_f(100), 212.0)

    def test_c_to_f_body_temp(self):
        self.assertAlmostEqual(gw.convert_c_to_f(37), 98.6, places=1)

    def test_c_to_f_negative(self):
        self.assertAlmostEqual(gw.convert_c_to_f(-40), -40.0)

    def test_c_to_f_none(self):
        self.assertIsNone(gw.convert_c_to_f(None))

    # Pascals → inHg
    def test_pa_to_inhg_standard_atmosphere(self):
        self.assertAlmostEqual(gw.convert_pa_to_inhg(101325), 29.92, places=1)

    def test_pa_to_inhg_none(self):
        self.assertIsNone(gw.convert_pa_to_inhg(None))

    # km/h → mph
    def test_kmh_to_mph(self):
        self.assertAlmostEqual(gw.convert_kmh_to_mph(100), 62.14, places=1)

    def test_kmh_to_mph_zero(self):
        self.assertAlmostEqual(gw.convert_kmh_to_mph(0), 0.0)

    def test_kmh_to_mph_none(self):
        self.assertIsNone(gw.convert_kmh_to_mph(None))

    # Meters → miles
    def test_meters_to_miles(self):
        self.assertAlmostEqual(gw.convert_meters_to_miles(1609.34), 1.0, places=2)

    def test_meters_to_miles_none(self):
        self.assertIsNone(gw.convert_meters_to_miles(None))

    # Wind direction degrees → cardinal
    def test_wind_north_0(self):
        self.assertEqual(gw.wind_direction_to_cardinal(0), "N")

    def test_wind_north_360(self):
        self.assertEqual(gw.wind_direction_to_cardinal(360), "N")

    def test_wind_east(self):
        self.assertEqual(gw.wind_direction_to_cardinal(90), "E")

    def test_wind_south(self):
        self.assertEqual(gw.wind_direction_to_cardinal(180), "S")

    def test_wind_west(self):
        self.assertEqual(gw.wind_direction_to_cardinal(270), "W")

    def test_wind_northeast(self):
        self.assertEqual(gw.wind_direction_to_cardinal(45), "NE")

    def test_wind_southwest(self):
        self.assertEqual(gw.wind_direction_to_cardinal(225), "SW")

    def test_wind_nne(self):
        self.assertEqual(gw.wind_direction_to_cardinal(22.5), "NNE")

    # Unit → inches
    def test_mm_to_inches(self):
        self.assertAlmostEqual(gw.convert_to_inches(25.4, "mm"), 1.0, places=3)

    def test_cm_to_inches(self):
        self.assertAlmostEqual(gw.convert_to_inches(2.54, "cm"), 1.0, places=3)

    def test_m_to_inches(self):
        self.assertAlmostEqual(gw.convert_to_inches(0.0254, "m"), 1.0, places=2)

    def test_zero_value_returns_zero(self):
        self.assertEqual(gw.convert_to_inches(0, "mm"), 0)

    def test_negative_value_returns_zero(self):
        self.assertEqual(gw.convert_to_inches(-5, "mm"), 0)


# ---------------------------------------------------------------------------
# 6. AQI
# ---------------------------------------------------------------------------

class TestAQICategory(unittest.TestCase):

    def test_good(self):
        cat = gw.parse_aqi_category(25)
        self.assertEqual(cat['name'], "Good")
        self.assertEqual(cat['emoji'], "🟢")

    def test_moderate(self):
        self.assertEqual(gw.parse_aqi_category(75)['name'], "Moderate")

    def test_unhealthy_for_sensitive(self):
        self.assertIn("Sensitive", gw.parse_aqi_category(125)['name'])

    def test_unhealthy(self):
        self.assertEqual(gw.parse_aqi_category(175)['name'], "Unhealthy")

    def test_very_unhealthy(self):
        self.assertEqual(gw.parse_aqi_category(250)['name'], "Very Unhealthy")

    def test_hazardous(self):
        self.assertEqual(gw.parse_aqi_category(400)['name'], "Hazardous")

    def test_boundary_50_is_good(self):
        self.assertEqual(gw.parse_aqi_category(50)['name'], "Good")

    def test_boundary_51_is_moderate(self):
        self.assertEqual(gw.parse_aqi_category(51)['name'], "Moderate")

    def test_boundary_100_is_moderate(self):
        self.assertEqual(gw.parse_aqi_category(100)['name'], "Moderate")

    def test_boundary_101_is_sensitive(self):
        self.assertIn("Sensitive", gw.parse_aqi_category(101)['name'])


class TestFormatAQIOutput(unittest.TestCase):

    def test_with_current_data(self):
        current = [{"AQI": 42, "Category": {"Name": "Good"}, "ParameterName": "PM2.5"}]
        output = gw.format_aqi_output(current, [], "Chicago, IL")
        self.assertIn("42", output)
        self.assertIn("PM2.5", output)
        self.assertIn("Chicago", output)

    def test_empty_data(self):
        output = gw.format_aqi_output([], [], "Denver, CO")
        self.assertIn("Denver", output)

    def test_with_forecast(self):
        current = [{"AQI": 55, "Category": {"Name": "Moderate"}, "ParameterName": "Ozone"}]
        forecast = [
            {"AQI": 60, "Category": {"Name": "Moderate"}, "DateForecast": "2026-03-04"},
            {"AQI": 45, "Category": {"Name": "Good"}, "DateForecast": "2026-03-05"},
        ]
        output = gw.format_aqi_output(current, forecast, "Denver, CO")
        self.assertIn("Ozone", output)
        self.assertIn("Denver", output)

    def test_forecast_minus_one_filtered(self):
        """AQI -1 sentinel values (no data) must not appear in output."""
        current = [{"AQI": 20, "Category": {"Name": "Good"}, "ParameterName": "PM2.5"}]
        forecast = [
            {"AQI": -1, "Category": {"Name": "Good"}, "DateForecast": "2026-03-04"},
            {"AQI": -1, "Category": {"Name": "Good"}, "DateForecast": "2026-03-05"},
        ]
        output = gw.format_aqi_output(current, forecast, "Seattle, WA")
        self.assertNotIn("-1", output)
        self.assertNotIn("Forecast:", output)


# ---------------------------------------------------------------------------
# 7. Alerts
# ---------------------------------------------------------------------------

class TestAlertPriority(unittest.TestCase):

    def test_extreme_immediate_observed(self):
        alert = _make_alert(severity="Extreme", urgency="Immediate", certainty="Observed")
        self.assertEqual(gw.calculate_alert_priority(alert['properties']), 10)

    def test_minor_future_possible(self):
        alert = _make_alert(severity="Minor", urgency="Future", certainty="Possible")
        self.assertEqual(gw.calculate_alert_priority(alert['properties']), 3)

    def test_all_unknown(self):
        alert = _make_alert(severity="Unknown", urgency="Unknown", certainty="Unknown")
        self.assertEqual(gw.calculate_alert_priority(alert['properties']), 0)

    def test_sort_descending(self):
        low  = _make_alert(severity="Minor",   urgency="Future",     certainty="Possible")
        high = _make_alert(severity="Extreme", urgency="Immediate",  certainty="Observed")
        med  = _make_alert(severity="Moderate",urgency="Expected",   certainty="Likely")
        sorted_alerts = gw.sort_alerts_by_priority([low, high, med])
        priorities = [gw.calculate_alert_priority(a['properties']) for a in sorted_alerts]
        self.assertEqual(priorities, sorted(priorities, reverse=True))


class TestFormatAlerts(unittest.TestCase):

    def test_format_alert_contains_event(self):
        alert = _make_alert(event="Tornado Warning")
        output = gw.format_alert(alert)
        self.assertIn("Tornado Warning", output)

    def test_format_alert_contains_description(self):
        alert = _make_alert(description="Dangerous winds expected.")
        output = gw.format_alert(alert)
        self.assertIn("Dangerous winds", output)

    def test_format_alert_extreme_badge(self):
        alert = _make_alert(severity="Extreme")
        output = gw.format_alert(alert)
        self.assertIn("EXTREME", output)

    def test_format_enhanced_alerts_empty_is_falsy(self):
        output = gw.format_enhanced_alerts([])
        self.assertFalse(output)  # None or "" both pass

    def test_format_enhanced_alerts_high_priority_first(self):
        low  = _make_alert(severity="Minor",   event="Small Craft Advisory")
        high = _make_alert(severity="Extreme", event="Tornado Warning")
        output = gw.format_enhanced_alerts([low, high])
        self.assertLess(output.index("Tornado"), output.index("Small Craft"))

    def test_fire_alert_appears_in_fire_output(self):
        fire_alert = _make_alert(event="Red Flag Warning", description="Extreme fire danger.")
        output = gw.format_fire_weather_output(None, [fire_alert], "Los Angeles, CA")
        self.assertIn("Red Flag", output)


# ---------------------------------------------------------------------------
# 8. Moon Phase & Astronomical
# ---------------------------------------------------------------------------

class TestMoonPhase(unittest.TestCase):
    # Reference: Jan 6 2000 18:14 UTC was a new moon.
    # Lunar cycle = 29.53059 days. Phase index = int(elapsed/cycle * 8).
    NEW_MOON = datetime(2000, 1, 6, 18, 14)

    def test_new_moon_phase_0(self):
        result = gw.calculate_moon_phase(self.NEW_MOON)
        self.assertEqual(result['phase'], 0)
        self.assertAlmostEqual(result['illumination'], 0.0, places=0)

    def test_first_quarter_at_8_days(self):
        result = gw.calculate_moon_phase(self.NEW_MOON + timedelta(days=8.0))
        self.assertEqual(result['phase'], 2)
        self.assertAlmostEqual(result['illumination'], 50.0, places=0)

    def test_full_moon_at_15_days(self):
        result = gw.calculate_moon_phase(self.NEW_MOON + timedelta(days=15.0))
        self.assertEqual(result['phase'], 4)
        self.assertAlmostEqual(result['illumination'], 100.0, places=0)

    def test_last_quarter_at_22_days(self):
        result = gw.calculate_moon_phase(self.NEW_MOON + timedelta(days=22.0))
        self.assertEqual(result['phase'], 5)  # Waning gibbous
        self.assertAlmostEqual(result['illumination'], 75.0, places=0)

    def test_illumination_always_in_range(self):
        for days in range(30):
            result = gw.calculate_moon_phase(self.NEW_MOON + timedelta(days=days))
            self.assertGreaterEqual(result['illumination'], 0)
            self.assertLessEqual(result['illumination'], 100)

    def test_phase_always_0_to_7(self):
        for days in range(30):
            result = gw.calculate_moon_phase(self.NEW_MOON + timedelta(days=days))
            self.assertGreaterEqual(result['phase'], 0)
            self.assertLessEqual(result['phase'], 7)

    def test_iso_string_input(self):
        result = gw.calculate_moon_phase("2000-01-06T18:14:00")
        self.assertEqual(result['phase'], 0)

    def test_returns_name(self):
        result = gw.calculate_moon_phase(self.NEW_MOON)
        self.assertIn('name', result)
        self.assertGreater(len(result['name']), 0)


class TestDaylightAndAstro(unittest.TestCase):

    def test_12_hour_daylight(self):
        result = gw.calculate_daylight_hours(
            "2026-03-03T06:30:00-05:00",
            "2026-03-03T18:30:00-05:00"
        )
        self.assertIn("12", result)

    def test_short_daylight(self):
        result = gw.calculate_daylight_hours(
            "2026-12-21T07:15:00-05:00",
            "2026-12-21T16:30:00-05:00"
        )
        self.assertIn("9", result)

    def test_format_astronomical_has_sunrise_sunset_moon(self):
        astro = {
            "sunrise": "2026-03-03T06:30:00-05:00",
            "sunset": "2026-03-03T18:30:00-05:00",
            "civilTwilightBegin": "2026-03-03T06:05:00-05:00",
            "civilTwilightEnd": "2026-03-03T18:55:00-05:00",
        }
        output = gw.format_astronomical_output(astro, "Denver, CO")
        self.assertIn("Sunrise", output)
        self.assertIn("Sunset", output)
        self.assertIn("Moon", output)

    def test_get_astronomical_data_from_gridpoint(self):
        result = gw.get_astronomical_data(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)
        self.assertIn('sunrise', result)
        self.assertIn('sunset', result)

    def test_get_astronomical_data_missing_returns_none(self):
        props = {k: v for k, v in _NWS_GRIDPOINT_PROPS.items() if k != 'astronomicalData'}
        result = gw.get_astronomical_data(props)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 9. DateTime Formatting
# ---------------------------------------------------------------------------

class TestDateTimeFormatting(unittest.TestCase):

    def test_parse_iso_basic(self):
        dt = gw.parse_iso_datetime("2026-03-03T12:00:00")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.hour, 12)

    def test_parse_iso_with_offset(self):
        dt = gw.parse_iso_datetime("2026-03-03T06:30:00-05:00")
        self.assertEqual(dt.hour, 6)

    def test_format_simple_time_morning(self):
        result = gw.format_simple_time("2026-03-03T06:30:00-05:00")
        self.assertIn("6:30", result)
        self.assertIn("AM", result.upper())

    def test_format_simple_time_afternoon(self):
        result = gw.format_simple_time("2026-03-03T14:45:00-05:00")
        self.assertIn("2:45", result)
        self.assertIn("PM", result.upper())

    def test_format_simple_time_noon(self):
        result = gw.format_simple_time("2026-03-03T12:00:00-05:00")
        self.assertIn("12:00", result)

    def test_format_time_until_hours(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=2, minutes=30)).isoformat()
        result = gw.format_time_until(future)
        self.assertIn("in", result.lower())
        self.assertIn("2h", result)

    def test_format_time_until_past(self):
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        result = gw.format_time_until(past)
        self.assertIn("ago", result.lower())

    def test_format_time_until_multi_day(self):
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        result = gw.format_time_until(future)
        # Format is "Xd Yh" — just verify "d" is present
        self.assertIn("d", result)
        self.assertIn("in", result.lower())


# ---------------------------------------------------------------------------
# 10. Parse Target Time
# ---------------------------------------------------------------------------

class TestParseTargetTime(unittest.TestCase):

    @patch('get_weather.datetime')
    def test_parse_8pm(self, mock_dt):
        now = datetime(2026, 3, 3, 10, 0)
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = gw.parse_target_time("Chicago at 8 PM")
        if result:
            self.assertEqual(result.hour, 20)

    @patch('get_weather.datetime')
    def test_parse_tonight(self, mock_dt):
        now = datetime(2026, 3, 3, 10, 0)
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = gw.parse_target_time("Chicago tonight")
        if result:
            self.assertEqual(result.hour, 20)

    @patch('get_weather.datetime')
    def test_parse_tomorrow_morning(self, mock_dt):
        now = datetime(2026, 3, 3, 10, 0)
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = gw.parse_target_time("Seattle tomorrow morning")
        if result:
            self.assertEqual(result.day, 4)
            self.assertEqual(result.hour, 8)

    @patch('get_weather.datetime')
    def test_parse_tomorrow_afternoon(self, mock_dt):
        now = datetime(2026, 3, 3, 10, 0)
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = gw.parse_target_time("Denver tomorrow afternoon")
        if result:
            self.assertEqual(result.day, 4)
            self.assertEqual(result.hour, 14)

    @patch('get_weather.datetime')
    def test_parse_tomorrow_night(self, mock_dt):
        now = datetime(2026, 3, 3, 10, 0)
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = gw.parse_target_time("Austin tomorrow night")
        if result:
            self.assertEqual(result.day, 4)
            self.assertEqual(result.hour, 20)


# ---------------------------------------------------------------------------
# 11. TAF Decoding
# ---------------------------------------------------------------------------

class TestTAFDecoding(unittest.TestCase):

    def test_directional_wind(self):
        result = gw.decode_taf_wind("27012KT")
        self.assertIn("12", result)
        self.assertIn("kt", result.lower())

    def test_variable_wind(self):
        result = gw.decode_taf_wind("VRB05KT")
        self.assertIn("Variable", result)
        self.assertIn("5", result)

    def test_gusting_wind(self):
        result = gw.decode_taf_wind("18025G35KT")
        self.assertIn("25", result)
        self.assertIn("35", result)

    def test_calm_wind(self):
        result = gw.decode_taf_wind("00000KT")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_taf_with_data(self):
        taf = {
            "stationId": "KJFK",
            "rawTAF": "TAF KJFK 031730Z 0318/0418 27012KT P6SM SCT050",
        }
        output = gw.format_taf_output(taf, "New York, NY")
        self.assertIn("KJFK", output)

    def test_format_taf_none_returns_string(self):
        output = gw.format_taf_output(None, "New York, NY")
        self.assertIsInstance(output, str)


# ---------------------------------------------------------------------------
# 12. Accumulations
# ---------------------------------------------------------------------------

class TestAccumulations(unittest.TestCase):

    def _snow_grid(self, value):
        return {
            'snowfallAmount': {
                'values': [{
                    'validTime': '2026-03-04T06:00:00+00:00/PT6H',
                    'value': value,
                    'unitCode': 'wmoUnit:mm'
                }]
            }
        }

    def _ice_grid(self, value):
        return {
            'iceAccumulation': {
                'values': [{
                    'validTime': '2026-03-04T06:00:00+00:00/PT6H',
                    'value': value,
                    'unitCode': 'wmoUnit:mm'
                }]
            }
        }

    def _precip_grid(self, pct):
        return {
            'probabilityOfPrecipitation': {
                'values': [{
                    'validTime': '2026-03-04T06:00:00+00:00/PT6H',
                    'value': pct,
                    'unitCode': 'wmoUnit:percent'
                }]
            }
        }

    def test_snow_above_threshold_included(self):
        result = gw.extract_accumulations_from_grid(self._snow_grid(10.0))
        snow = [r for r in result if 'Snow' in r.get('type', '')]
        self.assertTrue(len(snow) > 0)

    def test_snow_zero_filtered(self):
        result = gw.extract_accumulations_from_grid(self._snow_grid(0.0))
        snow = [r for r in result if 'Snow' in r.get('type', '')]
        self.assertEqual(len(snow), 0)

    def test_ice_above_threshold_included(self):
        result = gw.extract_accumulations_from_grid(self._ice_grid(5.0))
        ice = [r for r in result if 'Ice' in r.get('type', '')]
        self.assertTrue(len(ice) > 0)

    def test_ice_zero_filtered(self):
        result = gw.extract_accumulations_from_grid(self._ice_grid(0.0))
        ice = [r for r in result if 'Ice' in r.get('type', '')]
        self.assertEqual(len(ice), 0)

    def test_high_precip_probability_included(self):
        result = gw.extract_accumulations_from_grid(self._precip_grid(80))
        precip = [r for r in result if 'Precip' in r.get('type', '')]
        self.assertTrue(len(precip) > 0)

    def test_low_precip_probability_filtered(self):
        result = gw.extract_accumulations_from_grid(self._precip_grid(20))
        precip = [r for r in result if 'Precip' in r.get('type', '')]
        self.assertEqual(len(precip), 0)

    def test_parse_text_snow_accumulation(self):
        # Pattern: "snow accumulation of X inches" (singular, lowercase)
        periods = [{"detailedForecast": "snow accumulation of 4 to 6 inches expected overnight."}]
        result = gw.parse_accumulations_from_text(periods)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['type'], 'Snow')

    def test_parse_text_new_snow(self):
        periods = [{"detailedForecast": "new snow 3 inches possible by morning."}]
        result = gw.parse_accumulations_from_text(periods)
        self.assertTrue(len(result) > 0)

    def test_parse_text_no_match_returns_empty(self):
        periods = [{"detailedForecast": "Sunny and warm with highs near 75."}]
        result = gw.parse_accumulations_from_text(periods)
        self.assertEqual(result, [])

    def test_format_accumulations_with_data(self):
        accum = [{'type': 'Snowfall', 'amount': 0.5, 'unit': 'in',
                  'time': '2026-03-04T06:00:00+00:00', 'icon': '❄️'}]
        output = gw.format_accumulations_output(accum, "Denver, CO")
        self.assertIn("Snow", output)
        self.assertIn("0.5", output)

    def test_format_accumulations_empty(self):
        output = gw.format_accumulations_output([], "Denver, CO")
        self.assertIn("Denver", output)


# ---------------------------------------------------------------------------
# 13. Forecast Emoji
# ---------------------------------------------------------------------------

class TestFormatPeriodEmoji(unittest.TestCase):

    def test_sunny(self):
        self.assertEqual(gw.format_period_emoji("Sunny"), "☀️")

    def test_clear(self):
        self.assertEqual(gw.format_period_emoji("Clear"), "☀️")

    def test_snow(self):
        self.assertEqual(gw.format_period_emoji("Heavy Snow"), "❄️")

    def test_rain(self):
        self.assertEqual(gw.format_period_emoji("Rain likely"), "🌧️")

    def test_thunderstorm(self):
        self.assertEqual(gw.format_period_emoji("Thunderstorms possible"), "⛈️")

    def test_cloudy(self):
        self.assertEqual(gw.format_period_emoji("Mostly Cloudy"), "☁️")

    def test_windy(self):
        self.assertEqual(gw.format_period_emoji("Breezy and windy"), "💨")

    def test_foggy(self):
        self.assertEqual(gw.format_period_emoji("Areas of fog"), "🌫️")

    def test_partly_sunny_is_sunny(self):
        # "Partly Sunny" matches "Sunny" keyword → ☀️
        self.assertEqual(gw.format_period_emoji("Partly Sunny"), "☀️")

    def test_unknown_returns_string(self):
        emoji = gw.format_period_emoji("Extreme Blizzard")
        self.assertIsInstance(emoji, str)


# ---------------------------------------------------------------------------
# 14. Format Outputs (NWS)
# ---------------------------------------------------------------------------

class TestFormatNWSOutput(unittest.TestCase):

    def test_contains_location(self):
        output = gw.format_nws_output({"periods": _make_nws_periods()}, [], "Chicago, IL")
        self.assertIn("Chicago", output)

    def test_contains_period_names(self):
        output = gw.format_nws_output({"periods": _make_nws_periods()}, [], "Chicago, IL")
        self.assertIn("Period 1", output)

    def test_with_alert_mentions_warning(self):
        alert = _make_alert(event="Winter Storm Warning")
        output = gw.format_nws_output({"periods": _make_nws_periods()}, [alert], "Chicago, IL")
        self.assertIn("Warning", output)

    def test_empty_periods_graceful(self):
        output = gw.format_nws_output({"periods": []}, [], "Chicago, IL")
        self.assertIsInstance(output, str)


class TestFormatHourlyOutput(unittest.TestCase):

    def test_next_12_hours_contains_location(self):
        output = gw.format_hourly_output(_make_hourly_periods(), "Seattle, WA")
        self.assertIn("Seattle", output)

    def test_with_target_time(self):
        target = datetime(2026, 3, 3, 15, 0, tzinfo=timezone.utc)
        output = gw.format_hourly_output(_make_hourly_periods(48), "Seattle, WA", target_time=target)
        self.assertIn("Seattle", output)

    def test_empty_periods_graceful(self):
        output = gw.format_hourly_output([], "Seattle, WA")
        self.assertIsInstance(output, str)


# ---------------------------------------------------------------------------
# 15. Format Observation
# ---------------------------------------------------------------------------

class TestFormatObservation(unittest.TestCase):

    def test_contains_temperature_in_fahrenheit(self):
        output = gw.format_observation(_NWS_OBSERVATION['properties'])
        self.assertIn("59", output)  # 15°C ≈ 59°F

    def test_contains_wind_direction(self):
        output = gw.format_observation(_NWS_OBSERVATION['properties'])
        self.assertIn("W", output)  # 270° = West

    def test_contains_humidity(self):
        output = gw.format_observation(_NWS_OBSERVATION['properties'])
        self.assertIn("65", output)

    def test_contains_pressure(self):
        output = gw.format_observation(_NWS_OBSERVATION['properties'])
        self.assertIn("29.9", output)  # ~29.92 inHg


# ---------------------------------------------------------------------------
# 16. wttr.in Formatting
# ---------------------------------------------------------------------------

class TestFormatWttrOutput(unittest.TestCase):

    def test_with_forecast_text(self):
        output = gw.format_wttr_output("Weather: Sunny 72°F", None, "Paris, France")
        self.assertIn("Paris", output)
        self.assertIn("Sunny", output)

    def test_with_current_conditions(self):
        current = {"condition": "Cloudy", "temp": "+18°C", "wind": "10 km/h",
                   "humidity": "70%", "precip": "0.0 mm"}
        output = gw.format_wttr_output(None, current, "London, UK")
        self.assertIn("London", output)
        self.assertIn("Cloudy", output)

    def test_both_none_returns_string(self):
        output = gw.format_wttr_output(None, None, "Tokyo, Japan")
        self.assertIsInstance(output, str)


# ---------------------------------------------------------------------------
# 17. Fire Weather
# ---------------------------------------------------------------------------

class TestFireWeather(unittest.TestCase):

    def test_with_fire_data(self):
        fire_data = {"text": "Critically dry conditions with strong gusty winds."}
        output = gw.format_fire_weather_output(fire_data, [], "Los Angeles, CA")
        self.assertIn("Los Angeles", output)
        self.assertIn("dry", output.lower())

    def test_with_fire_alert(self):
        alert = _make_alert(event="Red Flag Warning", description="Extreme fire danger.")
        output = gw.format_fire_weather_output(None, [alert], "San Diego, CA")
        self.assertIn("Red Flag", output)

    def test_no_data_returns_string(self):
        output = gw.format_fire_weather_output(None, [], "Portland, OR")
        self.assertIsInstance(output, str)


# ---------------------------------------------------------------------------
# 18. NWS API Functions (mocked)
# ---------------------------------------------------------------------------

class TestNWSAPIFunctions(unittest.TestCase):

    def _seq(self, *responses):
        return patch('urllib.request.urlopen',
                     side_effect=[_mock_urlopen(r) for r in responses])

    def test_get_nws_gridpoint_success(self):
        payload = {"properties": _NWS_GRIDPOINT_PROPS}
        with self._seq(payload):
            result = gw.get_nws_gridpoint(40.7, -74.0)
        self.assertIsNotNone(result)
        self.assertEqual(result['gridId'], "OKX")

    def test_get_nws_gridpoint_network_error(self):
        with patch('urllib.request.urlopen', side_effect=Exception("timeout")):
            result = gw.get_nws_gridpoint(40.7, -74.0)
        self.assertIsNone(result)

    def test_get_nws_forecast_success(self):
        payload = {"properties": {"periods": _make_nws_periods()}}
        with self._seq(payload):
            result = gw.get_nws_forecast(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)
        self.assertIn('periods', result)

    def test_get_nws_hourly_forecast_success(self):
        payload = {"properties": {"periods": _make_hourly_periods()}}
        with self._seq(payload):
            result = gw.get_nws_hourly_forecast(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)
        self.assertIn('periods', result)
        self.assertGreater(len(result['periods']), 0)

    def test_get_nws_alerts_with_active_alerts(self):
        payload = {
            "features": [{
                "properties": {
                    "event": "Winter Storm Warning", "severity": "Severe",
                    "urgency": "Expected", "certainty": "Likely",
                    "headline": "Storm Warning", "description": "Heavy snow.",
                    "instruction": "Stay safe.", "onset": "2026-03-04T06:00:00-05:00",
                    "expires": "2026-03-05T12:00:00-05:00", "response": "Prepare",
                }
            }]
        }
        with self._seq(payload):
            result = gw.get_nws_alerts(_NWS_GRIDPOINT_PROPS)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['properties']['event'], "Winter Storm Warning")

    def test_get_nws_alerts_empty(self):
        with self._seq({"features": []}):
            result = gw.get_nws_alerts(_NWS_GRIDPOINT_PROPS)
        self.assertEqual(result, [])

    def test_get_station_observation_success(self):
        with self._seq(_NWS_STATIONS, _NWS_OBSERVATION):
            result = gw.get_station_observation(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)

    def test_get_station_observation_network_error(self):
        with patch('urllib.request.urlopen', side_effect=Exception("error")):
            result = gw.get_station_observation(_NWS_GRIDPOINT_PROPS)
        self.assertIsNone(result)

    def test_get_nws_grid_data_success(self):
        payload = {"properties": {"snowfallAmount": {"values": []}}}
        with self._seq(payload):
            result = gw.get_nws_grid_data(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)

    def test_get_aviation_taf_success(self):
        taf_response = {
            "features": [{
                "properties": {
                    "stationId": "KJFK",
                    "rawTAF": "TAF KJFK 031730Z 0318/0418 27012KT P6SM SCT050",
                }
            }]
        }
        with self._seq(_NWS_STATIONS, taf_response):
            result = gw.get_aviation_taf(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)

    def test_get_fire_weather_success(self):
        payload = {"properties": {"text": "Dry and windy conditions."}}
        with self._seq(payload):
            result = gw.get_fire_weather(_NWS_GRIDPOINT_PROPS)
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# 19. AirNow API Functions (mocked)
# ---------------------------------------------------------------------------

class TestAirNowAPIFunctions(unittest.TestCase):

    def test_get_current_success(self):
        payload = [{"AQI": 42, "Category": {"Name": "Good"}, "ParameterName": "PM2.5"}]
        with patch('urllib.request.urlopen', return_value=_mock_urlopen(payload)):
            result = gw.get_airnow_current(40.7, -74.0)
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['AQI'], 42)

    def test_get_current_without_api_key(self):
        payload = [{"AQI": 55, "Category": {"Name": "Moderate"}, "ParameterName": "Ozone"}]
        env = {k: v for k, v in os.environ.items() if k != 'AIRNOW_API_KEY'}
        with patch.dict(os.environ, env, clear=True):
            with patch('urllib.request.urlopen', return_value=_mock_urlopen(payload)):
                result = gw.get_airnow_current(40.7, -74.0)
        self.assertIsNotNone(result)

    def test_get_forecast_success(self):
        payload = [
            {"AQI": 45, "Category": {"Name": "Good"}, "DateForecast": "2026-03-04"},
            {"AQI": 60, "Category": {"Name": "Moderate"}, "DateForecast": "2026-03-05"},
        ]
        with patch('urllib.request.urlopen', return_value=_mock_urlopen(payload)):
            result = gw.get_airnow_forecast(40.7, -74.0)
        self.assertEqual(len(result), 2)

    def test_network_error_returns_none(self):
        with patch('urllib.request.urlopen', side_effect=Exception("DNS error")):
            result = gw.get_airnow_current(40.7, -74.0)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 20. wttr.in API Functions (mocked)
# ---------------------------------------------------------------------------

class TestWttrAPIFunctions(unittest.TestCase):

    def test_get_forecast_success(self):
        ascii_art = "Weather: Paris\n☀️ Sunny 22°C"
        with patch('urllib.request.urlopen', return_value=_mock_urlopen_text(ascii_art)):
            result = gw.get_wttr_forecast("Paris, France")
        self.assertIn("Sunny", result)

    def test_get_forecast_network_error(self):
        with patch('urllib.request.urlopen', side_effect=Exception("timeout")):
            result = gw.get_wttr_forecast("Paris, France")
        self.assertIsNone(result)

    def test_get_current_success(self):
        pipe_response = "Sunny|+22°C|↑10km/h|65%|0.0mm"
        with patch('urllib.request.urlopen', return_value=_mock_urlopen_text(pipe_response)):
            result = gw.get_wttr_current("Paris, France")
        self.assertIsNotNone(result)
        self.assertIn("condition", result)

    def test_get_current_network_error(self):
        with patch('urllib.request.urlopen', side_effect=Exception("timeout")):
            result = gw.get_wttr_current("Paris, France")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
