import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MySQLHandler:
    def __init__(self, host: str, user: str, password: str, database: str = "cheese_db"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()

    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            raise

    def disconnect(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

    def insert_product(self, product: Dict[str, Any]) -> bool:
        """Insert a new cheese product into the database"""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO cheese_products (
                    id, name, cheese_type, brand, cheese_form, description,
                    price_each, price_per_lb, lb_per_each, location,
                    case_size, sku, upc, image_url, source_url
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            values = (
                product.get('id'),
                product.get('name'),
                product.get('cheese_type'),
                product.get('brand'),
                product.get('cheese_form'),
                product.get('description'),
                product.get('price_each'),
                product.get('price_per_lb'),
                product.get('lb_per_each'),
                product.get('location'),
                product.get('case_size'),
                product.get('sku'),
                product.get('upc'),
                product.get('image_url'),
                product.get('source_url')
            )
            cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error inserting product: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_most_expensive_cheese(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most expensive cheeses"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT * FROM cheese_products 
                WHERE price_each IS NOT NULL 
                ORDER BY price_each DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting most expensive cheese: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_cheese_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Get cheeses from a specific location"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT * FROM cheese_products 
                WHERE location LIKE %s
            """
            cursor.execute(query, (f"%{location}%",))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting cheese by location: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_cheese_by_type(self, cheese_type: str) -> List[Dict[str, Any]]:
        """Get cheeses of a specific type"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT * FROM cheese_products 
                WHERE cheese_type LIKE %s
            """
            cursor.execute(query, (f"%{cheese_type}%",))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting cheese by type: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_cheese_by_price_range(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """Get cheeses within a price range"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT * FROM cheese_products 
                WHERE price_each BETWEEN %s AND %s
            """
            cursor.execute(query, (min_price, max_price))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting cheese by price range: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def search_cheese(self, query: str) -> List[Dict[str, Any]]:
        """Search cheeses using full-text search"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            search_query = """
                SELECT * FROM cheese_products 
                WHERE MATCH(name, description, cheese_type, brand) 
                AGAINST(%s IN NATURAL LANGUAGE MODE)
            """
            cursor.execute(search_query, (query,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error searching cheese: {e}")
            return []
        finally:
            if cursor:
                cursor.close() 