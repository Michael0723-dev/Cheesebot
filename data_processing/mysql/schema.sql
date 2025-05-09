CREATE DATABASE IF NOT EXISTS cheese_db;
USE cheese_db;

CREATE TABLE IF NOT EXISTS cheese_products (
    id VARCHAR(255) PRIMARY KEY,
    cheese_type VARCHAR(100),
    brand VARCHAR(100),
    cheese_form VARCHAR(50),
    description TEXT,
    price_each DECIMAL(10,2),
    price_per_lb DECIMAL(10,2),
    lb_per_each DECIMAL(10,2),
    location VARCHAR(100),
    case_size VARCHAR(50),
    sku VARCHAR(100),
    upc VARCHAR(100),
    image_url TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cheese_type (cheese_type),
    INDEX idx_brand (brand),
    INDEX idx_price (price_each),
    INDEX idx_location (location)
); 