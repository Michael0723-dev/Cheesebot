import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
import sys
from pathlib import Path
import json

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
        
        # Define the function for determining question type
        self.DETERMINEFUNCTION = [{
            "type": "function",
            "function": {
                "name": "determine_question_type",
                "description": "The metadata we use include: cheese_type, brand, cheese_form, price_each, price_per_lb, lb_per_each, case, sku, upc, image_url, source_url. If the answer can be answered accurately through a pinecone vector database search that includes metadata filtering related to these values, then 1 must be output. But if the user's question now is one that is difficult to answer accurately with a chatbot using the Pinecone vector database. For example, it may be a greeting that is not related to the exact information about cheese, or it may be a question that is difficult to answer accurately with a semantic search using the vector database, in this case the output has to be 0, e.g. finding most expensive cheese, or the heaviest product. and also, it may be a question about a different field that cannot be considered a question from a user using this chatbot to know about cheese. In this case function output has to be 0, Otherwise output has to be 1 that is answerable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_cheese_question": {"type": "integer"}
                    },
                    "required": ["is_cheese_question"]
                }
            },
            "strict": True
        }]

        # Initialize Pinecone
        if not Config.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set in config.py")

        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)

            # Check if index exists
            available_indexes = self.pc.list_indexes()
            if Config.PINECONE_INDEX_NAME not in [index.name for index in available_indexes]:
                raise ValueError(f"Index '{Config.PINECONE_INDEX_NAME}' not found in Pinecone. Available indexes: {[index.name for index in available_indexes]}")

            # Connect to index
            self.index = self.pc.Index(Config.PINECONE_INDEX_NAME)

            # Check index stats
            index_stats = self.index.describe_index_stats()
            print(f"Connected to Pinecone index '{Config.PINECONE_INDEX_NAME}'")
            print(f"Index stats: {index_stats}")

            if index_stats.total_vector_count == 0:
                print("Warning: Index is empty! No vectors found.")
            
        except Exception as e:
            logger.error(f"Error connecting to Pinecone: {str(e)}")
            raise

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

            # Log the query details
            print(f"Querying Pinecone with:")
            print(f"- Query: {query}")
            print(f"- Top K: {top_k}")
            print(f"- Filters: {filter_dict}")

            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Log the results
            print(f"Pinecone returned {len(results.matches)} matches")
            
            # Process and return results
            products = []
            for match in results.matches:
                product = {
                    'id': match.id,
                    'score': match.score,
                    **match.metadata
                }
                products.append(product)
                print(f"Match found - ID: {match.id}, Score: {match.score}")

            if not products:
                print("No products found matching the query. This could be due to:")
                print("1. No vectors in the index")
                print("2. Query filters too restrictive")
                print("3. Query not matching any vectors")
                print("4. Index connection issues")

            return products

        except Exception as e:
            logger.error(f"Error querying products: {str(e)}")
            print(f"Error details: {str(e)}")
            return []

    def generate_response(
        self,
        query: str,
        type_of_question: int,
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
        if type_of_question == 1:
            try:
                # Prepare context from products
                context = []
                for product in context_products:
                    product_info = (
                        f"Product: {product['cheese_type']}\n"
                        f"Brand: {product['brand']}\n"
                        f"Form: {product['cheese_form']}\n"
                        f"Description: {product['description']}\n"
                        f"Price: ${product.get('price_each', 0):.2f}\n"
                        f"Price per lb: ${product.get('price_per_lb', 0):.2f}\n"
                        f"Lb per unit: {product.get('lb_per_each', 0):.2f}\n"
                        f"Case: {product.get('case', 'No')}\n"
                        f"Sku: {product.get('sku', 'No')}\n"
                        f"Upc: {product.get('upc', 'No')}\n"
                        f"Image: {product.get('image_url', 'N/A')}\n"
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
                print("response")
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
        else:
            return {
                'response': "this is not a question about cheese, general question",
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
        print(query)
        
        type_of_question = self.client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Here is customer conversation:" + query}],
            tools=self.DETERMINEFUNCTION,
            tool_choice={"type": "function", "function": {"name": "determine_question_type"}}
        )
        print(json.loads(type_of_question.choices[0].message.tool_calls[0].function.arguments)['is_cheese_question'])
        if json.loads(type_of_question.choices[0].message.tool_calls[0].function.arguments)['is_cheese_question'] == 1:
            
            system_message = """You are an expert data engineer. Given: 
    - A user's NL query about cheese products, 
    - The table of available Pinecone metadata filter fields and types below,
    your task is to output only a valid Pinecone filter object (in JSON). Do not return any explanations, only output the JSON filter.

    ONLY use these fields.
    - cheese_type: string, e.g. "Parmesan", "Mozzarella", "Premio" This item refers types of cheese ingredients.
    - cheese_form: string, e.g. "Sliced", "loaf", "Shredded", "Cream", "Crumbled", "Cubed", "Grated", "Shaved", "Cottage", "Weel", "Speciality" what form does the cheese come in?
    - brand: string, e.g. "North Beach", "Galbani", "Schreiber" Refers the brand of the cheese.
    - price_each: number (float) Refers the price of the cheese per unit.
    - price_per_lb: number (float) Refers the price of the cheese per pound.
    - lb_per_each: number (float) Refers the amount of pounds per unit.
    - case: string ("No" or integer in string form, e.g. "6", "No") Refers if the cheese comes in a case or not.
    - sku: string or integer Refers the sku number of the cheese. "No" if it doesn't have a sku.
    - upc: string or integer Refers the universal product code of the cheese. "No" if it doesn't have a upc.

    Rules:
    1. For price, parse user intent and use appropriate operators: `$lt` (less than), `$lte`, `$gt`, `$gte`, `$eq`.
    2. Multiple filters should be combined with `$and`.
    3. If the user's query does not specify a field, leave it out and only filter what is specified.
    4. Never use fields not in the schema above.
    5. Output ONLY a valid Pinecone filter JSON object, nothing else.

    Examples:
    User: Show me cheddar cheeses under $10
    Output: {"cheese_type": "Cheddar", "price_value": {"$lt": 10}}

    User: I want blue cheese from brand Saint Agur, in wedges, at most £20 per pound
    Output: {"$and": [{"cheese_type": "Blue Cheese"}, {"brand": "Saint Agur"}, {"cheese_form": "Wedge"}, {"price_per_lb": {"$lte": 20}}]}"""

            message = []
            message.append({"role" : "user", "content" : system_message + " Here is customer conversation:" + query})
            response = self.client.chat.completions.create(
                messages=message,
                model=Config.OPENAI_MODEL,
                temperature=0.1  # Lower temperature for more consistent JSON output
            )
            response_str = response.choices[0].message.content.strip()
            print("Raw response:", response_str)

            try:
                # Clean the response string if needed
                response_str = response_str.replace('\n', '').strip()
                if not response_str.startswith('{'):
                    response_str = '{' + response_str
                if not response_str.endswith('}'):
                    response_str = response_str + '}'

                # Parse the response string as JSON
                filter_dict = json.loads(response_str)
                print("Parsed filter:", filter_dict)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing filter JSON: {str(e)}")
                logger.error(f"Raw response was: {response_str}")
                filter_dict = None

            # Query for relevant products
            products = self.query_products(query, filter_dict=filter_dict)

            if not products:
                print("No products found")
                return {
                    'response': "I couldn't find any relevant products to answer your question.",
                    'context': []
                }
            # Generate response using the products as context
            return self.generate_response(query, json.loads(type_of_question.choices[0].message.tool_calls[0].function.arguments)['is_cheese_question'], products)
        else:
            return self.generate_response(query, json.loads(type_of_question.choices[0].message.tool_calls[0].function.arguments)['is_cheese_question'], [])


vector_store = VectorStore()

# Simple query
# result = vector_store.get_relevant_products("What are some good Mozzarella cheeses?")

# Query with filters
# filters = {
#     'price_value': {'$lt': 60},  # Price less than $20
#     'location': 'North Beach'      # Only from dairy case
# }
# result = vector_store.get_relevant_products(
#     "What are some affordable Mozzarella cheeses?",
#     filter_dict=filters
# )

# Access results
# print(result['response'])  # The generated answer
# print(result['context'])   # The products used as context 