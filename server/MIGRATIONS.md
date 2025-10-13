# Database Migration Guide

This guide explains how to manage database migrations for the RADEX project using Alembic.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Migration Management](#migration-management)
- [Common Workflows](#common-workflows)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

### What are Database Migrations?

Database migrations are version-controlled changes to your database schema. They allow you to:

- Track schema changes over time
- Apply changes consistently across environments
- Rollback changes if needed
- Collaborate with team members on schema changes

### Migration System Components

1. **Alembic**: The migration framework we use
2. **`alembic/`**: Directory containing migration scripts and configuration
3. **`alembic/versions/`**: Directory containing individual migration files
4. **`alembic_version` table**: Database table tracking applied migrations
5. **`migrate.py`**: Helper script for common migration operations

## Quick Start

### Check Migration Status

```bash
# Activate virtual environment
source myenv/bin/activate

# Check current migration status
python migrate.py status
```

### Apply Pending Migrations

```bash
# Apply all pending migrations
python migrate.py upgrade
```

### View Migration History

```bash
# Show all migrations
python migrate.py history

# Show current migration
python migrate.py current
```

## Migration Management

### Creating a New Migration

#### 1. Auto-Generate Migration (Recommended)

Alembic can automatically detect changes to your models and generate migrations:

```bash
# Create a new migration with auto-detection
python migrate.py create "Add email verification field"
```

This will:
1. Compare your SQLAlchemy models with the current database schema
2. Generate a migration file with detected changes
3. Save it in `alembic/versions/` with a timestamp

#### 2. Create Empty Migration (Manual)

For complex migrations or data migrations:

```bash
# Using alembic directly for empty migration
alembic revision -m "Custom data migration"
```

Then manually edit the generated file to add your migration logic.

### Reviewing Generated Migrations

**IMPORTANT**: Always review auto-generated migrations before applying them!

1. Find the latest migration file in `alembic/versions/`
2. Review the `upgrade()` and `downgrade()` functions
3. Verify the changes match your intentions
4. Test the migration in a development environment first

Example migration file structure:

```python
def upgrade() -> None:
    """Upgrade schema - applied when running 'upgrade'"""
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
    op.create_index('ix_users_email_verified', 'users', ['email_verified'])

def downgrade() -> None:
    """Downgrade schema - applied when running 'downgrade'"""
    op.drop_index('ix_users_email_verified', table_name='users')
    op.drop_column('users', 'email_verified')
```

### Applying Migrations

#### Upgrade to Latest

```bash
# Apply all pending migrations
python migrate.py upgrade
```

#### Upgrade Step by Step

```bash
# Apply next migration only
python migrate.py upgrade +1

# Apply next 2 migrations
python migrate.py upgrade +2
```

#### Upgrade to Specific Revision

```bash
# Upgrade to specific revision ID
python migrate.py upgrade abc123def456
```

### Reverting Migrations

#### Downgrade One Migration

```bash
# Rollback the last applied migration
python migrate.py downgrade
```

This will:
1. Ask for confirmation
2. Run the `downgrade()` function of the latest migration
3. Update the `alembic_version` table

#### Downgrade Multiple Migrations

```bash
# Rollback last 2 migrations
python migrate.py downgrade -2

# Rollback to specific revision
python migrate.py downgrade abc123def456

# Rollback all migrations
python migrate.py downgrade base
```

**⚠️ WARNING**: Downgrading may result in data loss. Always backup your database first!

## Common Workflows

### Adding a New Model

1. Create your model in `app/models/`:

```python
# app/models/organization.py
from sqlalchemy import Column, String
from app.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
```

2. Import the model in `alembic/env.py` (if not already imported):

```python
from app.models.organization import Organization  # noqa: F401
```

3. Create migration:

```bash
python migrate.py create "Add organization model"
```

4. Review the generated migration file

5. Apply the migration:

```bash
python migrate.py upgrade
```

### Modifying an Existing Model

1. Update your model:

```python
# app/models/user.py
class User(Base):
    # ... existing fields ...
    phone_number = Column(String(20), nullable=True)  # New field
```

2. Create migration:

```bash
python migrate.py create "Add phone number to users"
```

3. Review and apply:

```bash
# Review the file in alembic/versions/
python migrate.py upgrade
```

### Data Migration

For migrations that transform data:

1. Create an empty migration:

```bash
alembic revision -m "Migrate user data format"
```

2. Edit the migration file to include data operations:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Define table structure for operations
    users = table('users',
        column('id', sa.UUID),
        column('old_field', sa.String),
        column('new_field', sa.String)
    )

    # Execute raw SQL or use SQLAlchemy operations
    conn = op.get_bind()

    # Example: Copy and transform data
    results = conn.execute(sa.select(users.c.id, users.c.old_field))
    for row in results:
        new_value = transform_data(row.old_field)
        conn.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(new_field=new_value)
        )

def downgrade() -> None:
    # Implement reverse transformation
    pass
```

3. Test thoroughly before applying to production!

### Handling Multiple Branches

If you're working with feature branches:

```bash
# Merge migration heads
alembic merge -m "Merge migration branches" head1 head2

# Check for multiple heads
alembic heads

# Show branches
alembic branches
```

## Best Practices

### 1. Always Review Auto-Generated Migrations

Auto-generation is smart but not perfect. Common issues:

- **Unwanted changes**: May detect changes you didn't intend
- **Column renames**: Detects as drop + add (data loss!)
- **Type changes**: May not handle all database-specific types correctly

### 2. Use Descriptive Migration Messages

❌ Bad:
```bash
python migrate.py create "update"
python migrate.py create "fix"
```

✅ Good:
```bash
python migrate.py create "Add email verification to users table"
python migrate.py create "Create organizations and memberships tables"
```

### 3. Keep Migrations Small and Focused

Create separate migrations for:
- Schema changes (tables, columns)
- Index creation
- Data migrations
- Constraint changes

### 4. Test Migrations Thoroughly

Before applying to production:

```bash
# 1. Apply migration
python migrate.py upgrade

# 2. Test your application

# 3. Test rollback
python migrate.py downgrade

# 4. Reapply to ensure it works both ways
python migrate.py upgrade
```

### 5. Never Edit Applied Migrations

Once a migration is:
- Committed to version control
- Applied to any environment (dev, staging, prod)

**Never modify it!** Create a new migration instead.

### 6. Backup Before Downgrading

```bash
# Backup database before rollback
pg_dump -U raguser -d ragdb > backup_before_rollback.sql

# Then downgrade
python migrate.py downgrade
```

### 7. Handle Production Carefully

For production deployments:

```bash
# 1. Backup database
pg_dump -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check migration status
python migrate.py status

# 3. Review pending migrations
python migrate.py history

# 4. Apply migrations
python migrate.py upgrade

# 5. Verify application works
# Run smoke tests, check logs, etc.
```

## Troubleshooting

### Migration Failed Mid-Way

If a migration fails partially:

```bash
# 1. Check current state
python migrate.py current

# 2. Check database for partial changes
psql -U raguser -d ragdb -c "\d tablename"

# 3. Either:
#    a) Fix the issue and retry
python migrate.py upgrade

#    b) Or manually fix database and mark as complete
python migrate.py stamp head
```

### Migration History Out of Sync

If `alembic_version` doesn't match reality:

```bash
# Check what's recorded
python migrate.py current

# Check what's actually in database
psql -U raguser -d ragdb -c "\dt"

# Stamp with correct revision (DANGEROUS - know what you're doing!)
python migrate.py stamp <correct_revision_id>
```

### Detecting Changes Not Working

If Alembic isn't detecting your model changes:

1. Verify model is imported in `alembic/env.py`
2. Check `Base.metadata` includes your models
3. Ensure models inherit from the correct `Base`

```bash
# Test by checking metadata
python -c "from app.database import Base; print(Base.metadata.tables.keys())"
```

### Multiple Heads Error

If you see "Multiple heads detected":

```bash
# View all heads
alembic heads

# Merge them
alembic merge -m "Merge branches" head1_id head2_id

# Apply merge migration
python migrate.py upgrade
```

### Database Connection Issues

```bash
# Verify database connection
psql -U raguser -h localhost -d ragdb

# Check environment variables
python -c "from app.config import settings; print(settings.db_host, settings.db_name)"

# Test with direct alembic
alembic current
```

## Advanced Usage

### Using Raw SQL in Migrations

```python
from alembic import op

def upgrade():
    # Execute raw SQL
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_users_email_lower
        ON users (LOWER(email));
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_users_email_lower;")
```

### Batch Operations (SQLite)

For SQLite or to minimize locking:

```python
from alembic import op

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(50)))
        batch_op.create_index('idx_new_field', ['new_field'])
```

### Using Alembic Directly

While `migrate.py` covers most use cases, you can use Alembic directly:

```bash
# Show current revision
alembic current

# Show history with details
alembic history --verbose

# Upgrade with SQL output (don't execute)
alembic upgrade head --sql

# Show SQL for specific migration
alembic upgrade abc123:def456 --sql
```

### Migration Dependencies

For complex migrations with dependencies:

```python
# In migration file
revision = 'def456'
down_revision = 'abc123'
depends_on = ('xyz789',)  # This migration requires xyz789 to be applied
```

### Environment-Specific Migrations

```python
from alembic import op
from app.config import settings

def upgrade():
    if settings.environment == 'production':
        # Production-specific migration
        op.execute("CREATE INDEX CONCURRENTLY ...")
    else:
        # Development migration
        op.execute("CREATE INDEX ...")
```

## Migration Workflow Cheat Sheet

```bash
# Daily Development
python migrate.py status          # Check for pending migrations
python migrate.py upgrade         # Apply pending migrations
python migrate.py create "msg"    # Create new migration after model changes

# Before Committing
python migrate.py history         # Review migration history
cat alembic/versions/latest_*.py  # Review generated migration
python migrate.py downgrade       # Test rollback
python migrate.py upgrade         # Reapply to verify

# Production Deployment
pg_dump > backup.sql              # Backup database
python migrate.py status          # Check status
python migrate.py upgrade         # Apply migrations
# Run application tests

# Emergency Rollback
python migrate.py downgrade       # Rollback last migration
# Or restore from backup
psql ragdb < backup.sql
```

## CI/CD Integration

### Docker Deployment

Add to your Docker entrypoint or startup script:

```bash
#!/bin/bash
# entrypoint.sh

# Wait for database
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    echo "Waiting for database..."
    sleep 2
done

# Run migrations
python migrate.py upgrade

# Start application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
- name: Run Database Migrations
  run: |
    source myenv/bin/activate
    python migrate.py upgrade
  env:
    DB_HOST: ${{ secrets.DB_HOST }}
    DB_USER: ${{ secrets.DB_USER }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Getting Help

If you encounter issues:

1. Check migration status: `python migrate.py status`
2. Review migration history: `python migrate.py history`
3. Check database state: `psql -U raguser -d ragdb`
4. Review Alembic logs in terminal output
5. Check application logs for SQLAlchemy errors

For critical issues, restore from backup and investigate before retrying.
