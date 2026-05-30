"""
LangGraph Pipeline -- Disaster Management Graph
==================================================
Builds the full state-driven pipeline connecting all 8 nodes
with conditional routing and a self-improving feedback loop.

Graph Architecture:
    START -> weather_ingestion -> time_series_forecast -> disaster_prediction
         -> news_monitor -> cognitive_assessor -> [department_agent (routed)]
         -> human_gatekeeper -> approve: send_alert -> END
                             -> reject:  self_improver -> department_agent (loop)
"""

from langgraph.graph import StateGraph, START, END

from pipeline.state import DisasterState
from pipeline.nodes.weather_ingestion import weather_ingestion_node
from pipeline.nodes.time_series_forecast import time_series_forecast_node
from pipeline.nodes.disaster_prediction import disaster_prediction_node
from pipeline.nodes.news_monitor import news_monitor_node
from pipeline.nodes.cognitive_assessor import cognitive_assessor_node
from pipeline.nodes.department_agents import department_agent_node
from pipeline.nodes.human_gatekeeper import human_gatekeeper_node
from pipeline.nodes.self_improver import self_improver_node


# ---------------------------------------------------------------------------
# Alert Sender (final step on approval)
# ---------------------------------------------------------------------------
def send_alert_node(state: dict) -> dict:
    """Send the approved alert (dry-run mode)."""
    print(f"\n{'='*60}")
    print(f"[SEND ALERT] APPROVED -- ALERT DISPATCHED")
    print(f"{'='*60}")
    print(f"Severity: {state['severity'].upper()}")
    print(f"Department: {state['department']}")
    print(f"Disaster: {state['disaster_prediction']['predicted_disaster']}")
    print(f"\n[DRY RUN] Alert message would be sent to all registered recipients.")
    print(f"{'='*60}")
    return {}


# ---------------------------------------------------------------------------
# Conditional Edge: Human Decision Router
# ---------------------------------------------------------------------------
def route_human_decision(state: dict) -> str:
    """Route based on human approve/reject decision."""
    decision = state.get("human_decision", "pending")
    if decision == "approve":
        return "send_alert"
    elif decision == "reject":
        return "self_improver"
    else:
        # pending -- in web mode, the graph will be interrupted here
        return "send_alert"  # default to approve for safety


# ---------------------------------------------------------------------------
# Build the Full Graph
# ---------------------------------------------------------------------------
def build_disaster_graph():
    """
    Constructs and compiles the full disaster management pipeline.
    """
    workflow = StateGraph(DisasterState)

    # Add all nodes
    workflow.add_node("weather_ingestion", weather_ingestion_node)
    workflow.add_node("time_series_forecast", time_series_forecast_node)
    workflow.add_node("disaster_prediction", disaster_prediction_node)
    workflow.add_node("news_monitor", news_monitor_node)
    workflow.add_node("cognitive_assessor", cognitive_assessor_node)
    workflow.add_node("department_agent", department_agent_node)
    workflow.add_node("human_gatekeeper", human_gatekeeper_node)
    workflow.add_node("self_improver", self_improver_node)
    workflow.add_node("send_alert", send_alert_node)

    # Define edges: Sequential flow
    workflow.add_edge(START, "weather_ingestion")
    workflow.add_edge("weather_ingestion", "time_series_forecast")
    workflow.add_edge("time_series_forecast", "disaster_prediction")
    workflow.add_edge("disaster_prediction", "news_monitor")
    workflow.add_edge("news_monitor", "cognitive_assessor")
    workflow.add_edge("cognitive_assessor", "department_agent")
    workflow.add_edge("department_agent", "human_gatekeeper")

    # Conditional edge: human decision
    workflow.add_conditional_edges(
        "human_gatekeeper",
        route_human_decision,
        {
            "send_alert": "send_alert",
            "self_improver": "self_improver",
        },
    )

    # Self-improver loops back to department agent
    workflow.add_edge("self_improver", "department_agent")

    # Send alert goes to END
    workflow.add_edge("send_alert", END)

    # Compile
    graph = workflow.compile()
    print("[Graph] Disaster Management pipeline compiled successfully.")
    print("[Graph] Flow: Weather -> Forecast -> ML Predict -> News -> Assess -> Dept Agent -> Human -> Approve/Reject")
    return graph


def run_pipeline(location: str, human_decision: str = "approve", human_feedback: str = "") -> dict:
    """
    Run the full pipeline for a given location.
    For CLI/testing, pass human_decision directly.
    """
    graph = build_disaster_graph()

    initial_state = {
        "location": location,
        "weather_data": {},
        "historical_data": [],
        "forecast": {},
        "disaster_prediction": {},
        "news_context": "",
        "severity": "",
        "department": "",
        "action_plan": "",
        "alert_message": "",
        "human_decision": human_decision,
        "human_feedback": human_feedback,
        "insights": [],
        "iteration": 0,
    }

    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    import sys
    location = sys.argv[1] if len(sys.argv) > 1 else "Mumbai, India"
    print(f"\n{'#'*70}")
    print(f"  AUTONOMOUS DISASTER MANAGEMENT SYSTEM")
    print(f"  Location: {location}")
    print(f"{'#'*70}")
    result = run_pipeline(location)
    print(f"\n{'#'*70}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'#'*70}")
