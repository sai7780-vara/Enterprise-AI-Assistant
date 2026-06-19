import sys
import json
import os
import logging

# Configure logging to sys.stderr before importing other app modules to avoid stdout corruption
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Ensure the parent of backend/app is in PYTHONPATH to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Prevent app.core.logger from resetting basicConfig to sys.stdout
import app.core.logger as app_logger
app_logger._configured = True

import google.generativeai as genai
from app.services.vector_store import vector_store
from app.core.config import settings

def search_documents(query, top_k=4):
    try:
        vector_store.load()
    except Exception as e:
        logging.error("Failed to reload vector store: %s", e)
        
    # Check if we have documents
    if len(vector_store.chunk_metadata_map) == 0:
        return {"chunks": [], "confidence": 0.0}
        
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing.")
        
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    embedding_model = settings.GEMINI_EMBEDDING_MODEL
    if not embedding_model.startswith("models/"):
        embedding_model = f"models/{embedding_model}"
        
    query_resp = genai.embed_content(
        model=embedding_model,
        content=query,
        task_type="retrieval_query",
    )
    
    raw_emb = query_resp.get("embedding", [])
    if isinstance(raw_emb, dict) and "values" in raw_emb:
        query_embedding = raw_emb["values"]
    elif isinstance(raw_emb, list):
        if raw_emb and isinstance(raw_emb[0], list):
            query_embedding = raw_emb[0]
        elif raw_emb and isinstance(raw_emb[0], dict) and "values" in raw_emb[0]:
            query_embedding = raw_emb[0]["values"]
        else:
            query_embedding = raw_emb
    else:
        query_embedding = raw_emb
        
    results = vector_store.search(query_embedding, top_k=top_k)
    
    chunks = []
    for meta, score in results:
        chunks.append({
            "doc_id": meta["doc_id"],
            "filename": meta["filename"],
            "text": meta["text"],
            "page_number": meta.get("page_number", 1),
            "chunk_id": meta["chunk_id"],
            "score": float(score)
        })
        
    best_similarity = results[0][1] if results else 0.0
    confidence = min(100.0, max(0.0, best_similarity) * 100.0)
    return {"chunks": chunks, "confidence": round(confidence, 1)}

def get_sources(doc_id):
    docs = vector_store.list_documents()
    for d in docs:
        if d["doc_id"] == doc_id:
            return d
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
                "serverInfo": {"name": "document-search-mcp", "version": "1.0.0"}
            }
        }
        
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_documents",
                        "description": "Search for relevant information chunks in the uploaded document knowledge base.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "top_k": {"type": "integer"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_sources",
                        "description": "Get high-level details of a source document by its ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "doc_id": {"type": "string"}
                            },
                            "required": ["doc_id"]
                        }
                    }
                ]
            }
        }
        
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        try:
            if tool_name == "search_documents":
                top_k = int(args.get("top_k", 4))
                result = search_documents(args.get("query"), top_k)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            elif tool_name == "get_sources":
                result = get_sources(args.get("doc_id"))
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

from http.server import HTTPServer, BaseHTTPRequestHandler

class MCPHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            req = json.loads(post_data.decode('utf-8'))
            resp = handle_request(req)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

def run_http_server(port):
    server = HTTPServer(('0.0.0.0', port), MCPHTTPHandler)
    logging.info("Starting MCP HTTP server on port %d...", port)
    server.serve_forever()

def main():
    port_env = os.environ.get("PORT")
    if port_env:
        try:
            port = int(port_env)
            run_http_server(port)
        except Exception as e:
            logging.error("Failed to run HTTP server on port %s: %s", port_env, e)
            sys.exit(1)
    else:
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
