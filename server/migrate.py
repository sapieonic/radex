#!/usr/bin/env python3
"""
Database Migration Management Script

This script provides a command-line interface for managing database migrations
using Alembic. It wraps common Alembic commands for easier usage.

Usage:
    python migrate.py upgrade          # Upgrade to latest migration
    python migrate.py downgrade        # Downgrade one migration
    python migrate.py current          # Show current migration
    python migrate.py history          # Show migration history
    python migrate.py create "message" # Create new migration
    python migrate.py status           # Show migration status
"""

import sys
import os
from pathlib import Path
import subprocess
import argparse

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from app.config import settings


def get_alembic_config():
    """Get Alembic configuration"""
    config_path = Path(__file__).parent / "alembic.ini"
    config = Config(str(config_path))
    return config


def get_database_url():
    """Get database URL from settings"""
    return f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


def get_current_revision():
    """Get current database revision"""
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        return None


def get_pending_migrations():
    """Get list of pending migrations"""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)

    current = get_current_revision()
    head = script.get_current_head()

    if current == head:
        return []

    if current is None:
        # No migrations applied yet
        revisions = []
        for rev in script.walk_revisions():
            revisions.append(rev)
        return list(reversed(revisions))

    # Get migrations between current and head
    revisions = []
    for rev in script.iterate_revisions(head, current):
        revisions.append(rev)
    return list(reversed(revisions[:-1])) if revisions else []


def upgrade(revision="head"):
    """Upgrade database to a specific revision"""
    print(f"🔄 Upgrading database to revision: {revision}")
    config = get_alembic_config()

    try:
        command.upgrade(config, revision)
        print("✅ Database upgraded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error upgrading database: {e}")
        return False


def downgrade(revision="-1"):
    """Downgrade database by one or to specific revision"""
    current = get_current_revision()
    if not current:
        print("⚠️  No migrations to downgrade")
        return False

    print(f"🔄 Downgrading database from revision: {current}")
    confirm = input("⚠️  Are you sure you want to downgrade? (yes/no): ")

    if confirm.lower() != "yes":
        print("❌ Downgrade cancelled")
        return False

    config = get_alembic_config()

    try:
        command.downgrade(config, revision)
        print("✅ Database downgraded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error downgrading database: {e}")
        return False


def current():
    """Show current database revision"""
    config = get_alembic_config()

    print("📍 Current database revision:")
    command.current(config)

    current_rev = get_current_revision()
    if current_rev:
        print(f"\n   Revision ID: {current_rev}")
    else:
        print("\n   ⚠️  No migrations applied yet")


def history():
    """Show migration history"""
    config = get_alembic_config()

    print("📜 Migration history:")
    command.history(config)


def status():
    """Show migration status with pending migrations"""
    print("📊 Migration Status\n" + "=" * 50)

    current_rev = get_current_revision()
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()

    if current_rev:
        print(f"✅ Current Revision: {current_rev}")
    else:
        print("⚠️  Current Revision: None (no migrations applied)")

    print(f"🎯 Latest Revision:  {head}")

    pending = get_pending_migrations()

    if pending:
        print(f"\n⚠️  Pending Migrations: {len(pending)}")
        print("-" * 50)
        for i, rev in enumerate(pending, 1):
            print(f"{i}. {rev.revision[:8]} - {rev.doc}")
        print("\n💡 Run 'python migrate.py upgrade' to apply pending migrations")
    else:
        print("\n✅ Database is up to date!")


def create_migration(message):
    """Create a new migration"""
    if not message:
        print("❌ Error: Migration message is required")
        return False

    print(f"📝 Creating new migration: {message}")
    config = get_alembic_config()

    try:
        command.revision(config, message=message, autogenerate=True)
        print("✅ Migration created successfully!")
        print("\n💡 Review the generated migration file before applying it")
        return True
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        return False


def stamp(revision):
    """Stamp database with a specific revision without running migrations"""
    print(f"🏷️  Stamping database with revision: {revision}")
    confirm = input("⚠️  This will mark the database as being at this revision without running migrations. Continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("❌ Stamp cancelled")
        return False

    config = get_alembic_config()

    try:
        command.stamp(config, revision)
        print("✅ Database stamped successfully!")
        return True
    except Exception as e:
        print(f"❌ Error stamping database: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Database Migration Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py upgrade              Upgrade to latest migration
  python migrate.py upgrade +1           Upgrade one migration
  python migrate.py downgrade            Downgrade one migration
  python migrate.py downgrade -2         Downgrade two migrations
  python migrate.py current              Show current revision
  python migrate.py history              Show all migrations
  python migrate.py status               Show migration status
  python migrate.py create "Add users"   Create new migration
  python migrate.py stamp head           Mark DB as at latest revision
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="Target revision (default: head)")

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument("revision", nargs="?", default="-1", help="Target revision (default: -1)")

    # Current command
    subparsers.add_parser("current", help="Show current revision")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message")

    # Stamp command
    stamp_parser = subparsers.add_parser("stamp", help="Stamp database with revision")
    stamp_parser.add_argument("revision", help="Target revision")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == "upgrade":
        upgrade(args.revision)
    elif args.command == "downgrade":
        downgrade(args.revision)
    elif args.command == "current":
        current()
    elif args.command == "history":
        history()
    elif args.command == "status":
        status()
    elif args.command == "create":
        create_migration(args.message)
    elif args.command == "stamp":
        stamp(args.revision)


if __name__ == "__main__":
    main()
