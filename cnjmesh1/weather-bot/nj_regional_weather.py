import os
#!/usr/bin/env python3
"""
NJ Regional Weather Bot - North and South NJ
Uses NWS API only (no PWS required)
Posts to MeshCore NJ Discord channels
"""

import sys
import logging
import requests
from datetime import datetime, timezone

# ── North NJ (Bergen County) ──────────────────────────────────────────────────
NORTH_POINTS_URL = "https://api.weather.gov/points/40.9176,-74.1719"
NORTH_ZONE       = "NJZ104"
NORTH_LABEL      = "Northern NJ (Bergen County)"
NORTH_WEBHOOK    = os.environ["NORTH_WEBHOOK"]

# ── South NJ (Atlantic City area) ────────────────────────────────────────────
SOUTH_POINTS_URL = "https://api.weather.gov/points/39.3643,-74.4229"
SOUTH_ZONE       = "NJZ015"
SOUTH_LABEL      = "Southern NJ (Atlantic County)"
SOUTH_WEBHOOK    = os.environ["SOUTH_WEBHOOK"]

LOG_FILE = "/var/log/nj-regional-weather.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def post_to_discord(webhook: str, embeds: list):
    try:
        r = requests.post(webhook, json={"embeds": embeds}, timeout=10)
        r.raise_for_status()
        log.info(f"Posted to {webhook[:60]}...")
    except Exception as e:
        log.error(f"Discord post failed: {e}")


def fetch_current_conditions(points_url: str) -> dict | None:
    try:
        r = requests.get(points_url, timeout=15,
                         headers={"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"})
        r.raise_for_status()
        props = r.json()["properties"]
        obs_url = props["observationStations"]
        r2 = requests.get(obs_url, timeout=15,
                          headers={"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"})
        r2.raise_for_status()
        station_id = r2.json()["features"][0]["properties"]["stationIdentifier"]
        obs_latest = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        r3 = requests.get(obs_latest, timeout=15,
                          headers={"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"})
        r3.raise_for_status()
        obs = r3.json()["properties"]
        return {
            "station": station_id,
            "temp_c": obs.get("temperature", {}).get("value"),
            "humidity": obs.get("relativeHumidity", {}).get("value"),
            "wind_speed": obs.get("windSpeed", {}).get("value"),
            "wind_dir": obs.get("windDirection", {}).get("value"),
            "description": obs.get("textDescription", ""),
            "pressure": obs.get("barometricPressure", {}).get("value"),
        }
    except Exception as e:
        log.error(f"NWS conditions fetch failed: {e}")
        return None


def c_to_f(c):
    if c is None:
        return None
    return round(c * 9/5 + 32, 1)


def ms_to_mph(ms):
    if ms is None:
        return None
    return round(ms * 2.23694, 1)


def pa_to_inhg(pa):
    if pa is None:
        return None
    return round(pa / 3386.39, 2)


def wind_direction(degrees) -> str:
    if degrees is None:
        return "N/A"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(degrees / 22.5) % 16]


def conditions_embed(c: dict, label: str) -> dict:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    temp_f = c_to_f(c["temp_c"])
    wind_mph = ms_to_mph(c["wind_speed"])
    pressure_inhg = pa_to_inhg(c["pressure"])
    wind = f"{wind_direction(c['wind_dir'])} {wind_mph} mph" if wind_mph is not None else "N/A"

    fields = [
        {"name": "🌡️ Temperature",  "value": f"{temp_f}°F" if temp_f else "N/A",             "inline": True},
        {"name": "💧 Humidity",     "value": f"{round(c['humidity'])}%" if c["humidity"] else "N/A", "inline": True},
        {"name": "🌬️ Wind",         "value": wind,                                             "inline": True},
        {"name": "🔵 Pressure",     "value": f"{pressure_inhg} inHg" if pressure_inhg else "N/A", "inline": True},
        {"name": "🌤️ Conditions",   "value": c["description"] or "N/A",                       "inline": True},
    ]
    return {
        "title": f"🌤️ {label} — Current Conditions",
        "description": f"Station **{c['station']}** • {now_str}",
        "color": 0x1E90FF,
        "fields": fields,
        "footer": {"text": f"Source: NWS | CNJ Mesh Weather"},
    }


def fetch_forecast(points_url: str) -> list:
    try:
        r = requests.get(points_url, timeout=15,
                         headers={"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"})
        r.raise_for_status()
        forecast_url = r.json()["properties"]["forecast"]
        r2 = requests.get(forecast_url, timeout=15,
                          headers={"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"})
        r2.raise_for_status()
        return r2.json().get("properties", {}).get("periods", [])[:4]
    except Exception as e:
        log.error(f"NWS forecast fetch failed: {e}")
        return []


def forecast_embed(periods: list, label: str) -> dict:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fields = []
    for p in periods:
        name = p.get("name", "")
        detail = p.get("detailedForecast", p.get("shortForecast", ""))
        temp = p.get("temperature")
        unit = p.get("temperatureUnit", "F")
        fields.append({
            "name": f"{name} — {temp}°{unit}",
            "value": detail[:200],
            "inline": False
        })
    return {
        "title": f"📅 {label} — NWS Forecast",
        "description": f"Issued by NWS Mount Holly NJ • {now_str}",
        "color": 0x2ECC71,
        "fields": fields,
        "footer": {"text": "Source: NWS Mount Holly (PHI) | CNJ Mesh Weather"},
    }


def run(mode: str):
    configs = [
        (NORTH_POINTS_URL, NORTH_LABEL, NORTH_WEBHOOK),
        (SOUTH_POINTS_URL, SOUTH_LABEL, SOUTH_WEBHOOK),
    ]

    for points_url, label, webhook in configs:
        if mode == "conditions":
            log.info(f"Running conditions post for {label}")
            c = fetch_current_conditions(points_url)
            if c:
                post_to_discord(webhook, [conditions_embed(c, label)])
            else:
                log.warning(f"No conditions data for {label}")

        elif mode == "forecast":
            log.info(f"Running forecast post for {label}")
            periods = fetch_forecast(points_url)
            if periods:
                post_to_discord(webhook, [forecast_embed(periods, label)])
            else:
                log.warning(f"No forecast data for {label}")

        else:
            log.error(f"Unknown mode: {mode}")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: nj_regional_weather.py [conditions|forecast]")
        sys.exit(1)
    run(sys.argv[1])
