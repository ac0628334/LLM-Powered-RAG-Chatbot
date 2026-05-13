# api/chatbot.py

from typing import List, Tuple

class RAGChatbot:
    def ask(self, question: str, chat_history: List[Tuple[str, str]] = None):
        # Dummy response for now
        return ChatbotResponse(answer=f"Echo: {question}")

def get_chatbot():
    # Dependency injection for FastAPI
    return RAGChatbot()

def build_chat_history(pairs: List[Tuple[str, str]]):
    # Just return the pairs for now
    return pairs

def count_documents():
    # Stub: pretend we have documents
    return 1

class ChatbotResponse:
    def __init__(self, answer: str):
        self.answer = answer

    def formatted_sources(self):
        # Return empty sources for now
        return []
