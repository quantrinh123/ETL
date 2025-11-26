"""
Load clean orders from CSV to PostgreSQL database.

Usage:
    python -m app.load_to_db
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from .config import get_settings
from .logging_conf import configure_logging

LOGGER = logging.getLogger("loader.db")


def create_table(connection) -> None:
    """Create orders table if not exists"""
    cursor = connection.cursor()
    create_sql = """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(50) UNIQUE NOT NULL,
        order_date DATE NOT NULL,
        customer_id VARCHAR(50),
        customer_name VARCHAR(100) NOT NULL,
        total_amount NUMERIC(10, 2) NOT NULL,
        status VARCHAR(50),
        source VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_sql)
    connection.commit()
    LOGGER.info("Table 'orders' created or already exists")
    cursor.close()


def load_csv_to_db(csv_path: Path, connection) -> int:
    """Load CSV file into PostgreSQL table. Return number of rows inserted."""
    if not csv_path.exists():
        LOGGER.warning("CSV file not found: %s", csv_path)
        return 0

    df = pd.read_csv(csv_path)
    if df.empty:
        LOGGER.info("CSV file is empty: %s", csv_path)
        return 0

    cursor = connection.cursor()
    
    # Prepare data for insertion
    records = []
    for _, row in df.iterrows():
        records.append((
            row.get("order_id", ""),
            row.get("order_date", ""),
            row.get("customer_id", ""),
            row.get("customer_name", ""),
            row.get("total_amount", 0),
            row.get("status", ""),
            row.get("source", ""),
        ))

    # Insert with conflict handling (upsert)
    insert_sql = """
    INSERT INTO orders 
    (order_id, order_date, customer_id, customer_name, total_amount, status, source)
    VALUES %s
    ON CONFLICT (order_id) DO UPDATE SET
        order_date = EXCLUDED.order_date,
        customer_id = EXCLUDED.customer_id,
        customer_name = EXCLUDED.customer_name,
        total_amount = EXCLUDED.total_amount,
        status = EXCLUDED.status,
        source = EXCLUDED.source
    """
    
    try:
        execute_values(cursor, insert_sql, records, page_size=100)
        connection.commit()
        LOGGER.info("Loaded %d records from %s", len(records), csv_path)
        return len(records)
    except Exception as e:
        connection.rollback()
        LOGGER.error("Error loading CSV: %s", e)
        return 0
    finally:
        cursor.close()


def main() -> None:
    """Main entry point"""
    settings = get_settings()
    configure_logging()

    # PostgreSQL connection
    try:
        connection = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
        )
        LOGGER.info("Connected to PostgreSQL")
    except psycopg2.Error as e:
        LOGGER.error("Failed to connect to PostgreSQL: %s", e)
        return

    try:
        # Create table
        create_table(connection)

        # Load clean orders
        csv_path = settings.output_dir / "orders_clean.csv"
        count = load_csv_to_db(csv_path, connection)
        LOGGER.info("Total records loaded: %d", count)

    finally:
        connection.close()
        LOGGER.info("Database connection closed")


if __name__ == "__main__":
    main()
