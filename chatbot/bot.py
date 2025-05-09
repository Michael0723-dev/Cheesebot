import sys
import os
from chatbot.retriver.data_retriver import VectorStore
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from typing import List, Dict, Any, Optional

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
        context_products = []
        # Refine the question with history
        refined_question = self.refine_query(user_question)

        # Retrieve relevant context from vector DB
        result = self.vector_store.get_relevant_products(
            query=refined_question,
            filter_dict=filter_dict
        )
        if result.get('response') == "this is not a question about cheese, general question":
            prompt = (
                "The user's question now is one that is difficult to answer accurately with a chatbot using the Pinecone vector database. For example, it may be a greeting that is not related to the exact information about cheese, or it may be a question that is difficult to answer accurately with a semantic search using the vector database, such as the most expensive or softest product, or the heaviest product."
                "Also, it may be a question about a different field that cannot be considered a question from a user using this chatbot to know about cheese. Therefore, you should consider the previous conversation history and give an accurate answer. If it is a content that is connected to a previous conversation, you should consider the context and give an accurate answer."
                "However, if it is a completely different question, you should not answer."
                "Think about it again, General questions can be of various types."
                "-If the question is a question that does not guarantee the accuracy of search using the vector database, such as an exact numeric value or string search. In this case, you should answer it simply and clearly, appropriately to the situation, such as e.g. I am a chatbot using the vector database, so I cannot answer these questions accurately. Please wait for the next version."
                "-If the question is not a question appropriate for users visiting the cheese sales site, you should not answer it accurately."
                f"Chat History:\n{self.get_history_str()}\n\n"
                f"User Question: {user_question}\n\n"
                "Please answer kindly."
            )
        else:
            # Extract context products from the result
            context_products = result.get('context', [])

            # Build the RAG prompt
            context_str = "\n".join([
                f"Description: {prod.get('description', '')}\n"
                for prod in context_products if isinstance(prod, dict)
            ])

            prompt = (
                "You are a helpful cheese expert assistant. Use the following product information and the chat history to answer the user's question. "
                "If the answer is not in the context, say so. Always cite the specific products you reference.\n\n"
                f"Chat History:\n{self.get_history_str()}\n\n"
                f"Context:\n{context_str}\n\n"
                f"User Question: {user_question}\n\n"
                "Please provide a detailed answer based on the product information above:"
            )


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


        self.add_to_history("assistant", answer)

        return {
            "answer": answer,
            "context": context_products,
            "history": self.history
        }


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