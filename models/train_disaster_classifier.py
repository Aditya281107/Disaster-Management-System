"""
Disaster Classifier Training Script
=====================================
Generates synthetic weather data and trains a RandomForestClassifier
to predict disaster types from weather features.

Run:  python models/train_disaster_classifier.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib


DISASTER_TYPES = ["No Disaster", "Flood", "Hurricane", "Heatwave", "Thunderstorm"]

# Feature columns the model expects
FEATURE_COLUMNS = [
    "temperature_c",    # Celsius
    "humidity_pct",     # 0-100
    "wind_speed_kmh",   # km/h
    "rainfall_mm",      # mm in 48h forecast
    "pressure_hpa",     # hectopascals
]


def generate_training_data(n_samples=2000):
    """
    Generate synthetic labeled training data.
    Each row maps weather features to a disaster type.
    """
    np.random.seed(42)
    data = []

    for _ in range(n_samples):
        temp = np.random.uniform(-5, 50)
        humidity = np.random.uniform(10, 100)
        wind = np.random.uniform(0, 200)
        rainfall = np.random.uniform(0, 500)
        pressure = np.random.uniform(950, 1050)

        # Rule-based labeling to create realistic patterns
        if rainfall > 200 and humidity > 80 and pressure < 1000:
            label = "Flood"
        elif wind > 120 and pressure < 980 and rainfall > 100:
            label = "Hurricane"
        elif temp > 42 and humidity < 30 and wind < 30:
            label = "Heatwave"
        elif wind > 60 and rainfall > 50 and pressure < 1010:
            label = "Thunderstorm"
        else:
            label = "No Disaster"

        data.append([temp, humidity, wind, rainfall, pressure, label])

    df = pd.DataFrame(data, columns=FEATURE_COLUMNS + ["disaster_type"])
    return df


def train_and_save_model():
    """Train the classifier and save it."""
    print("[TRAIN] Generating synthetic training data...")
    df = generate_training_data(n_samples=3000)

    print(f"[TRAIN] Dataset shape: {df.shape}")
    print(f"[TRAIN] Class distribution:")
    print(df["disaster_type"].value_counts().to_string())

    X = df[FEATURE_COLUMNS]
    y = df["disaster_type"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n[TRAIN] Training RandomForestClassifier...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\n[TRAIN] Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save model
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "disaster_classifier.joblib")
    joblib.dump(clf, model_path)
    print(f"[TRAIN] Model saved to: {model_path}")

    # Also save feature columns for inference
    meta_path = os.path.join(model_dir, "model_meta.joblib")
    joblib.dump({
        "feature_columns": FEATURE_COLUMNS,
        "disaster_types": DISASTER_TYPES,
    }, meta_path)
    print(f"[TRAIN] Metadata saved to: {meta_path}")

    return clf


if __name__ == "__main__":
    train_and_save_model()
