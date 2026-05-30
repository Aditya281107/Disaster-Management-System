"""
Node 2: Time Series Forecasting
=================================
Analyzes historical weather data to forecast near-future metrics
(temperature, rainfall, wind) for the next 48 hours using
Holt-Winters Exponential Smoothing (from Part 1).
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def _forecast_metric(values: list, steps: int = 2) -> list:
    """
    Forecast a single metric using Holt-Winters.
    steps=2 means 2 future periods (we treat each period as ~24h).
    """
    if len(values) < 5:
        # Not enough data, return last value repeated
        return [values[-1]] * steps

    series = pd.Series(values, dtype=float)

    try:
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(steps)
        return [round(float(v), 1) for v in forecast.values]
    except Exception:
        # Fallback: linear extrapolation
        last = values[-1]
        diff = values[-1] - values[-2] if len(values) >= 2 else 0
        return [round(last + diff * (i + 1), 1) for i in range(steps)]


def time_series_forecast_node(state: dict) -> dict:
    """
    Node 2: Forecast weather metrics for the next 48 hours.
    Uses Holt-Winters Exponential Smoothing on historical data.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 2] TIME SERIES FORECAST")
    print(f"{'='*60}")

    historical = state["historical_data"]
    current = state["weather_data"]

    # Extract time series for each metric
    temps = [r["temperature_c"] for r in historical]
    humidity = [r["humidity_pct"] for r in historical]
    wind = [r["wind_speed_kmh"] for r in historical]
    rainfall = [r["rainfall_mm"] for r in historical]
    pressure = [r["pressure_hpa"] for r in historical]

    print(f"Forecasting from {len(historical)} historical data points...")
    print("Using Holt-Winters Exponential Smoothing (Part 1 technique)")

    # Forecast 2 steps (each ~24h) = 48 hours
    temp_fc = _forecast_metric(temps, 2)
    hum_fc = _forecast_metric(humidity, 2)
    wind_fc = _forecast_metric(wind, 2)
    rain_fc = _forecast_metric(rainfall, 2)
    pres_fc = _forecast_metric(pressure, 2)

    # Use the max/worst-case from the 48h forecast for disaster prediction
    forecast = {
        "temperature_c": round(max(temp_fc), 1),
        "humidity_pct": round(min(100, max(0, max(hum_fc))), 1),
        "wind_speed_kmh": round(max(0, max(wind_fc)), 1),
        "rainfall_mm": round(max(0, sum(rain_fc)), 1),  # cumulative rainfall
        "pressure_hpa": round(min(pres_fc), 1),  # lowest pressure = worst
        "forecast_24h": {
            "temperature_c": temp_fc[0], "humidity_pct": hum_fc[0],
            "wind_speed_kmh": wind_fc[0], "rainfall_mm": rain_fc[0],
            "pressure_hpa": pres_fc[0],
        },
        "forecast_48h": {
            "temperature_c": temp_fc[1], "humidity_pct": hum_fc[1],
            "wind_speed_kmh": wind_fc[1], "rainfall_mm": rain_fc[1],
            "pressure_hpa": pres_fc[1],
        },
    }

    print(f"\n48-Hour Peak Forecast:")
    print(f"  Temperature: {forecast['temperature_c']}C")
    print(f"  Humidity: {forecast['humidity_pct']}%")
    print(f"  Wind Speed: {forecast['wind_speed_kmh']} km/h")
    print(f"  Rainfall (cumulative): {forecast['rainfall_mm']} mm")
    print(f"  Min Pressure: {forecast['pressure_hpa']} hPa")

    return {"forecast": forecast}
