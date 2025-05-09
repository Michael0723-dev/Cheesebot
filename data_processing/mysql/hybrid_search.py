import sys
import os
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import re

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from rag.vector_store import VectorStore
from db_handler import MySQLHandler
from utils.config import Config

logger = logging.getLogger(__name__)

class HybridSearch:
    def __init__(self):
        self.vector_store = VectorStore()
        self.mysql_handler = MySQLHandler(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )

    def _detect_query_type(self, query: str) -> Dict[str, Any]:
        """
        Analyze the query to determine the type of search needed
        Returns a dictionary with query type and parameters
        """
        query = query.lower()
        
        # Price-related queries
        if re.search(r'most expensive|highest price|costliest', query):
            return {'type': 'price', 'action': 'most_expensive'}
        elif re.search(r'cheap|affordable|budget|under \$(\d+)', query):
            price = re.search(r'\$(\d+)', query)
            if price:
                return {'type': 'price', 'action': 'price_range', 'max_price': float(price.group(1))}
        
        # Location-based queries
        location_pattern = r'from\s+([a-zA-Z\s]+)|in\s+([a-zA-Z\s]+)'
        location_match = re.search(location_pattern, query)
        if location_match:
            location = location_match.group(1) or location_match.group(2)
            return {'type': 'location', 'location': location.strip()}
        
        # Type-based queries
        type_pattern = r'(cheddar|mozzarella|parmesan|brie|gouda|blue cheese|swiss|provolone)'
        type_match = re.search(type_pattern, query)
        if type_match:
            return {'type': 'cheese_type', 'cheese_type': type_match.group(1)}
        
        # Default to semantic search
        return {'type': 'semantic'}

    def search(self, query: str) -> Dict[str, Any]:
        """
        Perform hybrid search based on query analysis
        """
        query_type = self._detect_query_type(query)
        
        try:
            if query_type['type'] == 'price':
                if query_type['action'] == 'most_expensive':
                    results = self.mysql_handler.get_most_expensive_cheese(limit=5)
                else:
                    results = self.mysql_handler.get_cheese_by_price_range(
                        min_price=0,
                        max_price=query_type.get('max_price', float('inf'))
                    )
            
            elif query_type['type'] == 'location':
                results = self.mysql_handler.get_cheese_by_location(query_type['location'])
            
            elif query_type['type'] == 'cheese_type':
                results = self.mysql_handler.get_cheese_by_type(query_type['cheese_type'])
            
            else:  # semantic search
                results = self.vector_store.get_relevant_products(query)
                if isinstance(results, dict) and 'context' in results:
                    results = results['context']
            
            # If no results from primary search, try the other method
            if not results:
                if query_type['type'] != 'semantic':
                    semantic_results = self.vector_store.get_relevant_products(query)
                    if isinstance(semantic_results, dict) and 'context' in semantic_results:
                        results = semantic_results['context']
                else:
                    lexical_results = self.mysql_handler.search_cheese(query)
                    results = lexical_results
            
            return {
                'results': results,
                'query_type': query_type['type'],
                'total_results': len(results) if results else 0
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return {
                'results': [],
                'query_type': query_type['type'],
                'total_results': 0,
                'error': str(e)
            } 