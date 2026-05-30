"""
Node 5: Cognitive Assessor & Router
======================================
The "brain" of the system. An LLM evaluates the ML prediction
alongside live news context to determine severity and route
to the appropriate department.
"""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


def _call_gemini(prompt: str) -> str:
    """Call Gemini via langchain-google-genai."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2,
        )
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "{}"


ASSESSOR_PROMPT = """You are a Disaster Management Cognitive Assessor. Your job is to evaluate the output of a machine learning disaster prediction model alongside real-world news context to determine the SEVERITY of the situation and ROUTE it to the correct department.

## ML Model Prediction
- Predicted Disaster Type: {disaster_type}
- Confidence: {confidence}%
- Feature Data: {features}
- Full Probability Distribution: {probabilities}

## Current Weather Conditions
{weather_summary}

## Live News Context
{news_context}

## Your Task
1. Evaluate the ML prediction's plausibility given the news context
2. Determine the severity level: low, medium, high, or critical
3. Route to the appropriate department:
   - emergency_response: For critical/high severity disasters requiring immediate evacuation, rescue
   - civil_defense: For medium/high severity requiring infrastructure protection, resource deployment
   - public_works: For low/medium severity requiring utility management, drainage, road closures

Respond in EXACTLY this JSON format (no markdown, no code fences):
{{"severity": "low|medium|high|critical", "department": "emergency_response|civil_defense|public_works", "reasoning": "Brief explanation of your assessment"}}
"""


def cognitive_assessor_node(state: dict) -> dict:
    """
    Node 5: LLM evaluates ML prediction + news and determines
    severity level and routing department.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 5] COGNITIVE ASSESSOR & ROUTER")
    print(f"{'='*60}")

    prediction = state["disaster_prediction"]
    weather = state["weather_data"]
    news = state["news_context"]

    weather_summary = (
        f"Location: {weather.get('location', state['location'])}\n"
        f"Temperature: {weather['temperature_c']}C\n"
        f"Humidity: {weather['humidity_pct']}%\n"
        f"Wind Speed: {weather['wind_speed_kmh']} km/h\n"
        f"Rainfall: {weather['rainfall_mm']} mm\n"
        f"Pressure: {weather['pressure_hpa']} hPa\n"
        f"Conditions: {weather.get('description', 'N/A')}"
    )

    prompt = ASSESSOR_PROMPT.format(
        disaster_type=prediction["predicted_disaster"],
        confidence=prediction["confidence_pct"],
        features=json.dumps(prediction["features_used"], indent=2),
        probabilities=json.dumps(prediction["probabilities"], indent=2),
        weather_summary=weather_summary,
        news_context=news,
    )

    print("Evaluating ML prediction + News context with Gemini LLM...")
    response = _call_gemini(prompt)

    # Parse the JSON response -- handle various LLM output formats
    try:
        clean = response.strip()
        # Remove markdown code fences if present
        fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', clean, re.DOTALL)
        if fence_match:
            clean = fence_match.group(1).strip()
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
        if json_match:
            clean = json_match.group(0)
        result = json.loads(clean)
    except (json.JSONDecodeError, AttributeError):
        print(f"[WARNING] Could not parse LLM response, using defaults.")
        print(f"Raw response: {response[:300]}")
        # Fallback: try to extract fields from text
        sev = "medium"
        dept = "civil_defense"
        for s in ["critical", "high", "medium", "low"]:
            if s in response.lower():
                sev = s
                break
        for d in ["emergency_response", "civil_defense", "public_works"]:
            if d in response.lower():
                dept = d
                break
        result = {
            "severity": sev,
            "department": dept,
            "reasoning": "Extracted from unstructured LLM response."
        }

    severity = result.get("severity", "medium")
    department = result.get("department", "civil_defense")
    reasoning = result.get("reasoning", "")

    print(f"\n--- Assessment Result ---")
    print(f"Severity: {severity.upper()}")
    print(f"Department: {department}")
    print(f"Reasoning: {reasoning}")

    return {
        "severity": severity,
        "department": department,
    }
