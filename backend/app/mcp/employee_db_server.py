import sys
import json
import sqlite3
import os
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

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employee.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    # Check if empty to pre-populate
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        test_employees = [
            (101, "Sai Kiran", "Engineering", "sai.kiran@enterprise.com", "Senior Software Engineer"),
            (102, "Jane Smith", "HR", "jane.smith@enterprise.com", "HR Manager"),
            (103, "John Doe", "Finance", "john.doe@enterprise.com", "Financial Analyst")
        ]
        cursor.executemany("INSERT INTO employees (id, name, department, email, role) VALUES (?, ?, ?, ?, ?)", test_employees)
        conn.commit()
    conn.close()

def get_employee(emp_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def search_employee(name):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE name LIKE ?", (f"%{name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_employee(name, department, email, role):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, department, email, role) VALUES (?, ?, ?, ?)",
        (name, department, email, role)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "name": name, "status": "Created"}

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
                "serverInfo": {"name": "employee-db-mcp", "version": "1.0.0"}
            }
        }
        
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "get_employee",
                        "description": "Get employee details by their integer ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"id": {"type": "integer"}},
                            "required": ["id"]
                        }
                    },
                    {
                        "name": "search_employee",
                        "description": "Search employees by name substring match.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "create_employee",
                        "description": "Create a new employee profile in the database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "department": {"type": "string"},
                                "email": {"type": "string"},
                                "role": {"type": "string"}
                            },
                            "required": ["name", "department", "email", "role"]
                        }
                    }
                ]
            }
        }
        
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        try:
            if tool_name == "get_employee":
                result = get_employee(int(args.get("id")))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            elif tool_name == "search_employee":
                result = search_employee(args.get("name"))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            elif tool_name == "create_employee":
                result = create_employee(
                    args.get("name"),
                    args.get("department"),
                    args.get("email"),
                    args.get("role")
                )
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
    # Read from stdin line by line
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
            # Send standard error if parsing fails
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
