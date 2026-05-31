"""
Node 8: Self-Improving Loop
==============================
When the human rejects an output, this node:
1. Reflects on the rejected output + human feedback
2. Generates a permanent "Insight/Rule"
3. Appends the insight to the state
4. Routes back to the department agent for regeneration

This demonstrates Memory & Adaptation.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Persistent storage for insights across runs
INSIGHTS_FILE = PROJECT_ROOT / "data" / "learned_insights.json"


def _call_gemini(prompt: str) -> str:
    """Call Gemini via langchain-google-genai."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
        )
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return ""


REFLECTION_PROMPT = """You are a Self-Improving AI Agent. A human reviewer has REJECTED an alert message you generated. Your job is to reflect on the failure and produce a PERMANENT RULE that will prevent the same mistake in the future.

## Rejected Alert Message
{alert_message}

## Human Feedback
"{human_feedback}"

## Existing Rules (do not duplicate these)
{existing_insights}

## Your Task
1. Analyze what went wrong in the rejected alert
2. Consider the human's feedback carefully
3. Generate ONE new, specific, actionable rule/insight

Respond with ONLY the new rule as a single sentence. Examples:
- "Always include emergency contact numbers for high-severity alerts"
- "Include specific evacuation routes with street names, not just general directions"
- "Add estimated time-to-impact for weather events"

Your new rule:"""


def _load_insights() -> list:
    """Load persisted insights from disk."""
    if INSIGHTS_FILE.exists():
        with open(INSIGHTS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_insights(insights: list):
    """Persist insights to disk."""
    INSIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INSIGHTS_FILE, "w") as f:
        json.dump(insights, f, indent=2)


def self_improver_node(state: dict) -> dict:
    """
    Node 8: Reflect on rejection, generate a new insight,
    and prepare for re-generation.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 8] SELF-IMPROVING LOOP")
    print(f"{'='*60}")

    feedback = state.get("human_feedback", "No specific feedback provided")
    alert = state.get("alert_message", "")
    current_insights = state.get("insights", [])
    iteration = state.get("iteration", 0)

    # Load any previously persisted insights
    persisted = _load_insights()
    all_insights = list(set(current_insights + persisted))

    existing_text = "\n".join(f"- {r}" for r in all_insights) if all_insights else "None yet."

    print(f"Human Feedback: \"{feedback}\"")
    print(f"Existing Insights: {len(all_insights)}")
    print(f"Generating new insight via reflection...")

    prompt = REFLECTION_PROMPT.format(
        alert_message=alert[:1000],  # Truncate for prompt size
        human_feedback=feedback,
        existing_insights=existing_text,
    )

    new_insight = _call_gemini(prompt).strip().strip('"').strip("'")

    # Avoid duplicates
    if new_insight and new_insight not in all_insights:
        all_insights.append(new_insight)
        print(f"\n[NEW INSIGHT] {new_insight}")
    else:
        print(f"\n[INFO] No new unique insight generated.")

    # Persist to disk
    _save_insights(all_insights)
    print(f"Total insights: {len(all_insights)}")
    print(f"Routing back to department agent for regeneration (iteration {iteration + 1})...")

    return {
        "insights": all_insights,
        "iteration": iteration + 1,
        "human_decision": "",  # Reset for next review
        "human_feedback": "",  # Reset
    }
