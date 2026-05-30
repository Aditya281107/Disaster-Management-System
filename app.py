"""
Flask Backend -- Disaster Management System
=============================================
REST API that drives the frontend and orchestrates the LangGraph pipeline.

Endpoints:
    GET  /              -- Serve the frontend
    POST /api/run       -- Start pipeline for a location (returns up to human gatekeeper)
    POST /api/decide    -- Submit human approve/reject decision
    GET  /api/insights  -- Get accumulated learning insights
"""

import os
import json
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pipeline.graph import run_pipeline

app = Flask(__name__, static_folder="static")
CORS(app)  # Enable CORS for all routes

# Pipeline imports
from pipeline.state import DisasterState
from pipeline.nodes.weather_ingestion import weather_ingestion_node
from pipeline.nodes.time_series_forecast import time_series_forecast_node
from pipeline.nodes.disaster_prediction import disaster_prediction_node
from pipeline.nodes.news_monitor import news_monitor_node
from pipeline.nodes.cognitive_assessor import cognitive_assessor_node
from pipeline.nodes.department_agents import department_agent_node
from pipeline.nodes.self_improver import self_improver_node, _load_insights

# In-memory session storage (stores pipeline state between steps)
pipeline_sessions = {}


# ---------------------------------------------------------------------------
# Serve Frontend
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# ---------------------------------------------------------------------------
# API: Run Pipeline (Nodes 1-6, pause before human decision)
# ---------------------------------------------------------------------------
@app.route("/api/run", methods=["POST"])
def api_run_pipeline():
    """Run pipeline nodes 1-6 and return state for human review."""
    try:
        data = request.get_json()
        location = data.get("location", "").strip()
        if not location:
            return jsonify({"error": "Location is required"}), 400

        print(f"\n{'#'*70}")
        print(f"  PIPELINE START: {location}")
        print(f"{'#'*70}")

        # Initialize state
        state = {
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
            "human_decision": "",
            "human_feedback": "",
            "insights": _load_insights(),
            "iteration": 0,
        }

        # Execute nodes 1-6 sequentially
        state.update(weather_ingestion_node(state))
        state.update(time_series_forecast_node(state))
        state.update(disaster_prediction_node(state))
        state.update(news_monitor_node(state))
        state.update(cognitive_assessor_node(state))
        state.update(department_agent_node(state))

        # Store state for the human decision step
        session_id = f"{location}_{state['iteration']}"
        pipeline_sessions[session_id] = state

        # Return state for frontend display (excluding large historical data)
        response_state = {k: v for k, v in state.items() if k != "historical_data"}

        return jsonify({
            "session_id": session_id,
            "state": response_state,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# API: Human Decision (Approve / Reject)
# ---------------------------------------------------------------------------
@app.route("/api/decide", methods=["POST"])
def api_human_decision():
    """Process human approve/reject decision."""
    try:
        data = request.get_json()
        session_id = data.get("session_id", "")
        decision = data.get("decision", "")  # "approve" or "reject"
        feedback = data.get("feedback", "")

        if session_id not in pipeline_sessions:
            return jsonify({"error": "Session not found. Run the pipeline first."}), 404

        if decision not in ("approve", "reject"):
            return jsonify({"error": "Decision must be 'approve' or 'reject'"}), 400

        state = pipeline_sessions[session_id]
        state["human_decision"] = decision
        state["human_feedback"] = feedback

        if decision == "approve":
            print(f"\n[APPROVED] Alert for {state['location']} dispatched.")
            result = {
                "status": "approved",
                "message": "Alert has been approved and dispatched (dry-run mode).",
                "alert_message": state["alert_message"],
                "severity": state["severity"],
                "department": state["department"],
            }
            # Clean up session
            del pipeline_sessions[session_id]
            return jsonify(result)

        else:  # reject
            print(f"\n[REJECTED] Running self-improving loop...")

            # Run self-improver (Node 8)
            state.update(self_improver_node(state))

            # Re-run department agent (Node 6) with new insights
            state.update(department_agent_node(state))

            # Update session for next review
            new_session_id = f"{state['location']}_{state['iteration']}"
            pipeline_sessions[new_session_id] = state
            if session_id in pipeline_sessions and session_id != new_session_id:
                del pipeline_sessions[session_id]

            response_state = {k: v for k, v in state.items() if k != "historical_data"}

            return jsonify({
                "status": "rejected",
                "message": "Output rejected. Self-improving loop activated. New alert generated.",
                "session_id": new_session_id,
                "state": response_state,
                "new_insight": state["insights"][-1] if state["insights"] else None,
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# API: Get Insights
# ---------------------------------------------------------------------------
@app.route("/api/insights", methods=["GET"])
def api_get_insights():
    """Return all accumulated learning insights."""
    insights = _load_insights()
    return jsonify({"insights": insights, "count": len(insights)})


# ---------------------------------------------------------------------------
# Run Server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Disaster Management System")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
