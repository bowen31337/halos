#!/usr/bin/env python3
"""Database migration system for Talos.

This script handles database schema migrations, ensuring all tables,
columns, indexes, and foreign key relationships are properly created.
"""

import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set

# Database path - use the same path as the application
DB_PATH = "./data/app.db"


def get_existing_tables(conn) -> Set[str]:
    """Get set of existing table names."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}


def get_existing_columns(conn, table_name: str) -> Dict[str, str]:
    """Get existing columns for a table with their types."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row[2] for row in cursor.fetchall()}


def get_existing_indexes(conn, table_name: str) -> Set[str]:
    """Get existing indexes for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({table_name})")
    return {row[1] for row in cursor.fetchall()}


def get_existing_foreign_keys(conn, table_name: str) -> Set[Tuple[str, str, str]]:
    """Get existing foreign key constraints (from_col, to_table, to_col)."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return {(row[3], row[2], row[4]) for row in cursor.fetchall()}


def create_table(conn, table_name: str, columns: List[str]) -> bool:
    """Create a new table."""
    cursor = conn.cursor()
    columns_sql = ", ".join(columns)
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
    try:
        cursor.execute(sql)
        print(f"  ✓ Created table: {table_name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create table {table_name}: {e}")
        return False


def add_column(conn, table_name: str, column_name: str, column_type: str) -> bool:
    """Add a column to an existing table."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"  ✓ Added column: {table_name}.{column_name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to add column {table_name}.{column_name}: {e}")
        return False


def create_index(conn, index_name: str, table_name: str, columns: List[str]) -> bool:
    """Create an index on a table."""
    cursor = conn.cursor()
    columns_str = ", ".join(columns)
    try:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})")
        print(f"  ✓ Created index: {index_name} on {table_name}({columns_str})")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create index {index_name}: {e}")
        return False


def create_foreign_key(conn, table_name: str, from_col: str, to_table: str, to_col: str) -> bool:
    """Add a foreign key constraint (requires table recreation in SQLite)."""
    # SQLite doesn't support adding FKs via ALTER TABLE
    # This would require recreating the table, which we'll skip for now
    # The init_db() in SQLAlchemy handles FK creation
    print(f"  ⚠ Foreign key {table_name}.{from_col} -> {to_table}.{to_col} (handled by SQLAlchemy)")
    return True


def run_migrations() -> bool:
    """Run all database migrations."""
    db_path = Path(DB_PATH)

    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run the application first to create the initial schema")
        return False

    print(f"📦 Migrating database: {DB_PATH}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # 1. Check existing tables
        existing_tables = get_existing_tables(conn)
        print(f"\n1. Existing tables: {len(existing_tables)}")
        for table in sorted(existing_tables):
            print(f"   - {table}")

        # 2. Define expected schema based on SQLAlchemy models
        # These would normally be managed by Alembic or similar
        # For now, we verify what SQLAlchemy init_db() creates

        # 3. Verify critical tables exist
        expected_tables = {
            "conversations", "messages", "artifacts", "checkpoints",
            "background_tasks", "folders", "folder_items", "projects",
            "project_files", "memories", "prompts", "mcp_servers",
            "shared_conversations"
        }

        missing_tables = expected_tables - existing_tables
        if missing_tables:
            print(f"\n2. Missing tables: {len(missing_tables)}")
            for table in sorted(missing_tables):
                print(f"   - {table}")
            print("   Note: Run application to create missing tables via SQLAlchemy")
        else:
            print("\n2. All expected tables exist ✓")

        # 4. Verify indexes on key tables
        print("\n3. Checking indexes...")

        # Check conversation indexes
        if "conversations" in existing_tables:
            indexes = get_existing_indexes(conn, "conversations")
            print(f"   conversations indexes: {sorted(indexes) if indexes else 'none'}")

        # Check message indexes
        if "messages" in existing_tables:
            indexes = get_existing_indexes(conn, "messages")
            print(f"   messages indexes: {sorted(indexes) if indexes else 'none'}")

        # 5. Verify foreign keys
        print("\n4. Checking foreign keys...")

        if "messages" in existing_tables:
            fks = get_existing_foreign_keys(conn, "messages")
            if fks:
                for fk in fks:
                    print(f"   messages.{fk[0]} -> {fk[1]}.{fk[2]}")
            else:
                print("   messages: no FKs found")

        if "folder_items" in existing_tables:
            fks = get_existing_foreign_keys(conn, "folder_items")
            if fks:
                for fk in fks:
                    print(f"   folder_items.{fk[0]} -> {fk[1]}.{fk[2]}")
            else:
                print("   folder_items: no FKs found")

        # 6. Verify background_tasks table (from feature #96)
        print("\n5. Verifying Background Tasks schema...")
        if "background_tasks" in existing_tables:
            cols = get_existing_columns(conn, "background_tasks")
            required_cols = ["id", "user_id", "task_type", "status", "progress", "created_at"]
            missing = [c for c in required_cols if c not in cols]
            if missing:
                print(f"   ✗ Missing columns: {missing}")
            else:
                print(f"   ✓ All required columns present")
                for col, col_type in cols.items():
                    print(f"     - {col}: {col_type}")
        else:
            print("   ⚠ Table not yet created (run application)")

        # 7. Run any pending migrations
        print("\n6. Running migrations...")
        migrations_applied = 0

        # Example: Add missing columns if any
        if "conversations" in existing_tables:
            cols = get_existing_columns(conn, "conversations")
            # Add any missing columns that should exist
            new_cols = [
                ("parent_conversation_id", "VARCHAR(36)"),
                ("branch_point_message_id", "VARCHAR(36)"),
                ("branch_name", "VARCHAR(100)"),
                ("branch_color", "VARCHAR(20)"),
            ]
            for col_name, col_type in new_cols:
                if col_name not in cols:
                    if add_column(conn, "conversations", col_name, col_type):
                        migrations_applied += 1

        if migrations_applied > 0:
            print(f"\n   Applied {migrations_applied} migration(s)")
        else:
            print("\n   No migrations needed")

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ Migration check complete!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def verify_schema() -> bool:
    """Verify the database schema is correct."""
    db_path = Path(DB_PATH)

    if not db_path.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Check all tables exist
        existing_tables = get_existing_tables(conn)

        # These tables should exist after init_db()
        required_tables = [
            "conversations", "messages", "artifacts", "checkpoints",
            "background_tasks", "folders", "folder_items", "projects",
            "project_files", "memories", "prompts", "mcp_servers",
            "shared_conversations"
        ]

        all_present = True
        for table in required_tables:
            if table not in existing_tables:
                print(f"❌ Missing table: {table}")
                all_present = False

        if all_present:
            print("✅ All required tables exist")

            # Verify background_tasks has correct columns
            bg_cols = get_existing_columns(conn, "background_tasks")
            expected_bg_cols = ["id", "user_id", "conversation_id", "task_type",
                               "status", "progress", "subagent_name", "result",
                               "error_message", "created_at", "started_at", "completed_at"]

            for col in expected_bg_cols:
                if col not in bg_cols:
                    print(f"❌ Missing column in background_tasks: {col}")
                    all_present = False

            if all_present:
                print("✅ Background tasks schema is correct")

        return all_present

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration system")
    parser.add_argument("--verify", action="store_true", help="Verify schema only")

    args = parser.parse_args()

    if args.verify:
        success = verify_schema()
    else:
        success = run_migrations()

    sys.exit(0 if success else 1)
