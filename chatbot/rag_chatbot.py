import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from typing import List, Dict, Any, Optional
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

class ChatSession:
    """
    Maintains chat history and handles RAG-based QA for a single user session.
    """
    def __init__(self):
        self.history: List[Dict[str, str]] = []  # Each entry: {"role": "user"/"assistant", "content": str}
        self.vector_store = VectorStore()

    def add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history_str(self) -> str:
        """
        Returns the chat history as a formatted string for prompt context.
        """
        return "\n".join(
            [f"{entry['role'].capitalize()}: {entry['content']}" for entry in self.history]
        )

    def refine_query(self, user_question: str) -> str:
        """
        Optionally refines the user question using chat history.
        """
        if not self.history:
            return user_question
        # Simple concatenation; can be replaced with more advanced context-aware refinement
        return f"Given the previous conversation: {self.get_history_str()}\nUser's new question: {user_question}"

    def ask(self, user_question: str, filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handles a user question, retrieves context, and generates an answer.
        """
        # Add user question to history
        self.add_to_history("user", user_question)

        # Refine the question with history
        refined_question = self.refine_query(user_question)

        # Retrieve relevant context from vector DB
        context_products = self.vector_store.query_products(
            query=refined_question,
            filter_dict=filter_dict
        )

        # Build the RAG prompt
        context_str = "\n".join([
            f"Product: {prod.get('name', '')}\nDescription: {prod.get('description', '')}\n"
            f"Price: ${prod.get('price_value', 0):.2f}\nLocation: {prod.get('location', '')}\n"
            for prod in context_products
        ])
        prompt = (
            "You are a helpful cheese expert assistant. Use the following product information and the chat history to answer the user's question. "
            "If the answer is not in the context, say so. Always cite the specific products you reference.\n\n"
            f"Chat History:\n{self.get_history_str()}\n\n"
            f"Context:\n{context_str}\n\n"
            f"User Question: {user_question}\n\n"
            "Please provide a detailed answer based on the product information above:"
        )

        # Get answer from GPT
        response = self.vector_store.client.chat.completions.create(
            model=self.vector_store.client.model if hasattr(self.vector_store.client, 'model') else "gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful cheese expert assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        answer = response.choices[0].message.content

        # Add answer to history
        self.add_to_history("assistant", answer)

        return {
            "answer": answer,
            "context": context_products,
            "history": self.history
        }

# Example usage
if __name__ == "__main__":
    session = ChatSession()
    print("Welcome to the Cheese RAG ChatBot!")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        result = session.ask(user_input)
        print("\nBot:", result["answer"])
        print("\nReference Context:", result["context"])