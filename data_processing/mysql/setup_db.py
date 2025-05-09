import sys
import os
from pathlib import Path
import logging
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any
import json

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from utils.config import Config
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

def setup_database():
    """Create database and tables if they don't exist"""
    connection = None
    cursor = None
    try:
        # Validate MySQL configuration
        missing = Config.validate()
        if missing:
            raise ValueError(f"Missing required MySQL configuration: {', '.join(missing.keys())}")
            
        # Connect to MySQL server
        print("Connecting to MySQL server")
        print(Config.MYSQL_HOST)
        print(Config.MYSQL_PORT)
        print(Config.MYSQL_USER)
        print(Config.MYSQL_PASSWORD)
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        
        if connection.is_connected():
            cursor = connection.cursor()

            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
            cursor.execute(f"USE {Config.MYSQL_DATABASE}")
            
            # Read and execute schema.sql
            schema_path = Path(__file__).parent / "schema.sql"
            with open(schema_path, 'r') as file:
                schema_sql = file.read()
                # Split and execute each statement
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
            
            connection.commit()
            logger.info("Database and tables created successfully")
            print("Database and tables created successfully")
        else:
            print("Failed to connect to MySQL server")
    except Error as e:
        logger.error(f"Error setting up database: {e}")
        print(f"Error setting up database: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def migrate_data_from_pinecone():
    """Migrate data from Pinecone to MySQL"""
    connection = None
    cursor = None
    try:
        # Initialize vector store
        vector_store = VectorStore()
        
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Get all vectors from Pinecone
            index = vector_store.pc.Index(Config.PINECONE_INDEX_NAME)
            fetch_response = index.fetch(ids=[])  # You'll need to get all IDs first
            
            # Insert each product into MySQL
            for id, vector in fetch_response.vectors.items():
                metadata = vector.metadata
                if metadata:
                    query = """
                        INSERT INTO cheese_products (
                            id, cheese_type, brand, cheese_form, description,
                            price_each, price_per_lb, lb_per_each, location,
                            case_size, sku, upc, image_url, source_url
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    values = (
                        id,
                        metadata.get('cheese_type', ''),
                        metadata.get('brand', ''),
                        metadata.get('cheese_form', ''),
                        metadata.get('description', ''),
                        metadata.get('price_each', 0.0),
                        metadata.get('price_per_lb', 0.0),
                        metadata.get('lb_per_each', 0.0),
                        metadata.get('location', ''),
                        metadata.get('case_size', ''),
                        metadata.get('sku', ''),
                        metadata.get('upc', ''),
                        metadata.get('image_url', ''),
                        metadata.get('source_url', '')
                    )
                    cursor.execute(query, values)
            
            connection.commit()
            logger.info("Data migration completed successfully")
            
    except Error as e:
        logger.error(f"Error migrating data: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def main():
    """Main function to set up database and migrate data"""
    try:
        # Setup database structure
        print("Setting up database structure")
        setup_database()
        
        # Migrate data from Pinecone
        migrate_data_from_pinecone()
        
        logger.info("Database setup and data migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main() 