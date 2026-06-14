# Phase 4 Learning Guide — Agent Architecture

## 1. What Problem Was Not Solved in the Previous Phase
In Phase 3, we built a highly capable RAG chat engine. However:
- The backend had a single generic prompt.
- We could not route queries to domain experts (e.g. IT support, HR benefits, Finance accounting).
- Ingesting all company manuals, policies, and code rules into one massive prompt would blow out token costs and lead to dilution (the model getting confused by irrelevant instructions).
- There was no safety net if the Gemini API hit rate limits (Free Tier quota issues).

## 2. Why This Phase Was Needed
To handle complex enterprise environments, we need a modular, multi-agent setup. Different tasks require different prompts and specialized expertise. 

By separating instructions into standalone "specialist agents" coordinated by a central "Supervisor Agent", we:
- Keep prompts small, highly focused, and accurate.
- Reduce token consumption.
- Allow independent development and testing of individual agents.
- Handle API failures gracefully by automatically rotating models.

## 3. Technical Skills Used in This Phase
* **Multi-Agent Routing:** Classifying queries dynamically using a zero-shot classification prompt.
* **Task Specialization:** Structuring LLM roleplay prompts (system instructions) for distinct expert personas.
* **Error Handling & Quota Safeguards:** Catching HTTP `429 (ResourceExhausted)` errors programmatically and executing fallback recovery routines.
* **Model Rotation:** Maintaining an array of models and dynamically switching to a backup model when the active one fails.
* **API Schema Extensions:** Modifying Pydantic schemas to pass agent execution metadata (`selected_agent`, `agent_type`) from the server to the client.

## 4. What Was Implemented in This Phase
* **Supervisor Agent:** Receives the query, classifies it into `HR`, `FINANCE`, `IT`, or `RAG`, and routes it.
* **Specialist Domain Agents:** 
  - `HRAgent` — expert on leaves, benefits, handbooks.
  - `FinanceAgent` — expert on expenses, invoicing, budgets.
  - `ITAgent` — expert on access, VPN, hardware.
  - `RagAgent` — delegates directly to Phase 3 RAG pipeline for document querying.
* **Model Rotation Service:** `gemini_service.py` rotates from `gemini-3.5-flash` to fallbacks (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-2.5-pro`, `gemini-2.0-flash-lite`) on rate limits.
* **Department Badges in UI:** Displays stylized emoji badges (👔 HR Agent, 💰 Finance Agent, 💻 IT Agent, 🔍 RAG Agent) indicating which agent resolved the query.

## 5. What This Phase Still Cannot Do
* **No Collaboration (A2A):** Agents cannot talk to each other. For example, if a user requests a new employee setup, the HR Agent cannot pass rules to the IT Agent to configure access.
* **No Stateful Workflows:** It cannot run multi-step sequential tasks (e.g., HR ➜ IT ➜ Finance).
* **No External Data Writes:** The IT Agent cannot log a real ticket, and the HR Agent cannot look up employee databases; they only answer questions.

## 6. What is Moved to the Next Phase
In **Phase 5 (LangGraph + A2A)**, we will solve the collaboration and state problems by:
- Orchestrating agent nodes with a LangGraph StateGraph.
- Storing intermediate results in a shared graph state dictionary.
- Enabling Agent-to-Agent (A2A) communication where downstream agents read inputs from upstream agents.
- Executing multi-department workflows (onboarding plans, travel calculations) in a cyclic state machine.

---

## 7. Beginner-Friendly Questions & Answers

### Q1: What is the difference between an Agent and a standard LLM function?
**A:** A standard LLM function takes text, calls the model, and returns text. An "Agent" is a specialized wrapper that couples the LLM with a specific system instruction (defining its persona, rules, and restrictions) and, in future phases, a set of tools (database functions, APIs) that it can choose to execute.

### Q2: Why is classification routing preferred over sending everything to one big prompt?
**A:** If you merge HR handbook guidelines, IT network protocols, and Finance invoicing rules into a single prompt, the instruction context becomes massive. This leads to higher API costs, slower response times, and increased risk of the LLM mixing up department policies. Routing isolates the context, ensuring high accuracy.

### Q3: What is "model rotation" and why is it useful?
**A:** Model rotation is a failover strategy. If a model fails due to a network timeout or rate limit exhaustion (HTTP 429), the code catches the exception, sleeps briefly, switches to a different model version (e.g., rotating from `gemini-3.5-flash` to `gemini-2.5-flash`), and retries the request. This keeps the application responsive.

### Q4: How does the Supervisor Agent decide where to route a query?
**A:** The Supervisor sends a classification prompt to Gemini that lists descriptions of each specialist agent. It asks the model to respond with exactly one classification string: `HR`, `FINANCE`, `IT`, or `RAG`. The Supervisor then reads this word and triggers the corresponding Python agent.

### Q5: What is a zero-shot prompt?
**A:** A zero-shot prompt is an instruction sent to an LLM without giving it any example inputs and outputs. We simply define the task (e.g. "Classify this text into HR, IT, or FINANCE") and rely on the model's pre-trained understanding to perform the task correctly.
