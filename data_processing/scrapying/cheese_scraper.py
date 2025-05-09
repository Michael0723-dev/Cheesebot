import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def scrape_product_details(product_url):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        driver.get(product_url)
        
        # Wait for the SKU/UPC div to be present
        wait = WebDriverWait(driver, 10)
        sku_upc_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'css-ahthbn')))
        
        # Get cheese form
        form_elems = driver.find_elements(By.CLASS_NAME, 'chakra-breadcrumb__link')
        cheese_form = form_elems[1].text.strip() if len(form_elems) > 1 else 'N/A'
        
        # Get SKU and UPC
        b_tags = sku_upc_div.find_elements(By.TAG_NAME, 'b')
        sku = b_tags[0].text.strip() if len(b_tags) > 0 else 'N/A'
        upc = b_tags[1].text.strip() if len(b_tags) > 1 else 'N/A'
        
        # Get table data
        table_data = {}
        table = sku_upc_div.find_element(By.CLASS_NAME, 'chakra-table')
        if table:
            tbody = table.find_element(By.TAG_NAME, 'tbody')
            rows = tbody.find_elements(By.TAG_NAME, 'tr')
            
            if rows:
                # Get all cells from all rows
                cells = [row.find_elements(By.TAG_NAME, 'td') for row in rows]
                
                # Check if we have both case and each columns
                if len(cells[0]) == 2:
                    table_data = {
                        'case': {
                            'count': cells[0][0].text.strip() if cells[0][0].text.strip() else 'N/A',
                            'volume': cells[1][0].text.strip() if cells[1][0].text.strip() else 'N/A',
                            'weight': cells[2][0].text.strip() if cells[2][0].text.strip() else 'N/A'
                        },
                        'each': {
                            'count': cells[0][1].text.strip() if cells[0][1].text.strip() else 'N/A',
                            'volume': cells[1][1].text.strip() if cells[1][1].text.strip() else 'N/A',
                            'weight': cells[2][1].text.strip() if cells[2][1].text.strip() else 'N/A'
                        }
                    }
                else:
                    # Only each column
                    table_data = {
                        'each': {
                            'count': cells[0][0].text.strip() if cells[0][0].text.strip() else 'N/A',
                            'volume': cells[1][0].text.strip() if cells[1][0].text.strip() else 'N/A',
                            'weight': cells[2][0].text.strip() if cells[2][0].text.strip() else 'N/A'
                        }
                    }
        
        details = {
            'cheese_form': cheese_form,
            'sku': sku,
            'upc': upc,
            'product_info': table_data,
        
        }
        
        print(f"Scraped results: {details}")
        return details
        
    except Exception as e:
        print(f"Error scraping product details: {e}")
        return {
            'cheese_form': 'N/A',
            'sku': 'N/A',
            'upc': 'N/A',
            'product_info': {},
            'related_cheeses': [],
            'other_cheeses': []
        }
    finally:
        driver.quit()

def scrape_cheese_department():
    base_url = "https://shop.kimelo.com/department/cheese/3365"
    current_page = 1
    all_cheese_products = []
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        while True:
            url = f"{base_url}?page={current_page}"
            print(f"\nScraping page {current_page}...")
            
            try:
                driver.get(url)
                # Wait for product cards to be present
                wait = WebDriverWait(driver, 10)
                product_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'chakra-card.group.css-5pmr4x')))
                
                cnt = 0
                for card in product_cards:
                    try:
                        # Get product name
                        name_elem = card.find_element(By.CLASS_NAME, 'css-pbtft')
                        
                        # Get price
                        price_elem = card.find_element(By.CLASS_NAME, 'css-1vhzs63')
                        
                        # Get price per lb
                        price_per_lb_elem = card.find_element(By.CLASS_NAME, 'css-ff7g47')
                        
                        # Get image
                        image_elem = card.find_element(By.TAG_NAME, 'img')
                        
                        # Get brand
                        brand_elem = card.find_element(By.CLASS_NAME, 'css-w6ttxb')
                        
                        # Get product URL
                        product_url = card.get_attribute('href')
                        
                        product_data = {
                            'cheese_type': name_elem.text.strip() if name_elem else 'N/A',
                            'price': price_elem.text.strip() if price_elem else 'N/A',
                            'price_per_lb': price_per_lb_elem.text.strip() if price_per_lb_elem else 'N/A',
                            'image_url': image_elem.get_attribute('src') if image_elem else 'N/A',
                            'product_url': product_url if product_url else 'N/A',
                            'brand': brand_elem.text.strip() if brand_elem else 'N/A',
                            'page_number': current_page
                        }
                        
                        if product_data['cheese_type'] != 'N/A':
                            # Scrape additional product details
                            if product_url != 'N/A':
                                print(f"Scraping details for {product_data['cheese_type']}...")
                                details = scrape_product_details(product_url)
                                product_data.update(details)
                                time.sleep(1)  # Be nice to the server between product detail requests
                            print(product_data)
                            all_cheese_products.append(product_data)
                            cnt += 1
                        
                    except Exception as e:
                        print(f"Error processing card on page {current_page}: {e}")
                        continue
                
                print(f"Found {cnt} / {len(product_cards)} product cards on page {current_page}")
                
                # Check if there's a next page
                next_page_link = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label="Next page"]')
                if not next_page_link or next_page_link[0].get_attribute('disabled'):
                    print("No next page link found or reached last page. Ending pagination.")
                    break
                    
                current_page += 1
                time.sleep(2)  # Be nice to the server between page requests
                
            except Exception as e:
                print(f"Error processing page {current_page}: {e}")
                break
    
    finally:
        driver.quit()
    
    output_data = {
        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_products': len(all_cheese_products),
        'total_pages': current_page - 1,
        'products': all_cheese_products
    }
    
    with open('cheese_products.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully scraped {len(all_cheese_products)} products from {current_page - 1} pages and saved to cheese_products.json")
    return output_data

def download_product_images(products_data):
    if not products_data or 'products' not in products_data:
        return
    
    if not os.path.exists('images'):
        os.makedirs('images')
    
    for idx, product in enumerate(products_data['products']):
        if product['image_url'] != 'N/A':
            try:
                response = requests.get(product['image_url'])
                if response.status_code == 200:
                    # Get the cheese type and clean it for filename
                    cheese_type = product['cheese_type']
                    # Remove any special characters and replace spaces with underscores
                    clean_filename = ''.join(c if c.isalnum() or c.isspace() else '_' for c in cheese_type)
                    clean_filename = clean_filename.replace(' ', '_')
                    filename = f"images/{clean_filename}.jpg"
                    
                    with open(filename, 'wb+') as f:
                        f.write(response.content)
                    print(f"Downloaded image for {cheese_type} as {filename}")
                    time.sleep(1)  # Be nice to the server
            except Exception as e:
                print(f"Error downloading image for {product['cheese_type']}: {e}")

if __name__ == "__main__":
    products_data = scrape_cheese_department()
    if products_data:
        download_product_images(products_data) 