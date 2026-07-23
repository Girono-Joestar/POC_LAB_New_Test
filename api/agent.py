"""
agent.py — LangChain-powered lab assistant agent with memory and RAG tools.

Each lab gets its own agent instance (cached) with access to its own FAISS retriever.
The agent is conversational, friendly, and NOT bot-like.

Token optimization:
- ConversationBufferWindowMemory — keeps only the last 6 messages
- MMR retrieval — max 5 diverse chunks from the knowledge base
- Experiment context injected only on first message (cached in memory)
- Max context per tool call capped at 3000 chars
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("poc_ai_lab.agent")

# Per-lab agent executor cache
_agents: Dict[str, object] = {}


def _make_llm(api_key: str, model: str = "deepseek-ai/deepseek-v4-pro"):
    """Create the underlying LLM using NVIDIA NIM."""
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from api.rate_limiter import llm_limiter

    # Apply rate limiting before creating/using the LLM
    llm_limiter.wait()

    return ChatNVIDIA(
        model=model,
        nvidia_api_key=api_key,
        temperature=0.35,
        max_tokens=800,
        # chat_template_kwargs={"thinking": True} # Thinking/Reasoning support
    )


def _make_system_prompt() -> str:
    return """You are a knowledgeable and enthusiastic lab guide for the Metrology and Quality Control Laboratory at MES College of Engineering, Pune.

Your personality:
- Warm, encouraging, and patient — you enjoy helping students understand complex concepts.
- Explain things clearly, using analogies when helpful. Avoid jargon without explaining it.
- When students make mistakes in their reasoning, gently correct them and explain why.
- You never respond with bullet points alone — always add a short conversational sentence to introduce or conclude lists.
- You are NOT a chatbot that reads scripts. You think, reason, and explain like a helpful senior student or lab demonstrator.
- Keep responses concise — 3–6 sentences for simple questions, and up to 2 short paragraphs for complex ones.
- If asked something outside the lab experiment context, politely say you're focused on this lab but can help with related metrology topics.

The student is currently viewing a lab experiment. Use the tools available to retrieve accurate, specific information from the knowledge base when needed."""


def _make_tools(exp_id: str, exp_data: dict, retriever) -> list:
    """Create the agent's tool set."""
    from langchain.tools import Tool

    def get_experiment_detail(query: str) -> str:
        """Return structured data about the current experiment."""
        # Return a summary of the experiment data — capped for token efficiency
        lines = [
            f"Experiment ID: {exp_id}",
            f"Apparatus: {exp_data.get('apparatus', 'N/A')}",
            f"Short Description: {exp_data.get('short_desc', '')}",
        ]
        
        objectives = exp_data.get("objectives", [])
        if objectives:
            lines.append("Objectives: " + "; ".join(objectives))
        
        formulas = exp_data.get("formulas", [])
        if formulas:
            lines.append("Key Formulas: " + " | ".join(formulas))
        
        key_points = exp_data.get("key_points", [])
        if key_points:
            lines.append("Key Points: " + "; ".join(key_points[:5]))
        
        return "\n".join(lines)[:2500]

    def search_knowledge(query: str) -> str:
        """Search the lab's knowledge base (RAG) for relevant information."""
        if retriever is None:
            return "Knowledge base is not available right now."
        try:
            docs = retriever.invoke(query)
            if not docs:
                return "No relevant information found for that query."
            
            # Combine and cap at 3000 chars
            combined = "\n\n---\n\n".join(d.page_content for d in docs)
            return combined[:3000]
        except Exception as e:
            logger.error("RAG search error: %s", e)
            return "Knowledge base search encountered an error."

    tools = [
        Tool(
            name="GetExperimentDetail",
            func=get_experiment_detail,
            description=(
                "Use this to look up the current experiment's apparatus, objectives, "
                "key formulas, and key points. Input can be any query about the experiment."
            ),
        ),
        Tool(
            name="SearchLabKnowledge",
            func=search_knowledge,
            description=(
                "Use this to search the broader lab knowledge base (procedures, theory, instrument specs) "
                "for information that goes beyond the basic experiment details. "
                "Input should be a focused question or keyword phrase."
            ),
        ),
    ]
    return tools


def get_or_create_agent(
    lab_id: str,
    exp_id: str,
    exp_data: dict,
    api_key: str,
    retriever,
    session_id: str,
):
    """
    Returns a fresh ConversationChain-compatible agent for a chat session.
    We do NOT cache agents since each session has its own memory.
    """
    try:
        from langchain.agents import initialize_agent, AgentType
        from langchain.memory import ConversationBufferWindowMemory
        
        llm = _make_llm(api_key)
        tools = _make_tools(exp_id, exp_data, retriever)
        
        memory = ConversationBufferWindowMemory(
            k=6,  # keep last 6 exchanges — ~1200 tokens history max
            memory_key="chat_history",
            output_key="output",
            return_messages=True,
        )
        
        # Inject friendly opening context into memory
        apparatus = exp_data.get("apparatus", exp_id)
        memory.chat_memory.add_ai_message(
            f"Hey there! 👋 I'm your lab guide for the MQC Lab. "
            f"You're looking at **{apparatus}**. "
            f"Feel free to ask me anything about this experiment — whether it's theory, "
            f"the procedure, formulas, or anything you're unsure about. I'm here to help!"
        )
        
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=4,  # limit to avoid runaway loops
            agent_kwargs={
                "prefix": _make_system_prompt(),
            },
        )
        
        return agent
        
    except Exception as e:
        logger.error("❌ Failed to create agent for lab %s / exp %s: %s", lab_id, exp_id, e)
        raise


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
    Run one turn of the agent conversation.
    
    history: list of {"role": "user"|"assistant", "content": str}
    Returns the agent's reply as a plain string.
    """
    logger.info("🤖 Agent run — lab=%s exp=%s session=%s", lab_id, exp_id, session_id)
    
    try:
        from langchain.agents import initialize_agent, AgentType
        from langchain.memory import ConversationBufferWindowMemory
        
        llm = _make_llm(api_key)
        tools = _make_tools(exp_id, exp_data, retriever)
        
        memory = ConversationBufferWindowMemory(
            k=6,
            memory_key="chat_history",
            output_key="output",
            return_messages=True,
        )
        
        # Replay history into memory (last 5 turns to limit tokens)
        if history:
            recent = history[-10:]  # max 10 messages = 5 turns
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    memory.chat_memory.add_user_message(content)
                else:
                    memory.chat_memory.add_ai_message(content)
        
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=4,
            agent_kwargs={
                "prefix": _make_system_prompt(),
            },
        )
        
        result = agent.run(input=user_message)
        logger.info("✅ Agent replied — %d chars", len(result))
        return result
        
    except Exception as e:
        logger.error("❌ Agent error: %s", e)
        # Graceful fallback
        return (
            "I ran into a little hiccup on my end — sorry about that! "
            "Could you try rephrasing your question? I'm still here to help."
        )
