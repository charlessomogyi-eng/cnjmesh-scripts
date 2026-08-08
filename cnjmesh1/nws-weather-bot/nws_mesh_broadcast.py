#!/usr/bin/env python3
import json, os, subprocess, sys, urllib.request

NWS_FORECAST_URL = "https://api.weather.gov/gridpoints/PHI/65,95/forecast"
NWS_ALERTS_URL = "https://api.weather.gov/alerts/active?zone=NJZ018"
CLI_PATH = "/home/somog/.local/bin/meshcore-cli"
PORT = "/dev/kpc1"
CHANNEL_INDEX = "2"
CACHE_FILE = "/tmp/last_nws_alert.txt"
HEADERS = {"User-Agent": "(CNJ-Mesh-WeatherBot, admin@cnjmesh.org)"}

def send_to_mesh(message):
    if not message:
        return
    cmd = [CLI_PATH, "-s", PORT, "chan", CHANNEL_INDEX, message]
    print("Executing:", " ".join(cmd))
    subprocess.run(cmd)

def broadcast_forecast():
    try:
        req = urllib.request.Request(NWS_FORECAST_URL, headers=HEADERS)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            today = data["properties"]["periods"][0]
            forecast = today.get("shortForecast", "")
            name = today.get("name", "Forecast")
            temp = today.get("temperature", "")
            unit = today.get("temperatureUnit", "F")
            wind_spd = today.get("windSpeed", "")
            wind_dir = today.get("windDirection", "")
            msg = f"NWS Daily ({name}): {forecast}. High {temp}{unit}. Wind {wind_spd} {wind_dir}."
            send_to_mesh(msg)
    except Exception as e:
        print("Forecast fetch error:", e, file=sys.stderr)

def check_alerts():
    try:
        req = urllib.request.Request(NWS_ALERTS_URL, headers=HEADERS)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            features = data.get("features", [])
            if not features:
                return
            alert_id = features[0].get("id", "")
            alert = features[0]["properties"]
            last_id = ""
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    last_id = f.read().strip()
            if alert_id != last_id:
                msg = "NWS ALERT: " + str(alert.get("event", "Alert")) + " - " + str(alert.get("headline", "")).strip()
                send_to_mesh(msg)
                with open(CACHE_FILE, "w") as f:
                    f.write(alert_id)
    except Exception as e:
        print("Alert fetch error:", e, file=sys.stderr)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "alert"
    if mode == "forecast":
        broadcast_forecast()
    else:
        check_alerts()
