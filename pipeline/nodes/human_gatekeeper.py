"""
Node 7: Human-in-the-Loop Gatekeeper
=======================================
Pauses the pipeline and presents the alert to a human for review.
In web mode, this sets a flag and returns; the Flask app handles
the actual human interaction via HTTP endpoints.
In CLI mode, uses input() for direct interaction.
"""


def human_gatekeeper_node(state: dict) -> dict:
    """
    Node 7: In web mode, this node simply marks the state as
    'awaiting_human_decision'. The Flask API handles the actual
    human interaction.

    In CLI mode (when called directly), it uses input().
    """
    print(f"\n{'='*60}")
    print(f"[NODE 7] HUMAN-IN-THE-LOOP GATEKEEPER")
    print(f"{'='*60}")
    print(f"\nSeverity: {state['severity'].upper()}")
    print(f"Department: {state['department']}")
    print(f"Disaster: {state['disaster_prediction']['predicted_disaster']}")
    print(f"\n--- ALERT MESSAGE FOR REVIEW ---")
    print(state["alert_message"])
    print(f"{'='*60}")

    # In web mode, we don't block here. The graph will be interrupted
    # and the Flask endpoint will handle the human decision.
    # The decision fields are set by the Flask API before resuming.

    # Default: awaiting decision (will be overridden by web API or CLI)
    return {
        "human_decision": state.get("human_decision", "pending"),
        "human_feedback": state.get("human_feedback", ""),
    }


def human_gatekeeper_cli(state: dict) -> dict:
    """
    CLI version: blocks and waits for human input via terminal.
    Used for standalone testing outside the web interface.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 7] HUMAN-IN-THE-LOOP GATEKEEPER")
    print(f"{'='*60}")
    print(f"\nSeverity: {state['severity'].upper()}")
    print(f"Department: {state['department']}")
    print(f"Disaster: {state['disaster_prediction']['predicted_disaster']}")
    print(f"\n--- ALERT MESSAGE FOR REVIEW ---")
    print(state["alert_message"])
    print(f"\n{'='*60}")

    while True:
        decision = input("\n[APPROVE] or [REJECT]? (a/r): ").strip().lower()
        if decision in ("a", "approve"):
            return {"human_decision": "approve", "human_feedback": ""}
        elif decision in ("r", "reject"):
            feedback = input("Feedback (why rejected?): ").strip()
            return {"human_decision": "reject", "human_feedback": feedback}
        else:
            print("Please enter 'a' to approve or 'r' to reject.")
