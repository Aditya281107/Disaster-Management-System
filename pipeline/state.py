"""
Pipeline State Schema
======================
Central TypedDict defining the shared state passed between all nodes
in the LangGraph disaster management pipeline.
"""

from typing import TypedDict


class DisasterState(TypedDict):
    """Shared state for the disaster management pipeline."""

    # --- Input ---
    location: str                 # User-provided geographic location

    # --- Node 1: Weather Ingestion ---
    weather_data: dict            # Current weather conditions from API/mock
    historical_data: list         # List of dicts: historical weather records

    # --- Node 2: Time Series Forecast ---
    forecast: dict                # 48-hour forecast: {temperature, rainfall, wind_speed, ...}

    # --- Node 3: Disaster Prediction (ML) ---
    disaster_prediction: dict     # {type, probability, features_used}

    # --- Node 4: News Monitoring ---
    news_context: str             # Summarized relevant news articles

    # --- Node 5: Cognitive Assessor ---
    severity: str                 # low | medium | high | critical
    department: str               # emergency_response | civil_defense | public_works

    # --- Node 6: Department Agent ---
    action_plan: str              # Detailed action plan from department agent
    alert_message: str            # Formatted alert message for approval

    # --- Node 7: Human Gatekeeper ---
    human_decision: str           # approve | reject
    human_feedback: str           # Feedback text on rejection

    # --- Node 8: Self-Improving Loop ---
    insights: list                # List of learned insight strings
    iteration: int                # Current retry iteration count
