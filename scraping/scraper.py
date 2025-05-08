from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import List, Dict, Any
import os
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CheeseScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        # Add user agent to appear more like a real browser
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
    def setup_driver(self):
        """Initialize and return the Chrome WebDriver"""
        return webdriver.Chrome(options=self.chrome_options)
    
    def random_sleep(self, min_seconds=2, max_seconds=5):
        """Sleep for a random amount of time to appear more human-like"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def extract_product_data(self, card) -> Dict[str, Any]:
        """Extract detailed product information from a product card"""
        try:
            # Try different possible selectors for product title
            name = None
            for selector in [".product-title", ".product-name", "h3", "h4"]:
                try:
                    name_element = card.select_one(selector)
                    if name_element:
                        name = name_element.text.strip()
                        break
                except:
                    continue
            
            if not name:
                logger.warning("Could not find product name")
                return None

            # Try different possible selectors for price
            price = None
            for selector in [".product-price", ".price", ".product-price-value"]:
                try:
                    price_element = card.select_one(selector)
                    if price_element:
                        price = price_element.text.strip()
                        break
                except:
                    continue

            # Extract description if available
            description = ""
            for selector in [".product-description", ".description", "p"]:
                try:
                    desc_element = card.select_one(selector)
                    if desc_element:
                        description = desc_element.text.strip()
                        break
                except:
                    continue

            # Extract image URL
            image_url = ""
            try:
                img_element = card.select_one("img")
                if img_element:
                    image_url = img_element.get("src", "")
                    if not image_url:
                        image_url = img_element.get("data-src", "")
            except:
                pass

            # Extract any available metadata
            metadata = {}
            try:
                # Look for any elements that might contain metadata
                meta_elements = card.select("[class*='meta'], [class*='info'], [class*='detail']")
                for element in meta_elements:
                    key = element.get("class", [""])[0].replace("product-", "")
                    value = element.text.strip()
                    if value:  # Only add non-empty metadata
                        metadata[key] = value
            except:
                pass

            return {
                "name": name,
                "price": price,
                "description": description,
                "image_url": image_url,
                "metadata": metadata,
                "source_url": self.base_url,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error extracting product data: {str(e)}")
            return None

    def scrape_products(self) -> List[Dict[str, Any]]:
        """Scrape all cheese products from the website"""
        driver = self.setup_driver()
        products = []
        
        try:
            logger.info(f"Starting to scrape products from {self.base_url}")
            driver.get(self.base_url)
            
            # Initial wait for page load
            self.random_sleep(3, 5)
            
            # Try different possible selectors for product items
            product_selectors = [
                ".product-item",
                ".product-card",
                ".item",
                "[class*='product']",
                "[class*='item']"
            ]
            
            for selector in product_selectors:
                try:
                    # Wait for at least one product to be visible
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found products using selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # Scroll a few times to load more content
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_sleep(2, 3)
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Try to find products with different selectors
            product_cards = []
            for selector in product_selectors:
                cards = soup.select(selector)
                if cards:
                    product_cards = cards
                    logger.info(f"Found {len(cards)} products using selector: {selector}")
                    break
            
            if not product_cards:
                logger.error("No products found with any selector")
                return []
            
            # Extract data from each product card
            for card in product_cards:
                product_data = self.extract_product_data(card)
                if product_data:
                    products.append(product_data)
                    logger.info(f"Successfully extracted data for product: {product_data['name']}")
            
            return products
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return []
        finally:
            driver.quit()
    
    def save_to_json(self, products: List[Dict[str, Any]], filename: str = "cheese_products.json"):
        """Save scraped products to a JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved {len(products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

def main():
    base_url = "https://shop.kimelo.com/department/cheese/3365"
    scraper = CheeseScraper(base_url)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Scrape products
    products = scraper.scrape_products()
    
    # Save to JSON
    scraper.save_to_json(products, "data/cheese_products.json")

if __name__ == "__main__":
    main()