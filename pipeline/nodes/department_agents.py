"""
Node 6: Department Agents
============================
Three specialized LLM agents that draft action plans and alert messages
based on the routed department. Each agent has a unique persona and
incorporates learned insights from past rejections.
"""

import os
import json
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
            temperature=0.4,
        )
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "**Emergency Alert**\n\nPlease be advised of the upcoming situation. Refer to local authorities for details."


# ---------------------------------------------------------------------------
# Department-Specific Prompt Templates
# ---------------------------------------------------------------------------

EMERGENCY_RESPONSE_PROMPT = """You are the EMERGENCY RESPONSE Department Agent for a Disaster Management System.
Your role is to draft immediate, life-saving action plans for critical situations.

## Situation Brief
- Location: {location}
- Disaster Type: {disaster_type} (Confidence: {confidence}%)
- Severity: {severity}
- Current Conditions: Temperature {temp}C, Humidity {humidity}%, Wind {wind} km/h, Rainfall {rain} mm
- News Context: {news_context}

{insights_section}

## Your Task
Draft a comprehensive EMERGENCY RESPONSE action plan and alert message. Include:
1. Immediate evacuation orders with specific zones
2. Emergency shelter locations
3. Emergency contact numbers (use realistic placeholder numbers)
4. Rescue team deployment plan
5. Medical emergency preparation
6. Communication channels for affected residents

Format your response as:
---ACTION PLAN---
[Your detailed action plan here]

---ALERT MESSAGE---
[A concise, urgent alert message suitable for SMS/email to residents]
"""

CIVIL_DEFENSE_PROMPT = """You are the CIVIL DEFENSE Department Agent for a Disaster Management System.
Your role is to draft infrastructure protection and resource deployment plans.

## Situation Brief
- Location: {location}
- Disaster Type: {disaster_type} (Confidence: {confidence}%)
- Severity: {severity}
- Current Conditions: Temperature {temp}C, Humidity {humidity}%, Wind {wind} km/h, Rainfall {rain} mm
- News Context: {news_context}

{insights_section}

## Your Task
Draft a comprehensive CIVIL DEFENSE action plan and alert message. Include:
1. Infrastructure protection measures (bridges, buildings, utilities)
2. Resource deployment (sandbags, barriers, equipment)
3. Coordination with military/national guard if needed
4. Supply chain and logistics for essential goods
5. Communication strategy for public awareness
6. Timeline of actions with priorities

Format your response as:
---ACTION PLAN---
[Your detailed action plan here]

---ALERT MESSAGE---
[A professional alert message suitable for government/agency distribution]
"""

PUBLIC_WORKS_PROMPT = """You are the PUBLIC WORKS Department Agent for a Disaster Management System.
Your role is to draft utility management and infrastructure maintenance plans.

## Situation Brief
- Location: {location}
- Disaster Type: {disaster_type} (Confidence: {confidence}%)
- Severity: {severity}
- Current Conditions: Temperature {temp}C, Humidity {humidity}%, Wind {wind} km/h, Rainfall {rain} mm
- News Context: {news_context}

{insights_section}

## Your Task
Draft a comprehensive PUBLIC WORKS action plan and alert message. Include:
1. Drainage system management and flood channel clearing
2. Road closure plan with alternative routes
3. Power grid protection and backup systems
4. Water supply and sanitation measures
5. Debris removal preparation
6. Coordination with utility companies

Format your response as:
---ACTION PLAN---
[Your detailed action plan here]

---ALERT MESSAGE---
[An informative alert message suitable for public notification]
"""

DEPARTMENT_PROMPTS = {
    "emergency_response": EMERGENCY_RESPONSE_PROMPT,
    "civil_defense": CIVIL_DEFENSE_PROMPT,
    "public_works": PUBLIC_WORKS_PROMPT,
}


def department_agent_node(state: dict) -> dict:
    """
    Node 6: The selected department agent drafts an action plan and alert.
    Incorporates any learned insights from previous rejections.
    """
    department = state["department"]
    print(f"\n{'='*60}")
    print(f"[NODE 6] DEPARTMENT AGENT: {department.upper().replace('_', ' ')}")
    print(f"{'='*60}")

    prediction = state["disaster_prediction"]
    weather = state["weather_data"]
    insights = state.get("insights", [])
    iteration = state.get("iteration", 0)

    # Build insights section if any exist
    if insights:
        insights_text = "## IMPORTANT: Learned Rules from Previous Feedback\n"
        insights_text += "You MUST follow these rules (learned from human feedback):\n"
        for i, insight in enumerate(insights, 1):
            insights_text += f"{i}. {insight}\n"
        insights_section = insights_text
    else:
        insights_section = ""

    # Select and fill the prompt
    prompt_template = DEPARTMENT_PROMPTS.get(department, CIVIL_DEFENSE_PROMPT)
    prompt = prompt_template.format(
        location=state["location"],
        disaster_type=prediction["predicted_disaster"],
        confidence=prediction["confidence_pct"],
        severity=state["severity"],
        temp=weather["temperature_c"],
        humidity=weather["humidity_pct"],
        wind=weather["wind_speed_kmh"],
        rain=weather["rainfall_mm"],
        news_context=state.get("news_context", "No news available."),
        insights_section=insights_section,
    )

    if iteration > 0:
        print(f"Iteration #{iteration + 1} (incorporating {len(insights)} learned insights)")
    print(f"Generating action plan for {prediction['predicted_disaster']} scenario...")

    response = _call_gemini(prompt)

    # Parse the response into action_plan and alert_message
    if "---ACTION PLAN---" in response and "---ALERT MESSAGE---" in response:
        parts = response.split("---ALERT MESSAGE---")
        action_plan = parts[0].replace("---ACTION PLAN---", "").strip()
        alert_message = parts[1].strip()
    else:
        # Fallback: use entire response as both
        action_plan = response
        alert_message = response[:500]

    print(f"\nAction Plan Length: {len(action_plan)} chars")
    print(f"Alert Message Length: {len(alert_message)} chars")
    print(f"Preview: {alert_message[:200]}...")

    return {
        "action_plan": action_plan,
        "alert_message": alert_message,
    }
