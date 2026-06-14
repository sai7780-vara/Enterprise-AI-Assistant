import sys
import os
import time

# Ensure the parent directory of backend/app is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.agents.supervisor_agent import supervisor_agent
from app.graph import graph_workflow


def process_chat(message: str, use_rag: bool = True, top_k: int = 4):
    """Simulates backend chat endpoint logic."""
    category = supervisor_agent.classify(message)
    if category in ("ONBOARDING", "TRAVEL", "CROSS_FUNCTIONAL"):
        initial_state = {
            "message": message,
            "use_rag": use_rag,
            "top_k": top_k,
            "execution_path": [],
            "remaining_steps": [],
            "next_agent": None,
            "hr_response": None,
            "finance_response": None,
            "it_response": None,
            "rag_response": None,
            "sources": [],
            "confidence": None,
            "final_reply": None,
            "workflow_type": None
        }
        result = graph_workflow.invoke(initial_state)
        return {
            "reply": result["final_reply"],
            "selected_agent": "Supervisor Agent",
            "workflow_type": result["workflow_type"],
            "execution_path": result["execution_path"],
            "sources": [],
            "confidence": None
        }
    else:
        reply, sources, confidence, agent_name = supervisor_agent.route_and_resolve(
            message=message,
            use_rag=use_rag,
            top_k=top_k
        )
        agent_type = agent_name.lower().split(" ")[0] if agent_name else None
        res_confidence = confidence if agent_type == "rag" else None
        return {
            "reply": reply,
            "selected_agent": agent_name,
            "workflow_type": None,
            "execution_path": [],
            "sources": sources,
            "confidence": res_confidence
        }


def run_test_cases():
    test_cases = [
        # Phase 4 Simple Routing Cases
        {
            "query": "What is our PTO policy?",
            "expected_agent": "HR Agent",
            "expected_workflow": None,
            "expected_path": []
        },
        {
            "query": "How do I submit an expense report?",
            "expected_agent": "Finance Agent",
            "expected_workflow": None,
            "expected_path": []
        },
        {
            "query": "My VPN is not working.",
            "expected_agent": "IT Agent",
            "expected_workflow": None,
            "expected_path": []
        },
        {
            "query": "Summarize the uploaded Transformer paper.",
            "expected_agent": "RAG Agent",
            "expected_workflow": None,
            "expected_path": []
        },
        # Phase 5 Multi-Agent Workflow Cases
        {
            "query": "Create onboarding plan for a new employee",
            "expected_agent": "Supervisor Agent",
            "expected_workflow": "onboarding",
            "expected_path": ["Supervisor Agent", "HR Agent", "IT Agent", "Finance Agent", "Supervisor Agent"]
        },
        {
            "query": "Prepare travel reimbursement plan",
            "expected_agent": "Supervisor Agent",
            "expected_workflow": "travel",
            "expected_path": ["Supervisor Agent", "Finance Agent", "HR Agent", "Supervisor Agent"]
        },
        {
            "query": "Create cross-functional employee setup plan",
            "expected_agent": "Supervisor Agent",
            "expected_workflow": "cross_functional",
            "expected_path": ["Supervisor Agent", "HR Agent", "IT Agent", "Finance Agent", "Supervisor Agent"]
        }
    ]

    print("=" * 60)
    print("STARTING PHASE 5 LANGGRAPH + A2A INTEGRATION TESTS")
    print("=" * 60)

    passed_count = 0

    for idx, tc in enumerate(test_cases, 1):
        query = tc["query"]
        expected_agent = tc["expected_agent"]
        expected_wf = tc["expected_workflow"]
        expected_path = tc["expected_path"]
        
        print(f"\n[Test {idx}] Query: '{query}'")
        print(f"Expected Agent:     {expected_agent}")
        print(f"Expected Workflow:  {expected_wf}")
        print(f"Expected Path:      {expected_path}")
        
        if idx > 1:
            print("Sleeping for 15 seconds to avoid API rate limits (Free Tier)...")
            time.sleep(15)
        
        try:
            res = process_chat(query, use_rag=True, top_k=4)
            print(f"Actual Agent:       {res['selected_agent']}")
            print(f"Actual Workflow:    {res['workflow_type']}")
            print(f"Actual Path:        {res['execution_path']}")
            print(f"Reply Snippet:      {res['reply'][:120]}...")
            
            # Verification rules
            agent_matches = res["selected_agent"] == expected_agent
            wf_matches = res["workflow_type"] == expected_wf
            
            # Path matches (if it is a workflow, verify path tags exist)
            path_matches = True
            if expected_path:
                path_matches = res["execution_path"] == expected_path

            if agent_matches and wf_matches and path_matches:
                print("Result:             SUCCESS [PASS]")
                passed_count += 1
            else:
                print("Result:             FAILED [FAIL] (Mismatch details:")
                if not agent_matches:
                    print(f"  - Agent mismatch: {res['selected_agent']} != {expected_agent}")
                if not wf_matches:
                    print(f"  - Workflow mismatch: {res['workflow_type']} != {expected_wf}")
                if not path_matches:
                    print(f"  - Path mismatch: {res['execution_path']} != {expected_path}")
                print(")")
        except Exception as e:
            print(f"Result:             FAILED [FAIL] (Error occurred: {e})")

    print("\n" + "=" * 60)
    print(f"TEST RUN COMPLETED: {passed_count}/{len(test_cases)} Passed")
    print("=" * 60)

    if passed_count == len(test_cases):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    run_test_cases()
