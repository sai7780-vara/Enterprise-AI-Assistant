from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.core.logger import get_logger

logger = get_logger(__name__)


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph: Supervisor Node running...")
    
    execution_path = list(state.get("execution_path", []))
    remaining_steps = list(state.get("remaining_steps", []))
    wtype = state.get("workflow_type")
    
    # 1. Initialize steps if first execution
    if not wtype:
        execution_path.append("Supervisor Agent")
        msg = state["message"].lower()
        if "onboarding" in msg or "new employee" in msg:
            wtype = "onboarding"
            remaining_steps = ["HR", "IT", "FINANCE"]
        elif "travel" in msg or "reimbursement" in msg:
            wtype = "travel"
            remaining_steps = ["FINANCE", "HR"]
        elif "cross-functional" in msg or "cross functional" in msg:
            wtype = "cross_functional"
            remaining_steps = ["HR", "IT", "FINANCE"]
        else:
            wtype = "generic_workflow"
            remaining_steps = ["HR", "IT", "FINANCE"]
            
        logger.info(f"LangGraph: Initializing workflow '{wtype}' with steps: {remaining_steps}")
        next_agent = remaining_steps[0]
        remaining_steps = remaining_steps[1:]
        
        return {
            "workflow_type": wtype,
            "remaining_steps": remaining_steps,
            "next_agent": next_agent,
            "execution_path": execution_path
        }
        
    # 2. Subsequent entries: check if any steps remain
    if remaining_steps:
        next_agent = remaining_steps[0]
        remaining_steps = remaining_steps[1:]
        logger.info(f"LangGraph: Routing to next step '{next_agent}'. Remaining: {remaining_steps}")
        return {
            "remaining_steps": remaining_steps,
            "next_agent": next_agent
        }
        
    # 3. All steps completed: Synthesize the final result
    logger.info("LangGraph: Synthesizing final multi-agent response...")
    execution_path.append("Supervisor Agent")
    from app.services.gemini_service import gemini_service
    
    hr_res = state.get("hr_response") or ""
    it_res = state.get("it_response") or ""
    fin_res = state.get("finance_response") or ""
    
    synthesis_prompt = (
        f"You are the Supervisor Agent. Combine and synthesize a professional and comprehensive final summary plan "
        f"for the user's request: '{state['message']}' by aligning the departments' individual outputs.\n\n"
        "Department Specific Plans gathered:\n"
    )
    if hr_res:
        synthesis_prompt += f"--- HR Department Requirements ---\n{hr_res}\n\n"
    if it_res:
        synthesis_prompt += f"--- IT Department Requirements ---\n{it_res}\n\n"
    if fin_res:
        synthesis_prompt += f"--- Finance Department Requirements ---\n{fin_res}\n\n"
        
    synthesis_prompt += (
        "Construct a detailed combined report. Include distinct sections for each department. "
        "Formulate it helpfully and clearly.\n"
        "Answer:"
    )
    
    final_reply = gemini_service.generate_reply(synthesis_prompt)
    
    return {
        "final_reply": final_reply,
        "next_agent": "END",
        "execution_path": execution_path
    }


def hr_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph: HR Specialist Node running...")
    from app.agents.hr_agent import hr_agent
    
    reply = hr_agent.handle_query(state["message"], state)
    execution_path = list(state.get("execution_path", []))
    execution_path.append("HR Agent")
    
    return {
        "hr_response": reply,
        "execution_path": execution_path
    }


def finance_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph: Finance Specialist Node running...")
    from app.agents.finance_agent import finance_agent
    
    reply = finance_agent.handle_query(state["message"], state)
    execution_path = list(state.get("execution_path", []))
    execution_path.append("Finance Agent")
    
    return {
        "finance_response": reply,
        "execution_path": execution_path
    }


def it_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph: IT Specialist Node running...")
    from app.agents.it_agent import it_agent
    
    reply = it_agent.handle_query(state["message"], state)
    execution_path = list(state.get("execution_path", []))
    execution_path.append("IT Agent")
    
    return {
        "it_response": reply,
        "execution_path": execution_path
    }


def rag_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph: RAG Specialist Node running...")
    from app.agents.rag_agent import rag_agent
    
    reply, sources, confidence = rag_agent.handle_query(
        state["message"],
        use_rag=state.get("use_rag", True),
        top_k=state.get("top_k", 4)
    )
    execution_path = list(state.get("execution_path", []))
    execution_path.append("RAG Agent")
    
    return {
        "rag_response": reply,
        "sources": sources,
        "confidence": confidence,
        "execution_path": execution_path
    }


def route_next(state: AgentState) -> str:
    next_a = state.get("next_agent")
    if next_a == "HR":
        return "hr"
    elif next_a == "FINANCE":
        return "finance"
    elif next_a == "IT":
        return "it"
    elif next_a == "RAG":
        return "rag"
    else:
        return "end"


# Define Graph structure
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("hr", hr_node)
workflow.add_node("finance", finance_node)
workflow.add_node("it", it_node)
workflow.add_node("rag", rag_node)

# Set entry point
workflow.set_entry_point("supervisor")

# Configure conditional navigation from supervisor
workflow.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "hr": "hr",
        "finance": "finance",
        "it": "it",
        "rag": "rag",
        "end": END
    }
)

# Specialist nodes cycle back to supervisor
workflow.add_edge("hr", "supervisor")
workflow.add_edge("finance", "supervisor")
workflow.add_edge("it", "supervisor")
workflow.add_edge("rag", "supervisor")

app = workflow.compile()
