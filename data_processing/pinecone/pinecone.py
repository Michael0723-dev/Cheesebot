import json
import logging
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from utils.config import Config

logger = logging.getLogger(__name__)

class PineconeIngestor:
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
        
        # Get or create index
        if Config.PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=Config.PINECONE_INDEX_NAME,
                dimension=Config.VECTOR_DIMENSION,
                metric=Config.VECTOR_METRIC,
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
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

    def ingest_data(self, processed_data: List[Dict[str, Any]]):
        """Ingest processed cheese data into Pinecone"""
        try:
            for item in processed_data:
                # Combine name and description for embedding
                text_to_embed = f"{item['description']}"
                
                # Generate embedding
                embedding = self.get_embedding(text_to_embed)
                if not embedding:
                    logger.warning(f"Failed to generate embedding for item {item['id']}")
                    continue
                
                # Prepare metadata
                metadata = {
                    **item['metadata'],
                    'image_url': item['image_url'],
                    'description': item['description'],
                    'processed_at': item['processed_at']
                }
                
                # Upsert to Pinecone
                self.index.upsert(
                    vectors=[(item['id'], embedding, metadata)]
                )
                print(item['id'])
                logger.info(f"Stored item {item['id']} in Pinecone")
            
            logger.info(f"Successfully ingested {len(processed_data)} items into Pinecone")
        except Exception as e:
            logger.error(f"Error ingesting data into Pinecone: {str(e)}")

def main():
    try:
        # Load processed data
        with open('data/processed_cheese_products.json', 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Initialize ingestor and ingest data
        ingestor = PineconeIngestor()
        ingestor.ingest_data(processed_data)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return

if __name__ == "__main__":
    main() 