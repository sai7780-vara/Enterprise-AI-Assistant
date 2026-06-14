from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    message: str
    use_rag: bool
    top_k: int
    execution_path: List[str]
    remaining_steps: List[str]
    next_agent: Optional[str]
    
    # Specialist responses
    hr_response: Optional[str]
    finance_response: Optional[str]
    it_response: Optional[str]
    rag_response: Optional[str]
    
    # Tool execution details
    selected_tool: Optional[str]
    mcp_server: Optional[str]
    
    # RAG metadata
    sources: List[dict]
    confidence: Optional[float]
    
    # Outputs
    final_reply: Optional[str]
    workflow_type: Optional[str]  # onboarding, travel, cross_functional
