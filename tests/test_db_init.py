#!/usr/bin/env python3
"""
Database tests for subscription database service
Compatible with Python 3.13 - no psycopg2 dependency required
"""

import os
import subprocess
import time
import pytest


class TestDatabaseSchema:
    """Unit tests for database schema validation - no database connection required"""
    
    def test_init_sql_file_exists(self):
        """Test that the init.sql file exists"""
        assert os.path.exists("scripts/init.sql"), "scripts/init.sql file should exist"
    
    def test_init_sql_contains_products_table(self):
        """Test that init.sql contains products table definition"""
        with open("scripts/init.sql", "r") as f:
            content = f.read().upper()
            assert "CREATE TABLE" in content, "Should contain CREATE TABLE statements"
            assert "PRODUCTS" in content, "Should contain products table definition"
    
    def test_init_sql_contains_orders_table(self):
        """Test that init.sql contains orders table definition"""
        with open("scripts/init.sql", "r") as f:
            content = f.read().upper()
            assert "ORDERS" in content, "Should contain orders table definition"
    
    def test_init_sql_contains_foreign_key(self):
        """Test that init.sql contains foreign key relationship"""
        with open("scripts/init.sql", "r") as f:
            content = f.read().upper()
            assert "FOREIGN KEY" in content, "Should contain foreign key constraint"
            assert "REFERENCES" in content, "Should reference parent table"
    
    def test_init_sql_contains_sample_data(self):
        """Test that init.sql contains sample data inserts"""
        with open("scripts/init.sql", "r") as f:
            content = f.read().upper()
            assert "INSERT INTO" in content, "Should contain INSERT statements"
            assert "HARVARD BUSINESS REVIEW" in content, "Should contain sample product data"
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and contains PostgreSQL"""
        assert os.path.exists("Dockerfile"), "Dockerfile should exist"
        
        with open("Dockerfile", "r") as f:
            content = f.read().upper()
            assert "FROM POSTGRES" in content, "Should use PostgreSQL base image"
            assert "COPY SCRIPTS/INIT.SQL" in content, "Should copy init.sql"
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and is properly configured"""
        assert os.path.exists("docker-compose.yml"), "docker-compose.yml should exist"
        
        with open("docker-compose.yml", "r") as f:
            content = f.read()
            assert "postgres" in content.lower(), "Should contain postgres service"
            assert "5432" in content, "Should expose PostgreSQL port"


class TestDatabaseIntegration:
    """Integration tests that require running database"""
    
    @classmethod
    def setup_class(cls):
        """Setup for integration tests - wait for database to be available"""
        cls.max_retries = 30
        cls.db_ready = False
        
        # Check if database is running and accessible
        for i in range(cls.max_retries):
            try:
                result = subprocess.run([
                    "docker-compose", "-f", "docker-compose.yml", 
                    "exec", "-T", "postgres", 
                    "pg_isready", "-U", "dbuser", "-d", "subscriptions"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    cls.db_ready = True
                    break
                    
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
            
            time.sleep(2)
    
    def test_database_connection(self):
        """Test that database is accessible"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "pg_isready", "-U", "dbuser", "-d", "subscriptions"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Database should be accessible"
    
    def test_products_table_created(self):
        """Test that products table was created successfully"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        # Query to check if products table exists
        sql_query = """
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'products';
        """
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "psql", "-U", "dbuser", "-d", "subscriptions", 
            "-c", sql_query
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Query should execute successfully"
        assert "1" in result.stdout, "Products table should exist"
    
    def test_orders_table_created(self):
        """Test that orders table was created successfully"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        sql_query = """
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'orders';
        """
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "psql", "-U", "dbuser", "-d", "subscriptions",
            "-c", sql_query
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Query should execute successfully"
        assert "1" in result.stdout, "Orders table should exist"
    
    def test_sample_products_inserted(self):
        """Test that sample products were inserted"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        sql_query = "SELECT COUNT(*) FROM products;"
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "psql", "-U", "dbuser", "-d", "subscriptions",
            "-c", sql_query
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Query should execute successfully"
        assert "5" in result.stdout, "Should have 5 sample products"
    
    def test_sample_orders_inserted(self):
        """Test that sample orders were inserted"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        sql_query = "SELECT COUNT(*) FROM orders;"
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "psql", "-U", "dbuser", "-d", "subscriptions",
            "-c", sql_query
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Query should execute successfully"
        assert "3" in result.stdout, "Should have 3 sample orders"
    
    def test_foreign_key_constraint_works(self):
        """Test that foreign key constraint is enforced"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        # Try to insert order with invalid product_id (should fail)
        sql_query = "INSERT INTO orders (product_id, quantity, total_price) VALUES (999, 1, 10.00);"
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "psql", "-U", "dbuser", "-d", "subscriptions",
            "-c", sql_query
        ], capture_output=True, text=True)
        
        assert result.returncode != 0, "Invalid foreign key should be rejected"
        assert "violates foreign key constraint" in result.stderr.lower(), "Should show foreign key error"
    
    def test_database_healthcheck(self):
        """Test that database healthcheck script works"""
        if not TestDatabaseIntegration.db_ready:
            pytest.skip("Database not available for integration tests")
        
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "exec", "-T", "postgres",
            "/usr/local/bin/healthcheck.sh"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Healthcheck should pass"
        assert "healthy" in result.stdout.lower(), "Should report database as healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])