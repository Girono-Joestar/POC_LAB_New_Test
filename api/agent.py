"""
agent.py — LangChain-powered lab assistant agent with memory and RAG context.

Each lab gets conversational assistance with access to experiment details and FAISS retriever context.
The agent is conversational, friendly, and NOT bot-like.

Token & Speed optimization:
- Direct context injection: Experiment details + RAG docs + Chat History -> Single LLM turn
- Fast response (<1 sec) without ReAct iteration loop overhead or parsing errors
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("poc_ai_lab.agent")

# Per-lab agent executor cache
_agents: Dict[str, object] = {}


def _make_llm(api_key: str, model: str = "meta/llama-3.1-70b-instruct"):
    """Create the underlying LLM using ChatNVIDIA."""
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from api.rate_limiter import llm_limiter

    # Apply rate limiting before creating/using the LLM
    llm_limiter.wait()

    return ChatNVIDIA(
        model=model,
        nvidia_api_key=api_key,
        temperature=0.35,
        max_tokens=800,
    )


def _make_system_prompt() -> str:
    return """You are a knowledgeable and enthusiastic lab guide for the Metrology and Quality Control Laboratory at MES College of Engineering, Pune.

Your personality:
- Warm, encouraging, and patient — you enjoy helping students understand complex concepts.
- Explain things clearly, using analogies when helpful. Avoid jargon without explaining it.
- When students make mistakes in their reasoning, gently correct them and explain why.
- You never respond with raw bullet points alone — always add a short conversational sentence to introduce or conclude lists.
- You are NOT a chatbot that reads scripts. You think, reason, and explain like a helpful senior student or lab demonstrator.
- Keep responses concise — 3–6 sentences for simple questions, and up to 2 short paragraphs for complex ones.
- If asked something outside the lab experiment context, politely say you're focused on this lab but can help with related metrology topics.

Use the provided Experiment Details and Knowledge Base context below to answer student questions accurately."""


def _get_experiment_context(exp_id: str, exp_data: dict) -> str:
    """Build a rich, structured text context about the current experiment."""
    lines = [
        f"EXPERIMENT ID: {exp_id}",
        f"APPARATUS: {exp_data.get('apparatus', 'N/A')}",
        f"DESCRIPTION: {exp_data.get('short_desc', '')}",
    ]
    
    objectives = exp_data.get("objectives", [])
    if objectives:
        lines.append("OBJECTIVES:\n- " + "\n- ".join(objectives))
    
    formulas = exp_data.get("formulas", [])
    if formulas:
        lines.append("FORMULAS:\n- " + "\n- ".join(formulas))
    
    key_points = exp_data.get("key_points", [])
    if key_points:
        lines.append("KEY POINTS:\n- " + "\n- ".join(key_points))
        
    procedure = exp_data.get("procedure", [])
    if procedure:
        if isinstance(procedure, list):
            lines.append("PROCEDURE STEPS:\n- " + "\n- ".join([str(p) for p in procedure]))
        elif isinstance(procedure, dict):
            proc_lines = []
            for k, v in procedure.items():
                proc_lines.append(f"{k}: {v}")
            lines.append("PROCEDURE:\n" + "\n".join(proc_lines))

    theory = exp_data.get("theory", {})
    if theory and isinstance(theory, dict):
        theory_lines = []
        for k, v in theory.items():
            theory_lines.append(f"{k}: {v}")
        lines.append("THEORY:\n" + "\n".join(theory_lines))

    return "\n\n".join(lines)[:3500]


def run_agent(
    lab_id: str,
    exp_id: str,
    exp_data: dict,
    api_key: str,
    retriever,
    session_id: str,
    user_message: str,
    history: Optional[list] = None,
) -> str:
    """
    Run one turn of the agent conversation with full context and chat history.
    """
    logger.info("🤖 Agent run — lab=%s exp=%s session=%s", lab_id, exp_id, session_id)
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        llm = _make_llm(api_key)

        # 1. Gather Experiment Context
        exp_context = _get_experiment_context(exp_id, exp_data)

        # 2. RAG Retrieval (if available)
        rag_context = ""
        if retriever is not None:
            try:
                docs = retriever.invoke(user_message)
                if docs:
                    rag_chunks = [d.page_content for d in docs]
                    rag_context = "\n\n---\n\n".join(rag_chunks)[:2500]
            except Exception as e:
                logger.warning("RAG retrieval warning: %s", e)

        # 3. Construct System Prompt with Context
        system_content = _make_system_prompt()
        system_content += f"\n\n=== CURRENT EXPERIMENT DATA ===\n{exp_context}"
        if rag_context:
            system_content += f"\n\n=== ADDITIONAL KNOWLEDGE BASE CONTEXT ===\n{rag_context}"

        messages = [SystemMessage(content=system_content)]

        # 4. Add Chat History (up to last 10 messages)
        if history:
            recent = history[-10:]
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if not content:
                    continue
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))

        # 5. Add Current User Message
        messages.append(HumanMessage(content=user_message))

        # 6. Invoke LLM
        response = llm.invoke(messages)
        result = response.content.strip()
        logger.info("✅ Agent replied — %d chars", len(result))
        return result

    except Exception as e:
        logger.error("❌ Agent error: %s", e)
        return (
            "I ran into a little hiccup processing that question. "
            "Could you try asking again or rephrasing? I'm here to help!"
        )
