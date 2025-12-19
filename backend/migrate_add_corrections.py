"""
Migration script to add message_corrections table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import MessageCorrection
from sqlalchemy import inspect

def migrate():
    """Add message_corrections table if it doesn't exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if 'message_corrections' not in existing_tables:
        print("Creating message_corrections table...")
        MessageCorrection.__table__.create(bind=engine, checkfirst=True)
        print("✅ message_corrections table created successfully!")
    else:
        print("✅ message_corrections table already exists")

if __name__ == "__main__":
    migrate()

