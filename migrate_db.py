#!/usr/bin/env python3
"""Migration script to add missing columns to conversations table."""
import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = "/tmp/talos-data/app.db"

def migrate():
    """Add missing columns to conversations table."""
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"📦 Migrating database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(conversations)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"   Existing columns: {sorted(existing_columns)}")

    # Columns to add
    migrations = [
        ("parent_conversation_id", "VARCHAR(36)"),
        ("branch_point_message_id", "VARCHAR(36)"),
        ("branch_name", "VARCHAR(100)"),
        ("branch_color", "VARCHAR(20)"),
    ]

    for column_name, column_type in migrations:
        if column_name not in existing_columns:
            print(f"   ➕ Adding column: {column_name}")
            try:
                cursor.execute(
                    f"ALTER TABLE conversations ADD COLUMN {column_name} {column_type}"
                )
            except Exception as e:
                print(f"   ⚠️  Error adding {column_name}: {e}")
        else:
            print(f"   ✓ Column {column_name} already exists")

    # Verify the changes
    cursor.execute("PRAGMA table_info(conversations)")
    new_columns = {row[1] for row in cursor.fetchall()}
    print(f"\n   New columns: {sorted(new_columns)}")

    conn.commit()
    conn.close()

    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
