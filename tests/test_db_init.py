#!/usr/bin/env python3
"""
Unit tests for database initialization
Tests the structure and sample data created by init.sql
"""

import os
# Psycopg2 may be an issue
import psycopg2
import pytest
from time import sleep

class TestDatabaseInit:
    
    @classmethod
    def setup_class(cls):
        """Setup database connection for tests"""
        # Wait for database to be ready
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cls.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'subscriptions'),
                    user=os.getenv('POSTGRES_USER', 'dbuser'),
                    password=os.getenv('POSTGRES_PASSWORD', 'dbpassword')
                )
                cls.cursor = cls.conn.cursor()
                break
            except psycopg2.OperationalError:
                retry_count += 1
                sleep(2)
        
        if retry_count >= max_retries:
            raise Exception("Could not connect to database after 30 retries")
    
    @classmethod
    def teardown_class(cls):
        """Close database connection"""
        if hasattr(cls, 'cursor'):
            cls.cursor.close()
        if hasattr(cls, 'conn'):
            cls.conn.close()
    
    def test_products_table_exists(self):
        """Test that products table exists with correct structure"""
        self.cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position;
        """)
        
        columns = self.cursor.fetchall()
        assert len(columns) == 6, "Products table should have 6 columns"
        
        expected_columns = [
            ('id', 'integer', 'NO'),
            ('publication_name', 'character varying', 'NO'),
            ('price_per_month', 'numeric', 'YES'),
            ('price_per_year', 'numeric', 'YES'),
            ('description', 'text', 'YES'),
            ('created_at', 'timestamp without time zone', 'YES')
        ]
        
        for i, (col_name, data_type, nullable) in enumerate(expected_columns):
            assert columns[i][0] == col_name
            assert data_type in columns[i][1]
            assert columns[i][2] == nullable
    
    def test_orders_table_exists(self):
        """Test that orders table exists with correct structure"""
        self.cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'orders'
            ORDER BY ordinal_position;
        """)
        
        columns = self.cursor.fetchall()
        assert len(columns) == 6, "Orders table should have 6 columns"
        
        expected_columns = [
            ('id', 'integer', 'NO'),
            ('product_id', 'integer', 'NO'),
            ('quantity', 'integer', 'NO'),
            ('total_price', 'numeric', 'NO'),
            ('status', 'character varying', 'YES'),
            ('created_at', 'timestamp without time zone', 'YES')
        ]
        
        for i, (col_name, data_type, nullable) in enumerate(expected_columns):
            assert columns[i][0] == col_name
            assert data_type in columns[i][1]
            assert columns[i][2] == nullable
    
    def test_foreign_key_constraint(self):
        """Test that foreign key constraint exists between orders and products"""
        self.cursor.execute("""
            SELECT tc.constraint_name, tc.table_name, kcu.column_name, 
                   ccu.table_name AS foreign_table_name,
                   ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND tc.table_name = 'orders';
        """)
        
        fk_constraints = self.cursor.fetchall()
        assert len(fk_constraints) == 1, "Should have exactly one foreign key constraint"
        
        constraint = fk_constraints[0]
        assert constraint[1] == 'orders'
        assert constraint[2] == 'product_id'
        assert constraint[3] == 'products'  
        assert constraint[4] == 'id'  
    
    def test_sample_products_inserted(self):
        """Test that sample products were inserted"""
        self.cursor.execute("SELECT COUNT(*) FROM products;")
        count = self.cursor.fetchone()[0]
        assert count == 5, "Should have 5 sample products"
        
        
        self.cursor.execute("SELECT publication_name FROM products WHERE publication_name = 'Harvard Business Review';")
        result = self.cursor.fetchone()
        assert result is not None, "Harvard Business Review should exist"
    
    def test_sample_orders_inserted(self):
        """Test that sample orders were inserted"""
        self.cursor.execute("SELECT COUNT(*) FROM orders;")
        count = self.cursor.fetchone()[0]
        assert count == 3, "Should have 3 sample orders"
        
        # Test order data integrity
        self.cursor.execute("""
            SELECT o.product_id, p.publication_name 
            FROM orders o 
            JOIN products p ON o.product_id = p.id;
        """)
        results = self.cursor.fetchall()
        assert len(results) == 3, "All orders should have valid product references"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])