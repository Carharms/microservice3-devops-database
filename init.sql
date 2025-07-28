-- Create products table
CREATE TABLE IF NOT EXISTS products (
                                    id SERIAL PRIMARY KEY,
                                    publication_name VARCHAR(255) NOT NULL,
                                    price_per_month DECIMAL(10, 2),
                                    price_per_year DECIMAL(8, 2)
                                    description TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    );

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
                                      id SERIAL PRIMARY KEY,
                                      product_id INTEGER NOT NULL,
                                      quantity INTEGER NOT NULL DEFAULT 1,
                                      total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
    );

-- Insert sample products
INSERT INTO products (name, price, description) VALUES
                                                    ('Harvard Business Review', 12.00, 120.00 , 'DESCRIBE'),
                                                    ('CNN', 3.99, 29.99, 'DESCRIBE'),
                                                    ('Wall Street Journal', NULL, $52.00, 'DESCRIBE'),
                                                    ('New York Times', NULL, $52.00, 'DESCRIBE'),
                                                    ('Washington Post', NULL, $52.00, 'DESCRIBE');

-- Improve this
-- When completed with final project - store this in the cloud