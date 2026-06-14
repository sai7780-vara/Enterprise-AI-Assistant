import sys
import os

# Ensure the parent of backend/app is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools import employee_tool, ticket_tool, document_tool
from app.mcp.client import mcp_client_manager

def run_tests():
    print("=" * 60)
    print("STARTING PHASE 6 DIRECT MCP TOOL TESTS")
    print("=" * 60)
    
    passed_count = 0
    total_tests = 5
    
    # Test 1: get_employee(101)
    print("\n[Test 1] employee_tool.get_employee(101)")
    try:
        res = employee_tool.get_employee(101)
        print("Result:", res)
        assert res["success"] is True
        assert res["selected_tool"] == "get_employee"
        assert res["mcp_server"] == "employee-db-mcp"
        assert res["data"]["name"] == "Sai Kiran"
        print("Result: PASS")
        passed_count += 1
    except Exception as e:
        print("Result: FAIL (Error:", e, ")")

    # Test 2: search_employee("Sai")
    print("\n[Test 2] employee_tool.search_employee('Sai')")
    try:
        res = employee_tool.search_employee("Sai")
        print("Result:", res)
        assert res["success"] is True
        assert res["selected_tool"] == "search_employee"
        assert res["mcp_server"] == "employee-db-mcp"
        assert len(res["data"]) > 0
        assert res["data"][0]["name"] == "Sai Kiran"
        print("Result: PASS")
        passed_count += 1
    except Exception as e:
        print("Result: FAIL (Error:", e, ")")

    # Test 3: ticket_tool.create_ticket
    print("\n[Test 3] ticket_tool.create_ticket(...)")
    ticket_id = None
    try:
        res = ticket_tool.create_ticket(
            title="VPN Issue",
            description="My VPN fails to authenticate.",
            priority="High"
        )
        print("Result:", res)
        assert res["success"] is True
        assert res["selected_tool"] == "create_ticket"
        assert res["mcp_server"] == "ticket-mcp"
        ticket_id = res["data"]["ticket_id"]
        assert ticket_id.startswith("TCK-")
        assert res["data"]["priority"] == "High"
        print("Result: PASS")
        passed_count += 1
    except Exception as e:
        print("Result: FAIL (Error:", e, ")")

    # Test 4: ticket_tool.get_ticket_status
    print("\n[Test 4] ticket_tool.get_ticket_status(...)")
    if ticket_id:
        try:
            res = ticket_tool.get_ticket_status(ticket_id)
            print("Result:", res)
            assert res["success"] is True
            assert res["selected_tool"] == "get_ticket_status"
            assert res["mcp_server"] == "ticket-mcp"
            assert res["data"]["ticket_id"] == ticket_id
            print("Result: PASS")
            passed_count += 1
        except Exception as e:
            print("Result: FAIL (Error:", e, ")")
    else:
        print("Skipping Test 4: create_ticket failed first.")

    # Test 5: document_tool.search_documents
    print("\n[Test 5] document_tool.search_documents(...)")
    try:
        # Search for any string, should return successfully (even if empty chunks)
        res = document_tool.search_documents("Transformer", 4)
        print("Result:", res)
        assert res["success"] is True
        assert res["selected_tool"] == "search_documents"
        assert res["mcp_server"] == "document-search-mcp"
        print("Result: PASS")
        passed_count += 1
    except Exception as e:
        print("Result: FAIL (Error:", e, ")")

    # Shut down subprocesses
    mcp_client_manager.shutdown()

    print("\n" + "=" * 60)
    print(f"DIRECT MCP TOOL TESTS COMPLETED: {passed_count}/{total_tests} Passed")
    print("=" * 60)
    
    if passed_count == total_tests:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
