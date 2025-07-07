#!/usr/bin/env python3
"""
BankBot Application Startup Script
Run this script from the project root directory.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Import settings after adding to path
    from app.config import settings
    
    print("🚀 Starting BankBot API...")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Database: {settings.DB_NAME}")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 