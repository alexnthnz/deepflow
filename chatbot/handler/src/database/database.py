import logging

import psycopg
from langchain_postgres import PostgresChatMessageHistory
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.config import config

# pull in your existing logger or create one
logger = logging.getLogger(__name__)

DATABASE_URL = config.DATABASE_URL
engine = create_engine("postgresql+psycopg://" + DATABASE_URL, echo=True, future=True)
sync_connection = psycopg.connect(conninfo="postgresql://" + DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: create a new DB session per request and close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get a database session for direct use."""
    return SessionLocal()


def check_db_connection():
    """Verify we can connect and run a simple query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "success", "detail": "Database connection OK"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def list_tables():
    """List all tables in the public schema."""
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    return {"tables": tables}


def migrate_db():
    """
    Create all tables defined on Base.metadata and seed with default data.
    Accepts an optional Session for signature consistency.
    """
    try:
        # import all models so they're registered on Base.metadata
        from database import models

        Base.metadata.create_all(bind=engine)
        PostgresChatMessageHistory.create_tables(sync_connection, "chat_history")
        logger.info("Database migrations applied successfully")

        # Seed the database with default data
        try:
            from database.seed_data import seed_database

            seed_result = seed_database()
            if seed_result["status"] == "success":
                logger.info("Database seeding completed successfully")
            else:
                logger.warning(f"Database seeding had issues: {seed_result['message']}")
        except Exception as e:
            logger.warning(f"Database seeding failed, but migration succeeded: {e}")

        return {"status": "success", "detail": "Migrations applied and database seeded"}
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}
