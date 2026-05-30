"""
Node 3: Disaster Prediction Model
====================================
Loads the pre-trained RandomForest classifier and predicts the
likelihood and type of disaster from the forecasted weather metrics.

This is the ML-LLM Bridge: numerical ML outputs flow directly
into LLM reasoning prompts in downstream nodes.
"""

import os
from pathlib import Path

import numpy as np
import joblib

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = MODEL_DIR / "disaster_classifier.joblib"
META_PATH = MODEL_DIR / "model_meta.joblib"

FEATURE_COLUMNS = [
    "temperature_c", "humidity_pct", "wind_speed_kmh",
    "rainfall_mm", "pressure_hpa",
]


def disaster_prediction_node(state: dict) -> dict:
    """
    Node 3: Predict disaster type and probability using the pre-trained ML model.
    Feeds forecasted weather metrics as features.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 3] DISASTER PREDICTION (ML MODEL)")
    print(f"{'='*60}")

    forecast = state["forecast"]

    # Build feature vector from the 48h peak forecast
    features = np.array([[
        forecast["temperature_c"],
        forecast["humidity_pct"],
        forecast["wind_speed_kmh"],
        forecast["rainfall_mm"],
        forecast["pressure_hpa"],
    ]])

    print(f"Feature vector: {dict(zip(FEATURE_COLUMNS, features[0]))}")

    # Load model
    if not MODEL_PATH.exists():
        print("[WARNING] Model not found. Run: python models/train_disaster_classifier.py")
        print("[WARNING] Using fallback rule-based prediction.")
        return {"disaster_prediction": _fallback_prediction(forecast)}

    clf = joblib.load(MODEL_PATH)
    print(f"Model loaded: {type(clf).__name__}")

    # Predict
    prediction = clf.predict(features)[0]
    probabilities = clf.predict_proba(features)[0]
    class_names = clf.classes_

    # Build probability map (cast names to str to avoid numpy.str_ JSON errors)
    prob_map = {str(name): round(float(prob) * 100, 1)
                for name, prob in zip(class_names, probabilities)}

    max_prob = round(float(max(probabilities)) * 100, 1)

    result = {
        "predicted_disaster": str(prediction),
        "confidence_pct": max_prob,
        "probabilities": prob_map,
        "features_used": dict(zip(FEATURE_COLUMNS, [float(x) for x in features[0]])),
        "model_type": "RandomForestClassifier",
    }

    print(f"\n--- ML Prediction ---")
    print(f"Predicted Disaster: {prediction}")
    print(f"Confidence: {max_prob}%")
    print(f"All Probabilities:")
    for name, prob in sorted(prob_map.items(), key=lambda x: -x[1]):
        bar = "#" * int(prob / 2)
        print(f"  {name:20s} {prob:5.1f}% {bar}")

    return {"disaster_prediction": result}


def _fallback_prediction(forecast: dict) -> dict:
    """Simple rule-based fallback if model not available."""
    temp = forecast["temperature_c"]
    rain = forecast["rainfall_mm"]
    wind = forecast["wind_speed_kmh"]
    pres = forecast["pressure_hpa"]
    hum = forecast["humidity_pct"]

    if rain > 200 and hum > 80 and pres < 1000:
        disaster = "Flood"
    elif wind > 120 and pres < 980:
        disaster = "Hurricane"
    elif temp > 42 and hum < 30:
        disaster = "Heatwave"
    elif wind > 60 and rain > 50:
        disaster = "Thunderstorm"
    else:
        disaster = "No Disaster"

    return {
        "predicted_disaster": disaster,
        "confidence_pct": 75.0,
        "probabilities": {disaster: 75.0},
        "features_used": {
            "temperature_c": temp, "humidity_pct": hum,
            "wind_speed_kmh": wind, "rainfall_mm": rain,
            "pressure_hpa": pres,
        },
        "model_type": "rule_based_fallback",
    }
