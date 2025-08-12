#!/usr/bin/env python3
"""
One-time script to create admin user in existing database
Run this from the server directory: python create_admin_user.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

def create_admin_user():
    db: Session = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists!")
            print(f"ID: {existing_admin.id}")
            print(f"Email: {existing_admin.email}")
            print(f"Username: {existing_admin.username}")
            print(f"Is Superuser: {existing_admin.is_superuser}")
            return

        # Create admin user
        hashed_password = get_password_hash("admin123456")
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Username: {admin_user.username}")
        print(f"Password: admin123456")
        print(f"Is Superuser: {admin_user.is_superuser}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()