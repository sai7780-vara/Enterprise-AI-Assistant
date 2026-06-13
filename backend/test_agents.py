import sys
import os

# Ensure the parent directory of backend/app is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.agents.supervisor_agent import supervisor_agent


def run_test_cases():
    test_cases = [
        {
            "query": "What is our PTO policy?",
            "expected_agent": "HR Agent"
        },
        {
            "query": "How do I submit an expense report?",
            "expected_agent": "Finance Agent"
        },
        {
            "query": "My VPN is not working.",
            "expected_agent": "IT Agent"
        },
        {
            "query": "Summarize the uploaded Transformer paper.",
            "expected_agent": "RAG Agent"
        }
    ]

    print("=" * 60)
    print("STARTING PHASE 4 AGENT ARCHITECTURE ROUTING TESTS")
    print("=" * 60)

    passed_count = 0

    for idx, tc in enumerate(test_cases, 1):
        query = tc["query"]
        expected = tc["expected_agent"]
        print(f"\n[Test {idx}] Query: '{query}'")
        print(f"Expected Agent: {expected}")
        
        if idx > 1:
            print("Sleeping for 15 seconds to avoid API rate limits (Free Tier)...")
            import time
            time.sleep(15)
        
        try:
            # We call supervisor_agent.route_and_resolve
            reply, sources, confidence, agent_name = supervisor_agent.route_and_resolve(
                message=query,
                use_rag=True,
                top_k=4
            )
            print(f"Actual Agent:   {agent_name}")
            print(f"Confidence:     {confidence}%")
            print(f"Sources Count:  {len(sources)}")
            print(f"Reply Snippet:  {reply[:120]}...")

            if agent_name == expected:
                print("Result:         SUCCESS [PASS]")
                passed_count += 1
            else:
                print("Result:         FAILED [FAIL] (Mismatch)")
        except Exception as e:
            print(f"Result:         FAILED [FAIL] (Error occurred: {e})")

    print("\n" + "=" * 60)
    print(f"TEST RUN COMPLETED: {passed_count}/{len(test_cases)} Passed")
    print("=" * 60)

    if passed_count == len(test_cases):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    run_test_cases()
