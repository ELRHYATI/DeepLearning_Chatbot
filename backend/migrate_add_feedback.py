"""
Migration script to add feedback table
"""
from app.database import engine, Base
from app.models import Feedback

def migrate():
    """Create feedback table"""
    print("Creating feedback table...")
    Feedback.__table__.create(engine, checkfirst=True)
    print("Feedback table created successfully!")

if __name__ == "__main__":
    migrate()

