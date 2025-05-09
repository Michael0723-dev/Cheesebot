import json
import hashlib
from typing import List, Dict, Any
import logging
from datetime import datetime
import os
import requests
from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image
import sys
from pathlib import Path
import urllib.parse

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from utils.config import Config

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.required_fields = ['name', 'description']
        # Use API key from config
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in config.py")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)  # Initialize OpenAI client with API key

    def clean_image_url(self, image_url: str) -> str:
        """Clean Kimelo shop image URL to get the actual image URL"""
        try:
            if not image_url or image_url == 'N/A':
                return ""
            
            # If it's a Kimelo shop URL, extract the actual image URL
            if 'shop.kimelo.com/_next/image' in image_url:
                # Parse the URL to get the 'url' parameter
                parsed = urllib.parse.urlparse(image_url)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'url' in query_params:
                    return urllib.parse.unquote(query_params['url'][0])
            
            return image_url
        except Exception as e:
            logger.error(f"Error cleaning image URL: {str(e)}")
            return image_url

    def generate_smart_description(self, image_url: str, metadata: Dict[str, Any]) -> str:
        """Generate a smart description using OpenAI's GPT-4 Vision"""
        try:
            # Check if API key is set
            if not Config.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY is not set in config.py")
                return ""

            # Clean the image URL
            clean_url = self.clean_image_url(image_url)
            print(clean_url)
            if not clean_url:
                logger.warning("No valid image URL provided")
                return ""

            # Prepare metadata context
            metadata_context = f"""
            Product Details:
            - cheese type: {metadata.get('cheese_type', 'Unknown')}
            - cheese form: {metadata.get('cheese_form', 'Unknown')}
            - sku: {metadata.get('sku', 'Unknown')}
            - upc: {metadata.get('upc', 'Unknown')}
            - brand: {metadata.get('brand', 'Unknown')}
            - Price per one: ${metadata.get('price_each', 0):.2f}
            - Price per lb: ${metadata.get('price_per_lb', 0):.2f}
            - lb per one: ${metadata.get('lb_per_each', 0):.2f}
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cheese expert. Analyze the cheese image and provided metadata to create a detailed, professional description. Focus on the cheese's appearance, texture, and characteristics. Include information about its origin and typical uses."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please analyze this cheese image and create a detailed description. Here's the product information: {metadata_context}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": clean_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating smart description: {str(e)}")
            return ""

    def generate_id(self, item: Dict[str, Any]) -> str:
        """Generate a unique ID for a product based on its key attributes"""
        # Combine key attributes to create a unique identifier
        key_attributes = f"{item.get('image_url', '')}"
        return hashlib.md5(key_attributes.encode()).hexdigest()

    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        return " ".join(text.split())

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single product item"""
        try:
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                logger.warning(f"Item is not a dictionary: {type(item)}")
                return None
            
            # Create a new dictionary with default values
            processed_item = {
                'description': '',
                'image_url': '',
                'metadata': {
                    'cheese_type': '',
                    'source_url': '',
                    'brand': '',
                    'cheese_form': '',
                    'sku': 0,
                    'upc': 0,
                    'price_per_lb': 0.00,
                    'price_each': 0.00,
                    'lb_per_each': 0.00,
                    'case': 'No'
                }
            }
            
            # Update with actual values if they exist
            for key in processed_item:
                if key in item:
                    processed_item[key] = item[key]
            
            # Generate unique ID
            processed_item['id'] = self.generate_id(processed_item)
            print(processed_item['id'])
            # Clean text fields
            # for field in ['name']:
            #     processed_item[field] = self.clean_text(processed_item[field])
            
            # Generate smart description
            if processed_item['image_url'] and processed_item['image_url'] != 'N/A':
                processed_item['description'] = self.generate_smart_description(
                    processed_item['image_url'],
                    processed_item['metadata']
                )
            
            # Add processing metadata
            processed_item['processed_at'] = datetime.utcnow().isoformat()
            
            return processed_item
        except Exception as e:
            logger.error(f"Error processing item: {str(e)}")
            return None

    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of product items"""
        processed_items = []
        
        # Ensure data is a list
        if not isinstance(data, list):
            logger.error(f"Input data is not a list: {type(data)}")
            return processed_items
        
        for item in data:
            processed_item = self.process_item(item)
            if processed_item:
                processed_items.append(processed_item)
        
        logger.info(f"Processed {len(processed_items)} items successfully")
        return processed_items

    def save_processed_data(self, data: List[Dict[str, Any]], output_file: str):
        """Save processed data to JSON file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved processed data to {output_file}")
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")

def main():
    try:
        # Check for OpenAI API key before proceeding
        if not Config.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set in config.py")
            return

        # Example usage
        processor = DataProcessor()
        
        # Load scraped data
        try:
            with open('data/cheese_products.json', 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            # Extract the products array from the wrapper structure
            if isinstance(raw_data, dict) and 'products' in raw_data:
                products = raw_data['products']
                logger.info(f"Found {len(products)} products in raw data")
            else:
                logger.error("Invalid data structure: missing 'products' array")
                return
                
            # Map the fields to match the expected structure
            mapped_products = []
            for product in products:
                if product.get('cheese_type') != 'N/A':  # Skip N/A entries
                    # Extract numerical price per lb value
                    price_per_lb_str = product.get('price_per_lb', '')
                    price_per_lb_value = 0.00
                    if price_per_lb_str != 'N/A':
                        try:
                            # Remove currency symbol and /lb, then convert to float
                            cleaned = ''.join(c for c in price_per_lb_str if c.isdigit() or c == '.')
                            price_per_lb_value = round(float(cleaned) if cleaned else 0.00, 2)
                        except (ValueError, TypeError):
                            price_per_lb_value = 0.00

                    # Extract numerical price value
                    price_str = product.get('price', '')
                    price_value = 0.00
                    if price_str != 'N/A':
                        try:
                            # Remove currency symbol and convert to float
                            cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
                            price_value = round(float(cleaned) if cleaned else 0.00, 2)
                        except (ValueError, TypeError):
                            price_value = 0.00

                    # Extract numerical each count of each case
                    case_count = 1  # Default value
                    if 'count' in product and isinstance(product['count'], dict):
                        if 'case' in product['count'] and isinstance(product['count']['case'], dict):
                            if 'count' in product['count']['case']:
                                try:
                                    count_str = ''.join(c for c in product['count']['case']['count'] if c.isdigit() or c == '.')
                                    case_count = int(count_str)
                                except (ValueError, TypeError):
                                    case_count = 1

                    # Extract numerical each product weight of each
                    lb_per_each = 0.00
                    if price_per_lb_value > 0:  # Avoid division by zero
                        lb_per_each = round(price_value / price_per_lb_value, 2)

                    mapped_product = {
                        'image_url': product.get('image_url', ''),
                        'metadata': {
                            'cheese_type': product.get('cheese_type', ''),
                            'source_url': product.get('product_url', ''),
                            'brand': product.get('brand', ''),
                            'cheese_form': product.get('cheese_form', ''),
                            'sku': int(product.get('sku', 0)),
                            'upc': int(product.get('upc', 0)),
                            'price_per_lb': price_per_lb_value,
                            'price_each': price_value,
                            'lb_per_each': lb_per_each,
                            'case': case_count if case_count != 1 else 'No'
                        }
                    }
                    mapped_products.append(mapped_product)
            
            logger.info(f"Mapped {len(mapped_products)} valid products")
        except Exception as e:
            logger.error(f"Error loading raw data: {str(e)}")
            return
        
        # Process data
        processed_data = processor.process_data(mapped_products)
        
        # Save processed data
        processor.save_processed_data(processed_data, 'data/processed_cheese_products1.json')
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return

if __name__ == "__main__":
    main()