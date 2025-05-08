import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from utils.config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        # Initialize OpenAI client
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in config.py")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Initialize Pinecone
        if not Config.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set in config.py")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = self.pc.Index(Config.PINECONE_INDEX_NAME)

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []

    def query_products(
        self,
        query: str,
        top_k: int = Config.TOP_K_RESULTS,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for relevant products
        
        Args:
            query: The search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {'price_value': {'$lt': 20}})
        
        Returns:
            List of relevant products with their metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

            # Process and return results
            products = []
            for match in results.matches:
                product = {
                    'id': match.id,
                    'score': match.score,
                    **match.metadata
                }
                products.append(product)

            return products

        except Exception as e:
            logger.error(f"Error querying products: {str(e)}")
            return []

    def generate_response(
        self,
        query: str,
        context_products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a response using GPT-4 with RAG
        
        Args:
            query: User's question
            context_products: List of relevant products from Pinecone
        
        Returns:
            Dictionary containing the response and reference context
        """
        try:
            # Prepare context from products
            context = []
            for product in context_products:
                product_info = (
                    f"Product: {product['name']}\n"
                    f"Description: {product['description']}\n"
                    f"Price: ${product.get('price_value', 0):.2f}\n"
                    f"Price per lb: ${product.get('price_per_lb', 0):.2f}\n"
                    f"Location: {product.get('location', 'Unknown')}\n"
                    f"Source: {product.get('source_url', 'N/A')}\n"
                )
                context.append(product_info)

            # Create RAG prompt
            prompt = (
                "You are a cheese expert assistant. Use the following product information to answer the user's question.\n"
                "If the information is not in the context, say so. Always cite the specific products you reference.\n\n"
                f"Context:\n{''.join(context)}\n\n"
                f"User Question: {query}\n\n"
                "Please provide a detailed answer based on the product information above:"
            )

            # Generate response
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful cheese expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return {
                'response': response.choices[0].message.content,
                'context': context_products
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error while processing your request.",
                'context': []
            }

    def get_relevant_products(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to get relevant products and generate a response
        
        Args:
            query: User's question
            filter_dict: Optional metadata filters
        
        Returns:
            Dictionary containing the response and reference context
        """
        # Query for relevant products
        products = self.query_products(query, filter_dict=filter_dict)
        
        if not products:
            return {
                'response': "I couldn't find any relevant products to answer your question.",
                'context': []
            }
        
        # Generate response using the products as context
        return self.generate_response(query, products)
    
vector_store = VectorStore()

# Simple query
result = vector_store.get_relevant_products("What are some good Mozzarella cheeses?")

# Query with filters
filters = {
    'price_value': {'$lt': 60},  # Price less than $20
    'location': 'North Beach'      # Only from dairy case
}
result = vector_store.get_relevant_products(
    "What are some affordable Mozzarella cheeses?",
    filter_dict=filters
)

# Access results
print(result['response'])  # The generated answer
print(result['context'])   # The products used as context 