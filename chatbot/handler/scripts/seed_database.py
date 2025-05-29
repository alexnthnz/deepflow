#!/usr/bin/env python3
"""
CLI script to seed the database with default graph configuration.
Usage: python scripts/seed_database.py
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
from database.seed_data import seed_database

def main():
    """Main function to run database seeding."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting manual database seeding...")
    
    try:
        result = seed_database()
        
        if result["status"] == "success":
            logger.info("✅ Database seeding completed successfully!")
            print(f"✅ Success: {result['message']}")
            sys.exit(0)
        else:
            logger.warning("⚠️ Database seeding completed with warnings")
            print(f"⚠️ Warning: {result['message']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 