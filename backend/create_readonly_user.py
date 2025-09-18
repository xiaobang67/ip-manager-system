#!/usr/bin/env python3
"""
Create a readonly user for testing the new readonly role functionality.
"""

import sys
import os
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserTheme

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_readonly_user():
    """Create a readonly user for testing"""
    db = SessionLocal()
    
    try:
        # Check if readonly user already exists
        existing_user = db.query(User).filter(User.username == "readonly").first()
        if existing_user:
            print("Readonly user already exists. Updating role to readonly...")
            existing_user.role = UserRole.READONLY
            db.commit()
            print(f"Updated user '{existing_user.username}' role to readonly")
            return
        
        # Create new readonly user
        hashed_password = pwd_context.hash("readonly123")
        
        readonly_user = User(
            username="readonly",
            password_hash=hashed_password,
            email="readonly@ipam.local",
            role=UserRole.READONLY,
            theme=UserTheme.LIGHT,
            is_active=True
        )
        
        db.add(readonly_user)
        db.commit()
        db.refresh(readonly_user)
        
        print(f"Successfully created readonly user:")
        print(f"  Username: {readonly_user.username}")
        print(f"  Email: {readonly_user.email}")
        print(f"  Role: {readonly_user.role}")
        print(f"  Password: readonly123")
        print(f"  User ID: {readonly_user.id}")
        
    except Exception as e:
        print(f"Error creating readonly user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating readonly user...")
    create_readonly_user()
    print("Done!")