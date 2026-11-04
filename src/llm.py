from __future__ import annotations

import os


def summarize_with_langchain(
    api_key: str,
    previous_summary: str,
    user_message: str,
    assistant_message: str,
) -> str:
    from langchain_classic.memory import ConversationSummaryMemory
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=api_key,
        temperature=0,
    )
    memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="summary",
        input_key="input",
        output_key="output",
    )
    memory.moving_summary_buffer = previous_summary
    memory.save_context({"input": user_message}, {"output": assistant_message})
    return str(memory.load_memory_variables({})["summary"])


def langchain_is_configured() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))
