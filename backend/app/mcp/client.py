import sys
import os
import json
import subprocess
from app.core.logger import get_logger

logger = get_logger(__name__)

class MCPClient:
    def __init__(self, server_script_name: str, http_url: str = None) -> None:
        self.server_script_name = server_script_name
        self.http_url = http_url
        self.process = None
        self.req_id = 0

    def start(self):
        """Starts the server process if it's not already running (for stdio mode)."""
        if self.http_url:
            return
            
        if self.process is None or self.process.poll() is not None:
            server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.server_script_name)
            logger.info("Starting MCP server: %s", server_path)
            
            # Spawn the subprocess using the current python executable to ensure virtual env consistency
            self.process = subprocess.Popen(
                [sys.executable, server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Send initial initialize handshake
            try:
                self.send_request("initialize", {})
            except Exception as e:
                logger.error("Failed to initialize MCP server '%s': %s", self.server_script_name, e)
                self.stop()
                raise e

    def send_request(self, method: str, params: dict) -> dict:
        self.start()
        self.req_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params
        }
        
        if self.http_url:
            import urllib.request
            import urllib.error
            try:
                req_data = json.dumps(req).encode('utf-8')
                http_req = urllib.request.Request(
                    self.http_url,
                    data=req_data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(http_req, timeout=15) as response:
                    resp_data = response.read().decode('utf-8')
                    resp = json.loads(resp_data.strip())
                    if "error" in resp:
                        raise RuntimeError(resp["error"].get("message", "Unknown JSON-RPC error"))
                    return resp.get("result", {})
            except Exception as e:
                logger.exception("MCP client HTTP call error to '%s': %s", self.http_url, e)
                raise e
        else:
            try:
                req_str = json.dumps(req)
                self.process.stdin.write(req_str + "\n")
                self.process.stdin.flush()
                
                # Read one line of response
                line = self.process.stdout.readline()
                if not line:
                    # Check stderr for diagnostic details
                    stderr_diag = ""
                    try:
                        stderr_diag = self.process.stderr.readline()
                    except:
                        pass
                    raise RuntimeError(f"MCP server stream closed unexpectedly. Stderr: {stderr_diag}")
                    
                resp = json.loads(line.strip())
                if "error" in resp:
                    raise RuntimeError(resp["error"].get("message", "Unknown JSON-RPC error"))
                return resp.get("result", {})
            except Exception as e:
                logger.exception("MCP client call error in '%s': %s", self.server_script_name, e)
                self.stop()
                raise e

    def stop(self):
        """Safely stops the subprocess."""
        if self.process:
            logger.info("Stopping MCP server: %s", self.server_script_name)
            try:
                self.process.stdin.close()
            except:
                pass
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                pass
            self.process = None


class MCPClientManager:
    def __init__(self) -> None:
        self.clients = {
            "employee-db-mcp": MCPClient("employee_db_server.py", os.environ.get("EMPLOYEE_DB_MCP_URL")),
            "ticket-mcp": MCPClient("ticket_server.py", os.environ.get("TICKET_MCP_URL")),
            "document-search-mcp": MCPClient("document_server.py", os.environ.get("DOCUMENT_MCP_URL"))
        }

    def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> dict:
        client = self.clients.get(server_name)
        if not client:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        # Execute the tools/call method
        response_result = client.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        # Decode contents: response_result is {"content": [{"type": "text", "text": "..."}]}
        contents = response_result.get("content", [])
        if contents and contents[0].get("type") == "text":
            return json.loads(contents[0]["text"])
        return response_result

    def shutdown(self):
        for name, client in self.clients.items():
            client.stop()


# Shared singleton client manager
mcp_client_manager = MCPClientManager()
