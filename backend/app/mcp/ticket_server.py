import sys
import json
import sqlite3
import os
import random
import logging

# Configure logging to sys.stderr to avoid stdout corruption
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Ensure the parent of backend/app is in PYTHONPATH to import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    # Prevent app.core.logger from resetting basicConfig to sys.stdout if imported later
    import app.core.logger as app_logger
    app_logger._configured = True
except ImportError:
    pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ticket.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_ticket(title, description, priority):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ticket_num = random.randint(1000, 9999)
    ticket_id = f"TCK-{ticket_num}"
    status = "Open"
    
    cursor.execute(
        "INSERT INTO tickets (ticket_id, title, description, priority, status) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, title, description, priority, status)
    )
    conn.commit()
    conn.close()
    
    return {
        "ticket_id": ticket_id,
        "title": title,
        "status": status,
        "priority": priority
    }

def get_ticket_status(ticket_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "ticket-mcp", "version": "1.0.0"}
            }
        }
        
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "create_ticket",
                        "description": "Create a new IT support ticket.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string"}
                            },
                            "required": ["title", "description", "priority"]
                        }
                    },
                    {
                        "name": "get_ticket_status",
                        "description": "Get status details of an IT ticket using its ID (e.g. TCK-1234).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ticket_id": {"type": "string"}
                            },
                            "required": ["ticket_id"]
                        }
                    }
                ]
            }
        }
        
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        try:
            if tool_name == "create_ticket":
                result = create_ticket(
                    args.get("title"),
                    args.get("description"),
                    args.get("priority")
                )
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            elif tool_name == "get_ticket_status":
                result = get_ticket_status(args.get("ticket_id"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."}
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }
            
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found."}
    }

def main():
    init_db()
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line.strip())
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
