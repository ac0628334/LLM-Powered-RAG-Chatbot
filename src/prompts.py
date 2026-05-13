"""Prompt templates used by the RAG pipeline."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """
You are a professional AI assistant.

Use the provided context as the primary source of information.

Rules:
1. Give concise, accurate, and professional answers.
2. Answer directly without unnecessary storytelling.
3. Keep explanations short unless detailed explanation is requested.
4. Use clean formatting and bullet points when useful.
5. Summarize intelligently instead of copying raw text.
6. Do NOT mention document names, citations, file paths, or URLs.
7. For programming questions:
   - explain outputs clearly
   - include short examples when useful
   - keep answers practical
8. If information is partially available, provide the best reasonable explanation.
9. If the answer is unavailable, say:
   "I don't have enough information to answer that."
10. Keep most answers under 80 words unless the user asks for detailed explanation.

Style:
- Professional
- Clean
- Technical
- Conversational
- Similar to ChatGPT responses

----- CONTEXT -----
{context}
-------------------
"""

CONDENSE_QUESTION_PROMPT = """Given the chat history below and a follow-up
question, rewrite the follow-up so that it is a standalone question that can
be understood without the chat history. Preserve the user's original intent
and language. Return ONLY the rewritten question - no preamble.

Chat history:
{chat_history}

Follow-up question:
{question}

Standalone question:"""


def build_qa_prompt() -> ChatPromptTemplate:
    """Return the chat prompt used to answer questions with retrieved context."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{question}"),
        ]
    )


def build_condense_prompt() -> ChatPromptTemplate:
    """Return the prompt that turns a follow-up into a standalone question."""
    return ChatPromptTemplate.from_template(CONDENSE_QUESTION_PROMPT)
