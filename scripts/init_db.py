#!/usr/bin/env python3
"""
Database Initialization Script
This script initializes the PostgreSQL database with the required schema.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

async def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect to postgres database to create our target database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.DB_NAME
        )
        
        if not exists:
            # Create database
            await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"✓ Database '{settings.DB_NAME}' created successfully")
        else:
            print(f"✓ Database '{settings.DB_NAME}' already exists")
            
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False
    
    return True

async def execute_sql_script(script_path: Path):
    """Execute SQL script against the database"""
    try:
        # Read SQL script
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Connect to target database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        # Execute SQL script
        await conn.execute(sql_content)
        print(f"✓ SQL script '{script_path.name}' executed successfully")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error executing SQL script '{script_path.name}': {e}")
        return False
    
    return True

async def verify_database_setup():
    """Verify that the database setup is correct"""
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        # Check if required tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'bank_documents', 'audit_logs')
        """)
        
        table_names = [row['table_name'] for row in tables]
        required_tables = ['users', 'bank_documents', 'audit_logs']
        
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"✗ Missing tables: {missing_tables}")
            return False
        
        print("✓ All required tables exist")
        
        # Check if pgvector extension is enabled
        extension_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            )
        """)
        
        if extension_exists:
            print("✓ pgvector extension is enabled")
        else:
            print("✗ pgvector extension is not enabled")
            return False
        
        # Check if vector column exists in bank_documents table
        vector_column_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'bank_documents' 
                AND column_name = 'embedding'
            )
        """)
        
        if vector_column_exists:
            print("✓ Vector column exists in bank_documents table")
        else:
            print("✗ Vector column not found in bank_documents table")
            return False
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error verifying database setup: {e}")
        return False
    
    return True

async def main():
    """Main initialization function"""
    print("🚀 Starting database initialization...")
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"User: {settings.DB_USER}")
    print("-" * 50)
    
    # Step 1: Create database if it doesn't exist
    if not await create_database_if_not_exists():
        print("✗ Failed to create database")
        sys.exit(1)
    
    # Step 2: Execute SQL schema script
    sql_script_path = Path(__file__).parent.parent / "sql" / "001_initial_schema.sql"
    
    if not sql_script_path.exists():
        print(f"✗ SQL script not found: {sql_script_path}")
        sys.exit(1)
    
    if not await execute_sql_script(sql_script_path):
        print("✗ Failed to execute SQL schema script")
        sys.exit(1)
    
    # Step 3: Verify database setup
    if not await verify_database_setup():
        print("✗ Database setup verification failed")
        sys.exit(1)
    
    print("-" * 50)
    print("✅ Database initialization completed successfully!")
    print(f"You can now start the FastAPI application with: python app/main.py")

if __name__ == "__main__":
    asyncio.run(main()) 