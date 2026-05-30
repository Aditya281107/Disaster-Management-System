"""
Node 1: Environmental Data Ingestion
======================================
Pulls current weather conditions from OpenWeatherMap API (or mock)
and appends to the historical dataset.
"""

import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_CSV = DATA_DIR / "historical_weather.csv"

WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

CSV_COLUMNS = ["date", "temperature_c", "humidity_pct", "wind_speed_kmh",
               "rainfall_mm", "pressure_hpa"]


def _ensure_historical_data():
    """Create synthetic historical weather data if none exists."""
    if HISTORICAL_CSV.exists():
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)

    rows = []
    base_date = datetime.now() - timedelta(days=90)
    for i in range(90):
        dt = base_date + timedelta(days=i)
        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "temperature_c": round(np.random.uniform(20, 40) + 5 * np.sin(i / 10), 1),
            "humidity_pct": round(np.random.uniform(40, 95), 1),
            "wind_speed_kmh": round(np.random.uniform(5, 80), 1),
            "rainfall_mm": round(max(0, np.random.normal(20, 30)), 1),
            "pressure_hpa": round(np.random.uniform(990, 1030), 1),
        })

    with open(HISTORICAL_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[Weather] Generated {len(rows)} days of synthetic historical data.")


def _fetch_weather_api(location: str) -> dict:
    """Fetch real weather from OpenWeatherMap."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": WEATHER_API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Calculate 24h rainfall estimate if rain data exists (OWM gives 1h or 3h)
    precip = 0.0
    if "rain" in data:
        precip = data["rain"].get("1h", 0) * 24 or data["rain"].get("3h", 0) * 8

    return {
        "temperature_c": data["main"]["temp"],
        "humidity_pct": data["main"]["humidity"],
        "wind_speed_kmh": round(data["wind"].get("speed", 0) * 3.6, 1), # m/s to km/h
        "rainfall_mm": round(precip, 1),
        "pressure_hpa": data["main"]["pressure"],
        "description": data["weather"][0]["description"] if data.get("weather") else "unknown",
        "location": f"{data.get('name', 'Unknown')}, {data.get('sys', {}).get('country', 'Unknown')}",
        "source": "openweathermap",
    }


def _mock_weather(location: str) -> dict:
    """Generate realistic mock weather for demo purposes."""
    np.random.seed(hash(location) % 2**31)

    # Create somewhat extreme conditions for interesting predictions
    scenarios = [
        {"temp": 38, "hum": 85, "wind": 45, "rain": 180, "pres": 998,
         "desc": "heavy intensity rain"},
        {"temp": 44, "hum": 18, "wind": 12, "rain": 0, "pres": 1025,
         "desc": "clear sky, extreme heat"},
        {"temp": 28, "hum": 92, "wind": 140, "rain": 250, "pres": 975,
         "desc": "tropical storm conditions"},
        {"temp": 32, "hum": 70, "wind": 75, "rain": 90, "pres": 1005,
         "desc": "thunderstorm with heavy rain"},
        {"temp": 25, "hum": 55, "wind": 20, "rain": 5, "pres": 1018,
         "desc": "partly cloudy, mild"},
    ]

    scenario = scenarios[hash(location) % len(scenarios)]
    # Add small noise
    return {
        "temperature_c": round(scenario["temp"] + np.random.uniform(-2, 2), 1),
        "humidity_pct": round(min(100, max(0, scenario["hum"] + np.random.uniform(-5, 5))), 1),
        "wind_speed_kmh": round(max(0, scenario["wind"] + np.random.uniform(-5, 5)), 1),
        "rainfall_mm": round(max(0, scenario["rain"] + np.random.uniform(-10, 10)), 1),
        "pressure_hpa": round(scenario["pres"] + np.random.uniform(-3, 3), 1),
        "description": scenario["desc"],
        "location": location,
        "source": "mock_data",
    }


def _append_to_historical(weather: dict):
    """Append the fresh reading to historical CSV."""
    _ensure_historical_data()
    row = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "temperature_c": weather["temperature_c"],
        "humidity_pct": weather["humidity_pct"],
        "wind_speed_kmh": weather["wind_speed_kmh"],
        "rainfall_mm": weather["rainfall_mm"],
        "pressure_hpa": weather["pressure_hpa"],
    }
    with open(HISTORICAL_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


def _load_historical() -> list:
    """Load historical data as list of dicts."""
    _ensure_historical_data()
    rows = []
    with open(HISTORICAL_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in CSV_COLUMNS[1:]:  # Convert numeric fields
                row[key] = float(row[key])
            rows.append(row)
    return rows


def weather_ingestion_node(state: dict) -> dict:
    """
    Node 1: Fetch current weather and append to historical dataset.
    """
    location = state["location"]
    print(f"\n{'='*60}")
    print(f"[NODE 1] WEATHER INGESTION")
    print(f"{'='*60}")
    print(f"Location: {location}")
    print(f"DEBUG: WEATHER_API_KEY is '{WEATHER_API_KEY}'")

    # Fetch weather (API or mock)
    if WEATHER_API_KEY:
        try:
            weather = _fetch_weather_api(location)
            print(f"Source: WeatherAPI.com (Live)")
        except Exception as e:
            print(f"API error: {e}. Falling back to mock data.")
            weather = _mock_weather(location)
    else:
        weather = _mock_weather(location)
        print(f"Source: Mock Data (no API key configured)")

    print(f"Temperature: {weather['temperature_c']}C")
    print(f"Humidity: {weather['humidity_pct']}%")
    print(f"Wind Speed: {weather['wind_speed_kmh']} km/h")
    print(f"Rainfall: {weather['rainfall_mm']} mm")
    print(f"Pressure: {weather['pressure_hpa']} hPa")
    print(f"Conditions: {weather['description']}")

    # Append to historical and load full history
    _append_to_historical(weather)
    historical = _load_historical()
    print(f"Historical records: {len(historical)} days")

    return {
        "weather_data": weather,
        "historical_data": historical,
    }
