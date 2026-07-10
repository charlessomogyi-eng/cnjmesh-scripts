#!/usr/bin/env python3
"""
CNJ Mesh Weather Bot
Station: KD2EEWX (Kendall Park, NJ) via Xweather/AerisWeather
Posts to #central-nj-weather-reports on CNJ Mesh Discord
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

PWS_STATION_ID    = "KD2EEWX"
PWS_CLIENT_ID     = "jP90vdoZlUt6In8IB1Mxx"
PWS_CLIENT_SECRET = os.environ["PWS_CLIENT_SECRET"]
PWS_API_URL       = (
    f"https://api.aerisapi.com/observations/PWS_{PWS_STATION_ID}"
    f"?client_id={PWS_CLIENT_ID}&client_secret={PWS_CLIENT_SECRET}"
)

NWS_ZONE        = "NJZ012"
NWS_ALERTS_URL  = f"https://api.weather.gov/alerts/active?zone={NWS_ZONE}"
NWS_POINTS_URL  = "https://api.weather.gov/points/40.4187,-74.5607"

DISCORD_WEBHOOKS = [os.environ["WEATHER_WEBHOOK_1"], os.environ["WEATHER_WEBHOOK_2"]]
ALERT_WEBHOOKS   = [os.environ["WEATHER_WEBHOOK_1"], os.environ["WEATHER_WEBHOOK_2"],
                    os.environ["NORTH_WEBHOOK"], os.environ["SOUTH_WEBHOOK"]]

STATE_FILE      = Path("/var/lib/weather-bot/state.json")
LOG_FILE        = "/var/log/weather-bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

def load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception as e:
        log.warning(f"Could not load state: {e}")
    return {"posted_alert_ids": [], "last_conditions_ts": 0}

def save_state(state: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        log.warning(f"Could not save state: {e}")

def post_to_discord(embeds: list, webhooks: list = None):
    payload = {"embeds": embeds}
    for url in (webhooks or DISCORD_WEBHOOKS):
        try:
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            log.info(f"Posted {len(embeds)} embed(s) to Discord ({url[:50]}...)")
        except Exception as e:
            log.error(f"Discord post failed for {url[:50]}: {e}")

def wind_direction(degrees: float) -> str:
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(degrees / 22.5) % 16]

def fetch_conditions() -> dict | None:
    try:
        r = requests.get(PWS_API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        obs = data["response"]["ob"]
        return {
            "temp":         obs.get("tempF"),
            "feels_like":   obs.get("feelslikeF"),
            "humidity":     obs.get("humidity"),
            "dewpoint":     obs.get("dewpointF"),
            "pressure":     obs.get("pressureIN"),
            "wind_speed":   obs.get("windSpeedMPH"),
            "wind_gust":    obs.get("windGustMPH"),
            "wind_dir":     obs.get("windDirDEG"),
            "precip_rate":  obs.get("precipRateIN"),
            "precip_today": obs.get("precipIN"),
            "uv":           obs.get("uvi"),
            "solar":        obs.get("solradWM2"),
            "obs_time":     obs.get("dateTimeISO"),
        }
    except Exception as e:
        log.error(f"PWS fetch failed: {e}")
        return None

def conditions_embed(c: dict) -> dict:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    wind = (
        f"{wind_direction(c['wind_dir'])} {c['wind_speed']} mph"
        if c['wind_dir'] is not None and c['wind_speed'] is not None
        else "N/A"
    )
    if c.get("wind_gust") and c["wind_gust"] > (c["wind_speed"] or 0):
        wind += f" (gusts {c['wind_gust']} mph)"

    fields = [
        {"name": "🌡️ Temperature",  "value": f"{c['temp']}°F",                                                    "inline": True},
        {"name": "🤔 Feels Like",   "value": f"{c['feels_like']}°F" if c['feels_like'] is not None else "N/A",    "inline": True},
        {"name": "💧 Humidity",     "value": f"{c['humidity']}%",                                                  "inline": True},
        {"name": "🌬️ Wind",         "value": wind,                                                                 "inline": True},
        {"name": "🌫️ Dew Point",    "value": f"{c['dewpoint']}°F" if c['dewpoint'] is not None else "N/A",        "inline": True},
        {"name": "🔵 Pressure",     "value": f"{c['pressure']} inHg" if c['pressure'] is not None else "N/A",     "inline": True},
        {"name": "🌧️ Rain Rate",    "value": f"{c['precip_rate']} in/hr" if c['precip_rate'] is not None else "0.00 in/hr", "inline": True},
        {"name": "📊 Rain Today",   "value": f"{c['precip_today']} in" if c['precip_today'] is not None else "0.00 in",     "inline": True},
        {"name": "☀️ UV Index",     "value": str(c['uv']) if c['uv'] is not None else "N/A",                      "inline": True},
    ]

    return {
        "title": "🌤️ Kendall Park, NJ — Current Conditions",
        "description": f"Station **KD2EEWX** • {now_str}",
        "color": 0x1E90FF,
        "fields": fields,
        "footer": {"text": "Source: KD2EEWX via Xweather | CNJ Mesh Weather"},
    }

def fetch_forecast() -> list:
    try:
        r = requests.get(NWS_POINTS_URL, timeout=15)
        r.raise_for_status()
        forecast_url = r.json()["properties"]["forecast"]
        r2 = requests.get(forecast_url, timeout=15)
        r2.raise_for_status()
        return r2.json().get("properties", {}).get("periods", [])[:4]
    except Exception as e:
        log.error(f"NWS forecast fetch failed: {e}")
        return []

def forecast_embed(periods: list) -> dict:
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
        "title": "📅 Kendall Park, NJ — NWS Forecast",
        "description": f"Issued by NWS Mount Holly NJ • {now_str}",
        "color": 0x2ECC71,
        "fields": fields,
        "footer": {"text": "Source: NWS Mount Holly (PHI) | CNJ Mesh Weather"},
    }

ALERTS_IGNORE = {"Heat Advisory"}

ALERT_COLORS = {
    "Tornado Warning":             0xFF0000,
    "Severe Thunderstorm Warning": 0xFF6600,
    "Flash Flood Warning":         0x008000,
    "Winter Storm Warning":        0xFF69B4,
    "Flood Watch":                 0x00FF7F,
    "Winter Storm Watch":          0x4169E1,
    "Wind Advisory":               0xD2691E,
    "Special Weather Statement":   0xFFD700,
}

def fetch_alerts() -> list:
    try:
        headers = {"User-Agent": "CNJMeshWeatherBot/1.0 (k2gia@arrl.net)"}
        r = requests.get(NWS_ALERTS_URL, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json().get("features", [])
    except Exception as e:
        log.error(f"NWS alert fetch failed: {e}")
        return []

def alert_embed(feature: dict) -> dict:
    props = feature.get("properties", {})
    event    = props.get("event", "Weather Alert")
    headline = props.get("headline", "")
    desc     = props.get("description", "")[:800]
    instr    = props.get("instruction", "")[:400]
    expires  = props.get("expires", "")[:16].replace("T", " ") if props.get("expires") else "N/A"
    color    = ALERT_COLORS.get(event, 0xFFA500)

    fields = []
    if headline:
        fields.append({"name": "Headline", "value": headline, "inline": False})
    if desc:
        fields.append({"name": "Details", "value": desc + ("…" if len(props.get("description","")) > 800 else ""), "inline": False})
    if instr:
        fields.append({"name": "Instructions", "value": instr, "inline": False})
    fields.append({"name": "Expires", "value": expires + " UTC", "inline": True})

    return {
        "title": f"⚠️ NWS ALERT — {event}",
        "color": color,
        "fields": fields,
        "footer": {"text": f"NWS Zone {NWS_ZONE} | Middlesex County, NJ"},
    }

def run(mode: str):
    state = load_state()

    if mode == "conditions":
        log.info("Running conditions post")
        c = fetch_conditions()
        if c:
            post_to_discord([conditions_embed(c)])
            state["last_conditions_ts"] = int(time.time())
            save_state(state)
        else:
            log.warning("No conditions data returned; skipping post")

    elif mode == "alerts":
        log.info("Checking NWS alerts")
        alerts = fetch_alerts()
        posted_ids = set(state.get("posted_alert_ids", []))
        new_embeds = []
        new_ids    = []

        for feature in alerts:
            if feature.get("properties",{}).get("event","") in ALERTS_IGNORE:
                continue
            sender = feature.get("properties",{}).get("senderName","")
            if "Mount Holly" not in sender:
                continue
            alert_id = feature.get("id", "")
            if alert_id and alert_id not in posted_ids:
                new_embeds.append(alert_embed(feature))
                new_ids.append(alert_id)

        if new_embeds:
            log.info(f"Posting {len(new_embeds)} new alert(s)")
            post_to_discord(new_embeds, ALERT_WEBHOOKS)
            posted_ids.update(new_ids)
            state["posted_alert_ids"] = list(posted_ids)[-50:]
            save_state(state)
        else:
            log.info("No new alerts")

    elif mode == "forecast":
        log.info("Running NWS forecast post")
        periods = fetch_forecast()
        if periods:
            post_to_discord([forecast_embed(periods)])
        else:
            log.warning("No forecast data returned; skipping post")

    else:
        log.error(f"Unknown mode: {mode}. Use 'conditions', 'alerts', or 'forecast'")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: weather_bot.py [conditions|alerts|forecast]")
        sys.exit(1)
    run(sys.argv[1])
