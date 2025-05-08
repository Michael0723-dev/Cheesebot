import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os

def scrape_cheese_department():
    url = "https://shop.kimelo.com/department/cheese/3365"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Debug: Print the HTML structure
        print("HTML Structure:")
        print(soup.prettify()[:1000])  # Print first 1000 characters to see structure
        
        # Find all product cards - try different selectors
        product_cards = soup.find_all('div', {'class': 'css-0'})
        print(f"\nFound {len(product_cards)} product cards")
        
        cheese_products = []
        
        for idx, card in enumerate(product_cards):
            print(f"\nProcessing card {idx + 1}:")
            print(card.prettify())  # Print the card's HTML structure
            
            try:
                # Try to find elements with more specific selectors
                name_elem = card.find('p', {'class': 'chakra-text css-pbtft'})
                price_elem = card.find('b', {'class': 'chakra-text css-1vhzs63'})
                price_per_lb_elem = card.find('span', {'class': 'chakra-badge css-ff7g47'})
                image_elem = card.find('img')
                link_elem = card.find('a')
                location = card.find('p', {'class': 'chakra-text css-w6ttxb'})
                product_data = {
                    'cheese_type': name_elem.text.strip() if name_elem else 'N/A',
                    'price': price_elem.text.strip() if price_elem else 'N/A',
                    'price_per_lb': price_per_lb_elem.text.strip() if price_per_lb_elem else 'N/A',
                    'image_url': 'https://shop.kimelo.com' + image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A',
                    'product_url': 'https://shop.kimelo.com' + link_elem['href'] if link_elem and 'href' in link_elem.attrs else 'N/A',

                    'location' : location.text.strip() if location else 'N/A'
                }
                
                # print(f"Extracted data: {product_data}")
                cheese_products.append(product_data)
                
            except Exception as e:
                print(f"Error processing card {idx + 1}: {e}")
                continue
        output_data = {
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_products': len(cheese_products),
            'products': cheese_products
        }
        
        with open('cheese_products.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
            
        print(f"\nSuccessfully scraped {len(cheese_products)} products and saved to cheese_products.json")
        return output_data
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error processing the data: {e}")
        return None

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
                    filename = f"images/cheese_{idx + 1}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded image for product {idx + 1}")
                    time.sleep(1)  # Be nice to the server
            except Exception as e:
                print(f"Error downloading image for product {idx + 1}: {e}")

if __name__ == "__main__":
    products_data = scrape_cheese_department()
    if products_data:
        download_product_images(products_data) 