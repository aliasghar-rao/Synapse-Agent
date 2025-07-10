"""
Account Manager module for Drive-Manager Pro.
Handles user accounts, authentication, and profile management.
"""

import os
import json
import logging
import datetime
import hashlib
import secrets
import re
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models import Base
from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(Base):
    """Model representing a user account"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    profile_image = Column(String)  # Path to profile image
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    # User preferences and settings
    theme = Column(String, default="light")
    default_view = Column(String, default="list")
    notifications_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships to other models can be added here
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert to dictionary (excludes sensitive information)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_image': self.profile_image,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'theme': self.theme,
            'default_view': self.default_view,
            'notifications_enabled': self.notifications_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Session(Base):
    """Model representing a user session"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Relationship to User
    user = relationship("User")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Session(user_id={self.user_id}, expires_at='{self.expires_at}')>"
    
    def is_valid(self):
        """Check if the session is still valid (not expired)"""
        return datetime.datetime.utcnow() < self.expires_at

class AccountManager:
    """Manager for user account functionality"""
    
    def __init__(self):
        """Initialize the account manager"""
        self.initialize_admin_account()
    
    def initialize_admin_account(self):
        """Create an admin account if none exists"""
        session = db_manager.get_session()
        if not session:
            logger.error("Failed to get database session")
            return
        
        try:
            # Check if we already have users
            user_count = session.query(User).count()
            if user_count > 0:
                logger.info(f"Database already contains {user_count} users")
                session.close()
                return
            
            # Create admin user
            admin_password = "admin123"  # In a real app, this would be a generated secure password
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(admin_password, salt)
            
            admin_user = User(
                username="admin",
                email="admin@drivemanager.com",
                password_hash=password_hash,
                salt=salt,
                first_name="Admin",
                last_name="User",
                is_active=True,
                last_login=datetime.datetime.utcnow()
            )
            
            session.add(admin_user)
            session.commit()
            logger.info("Created admin user account")
        
        except Exception as e:
            logger.error(f"Error creating admin account: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def _hash_password(self, password, salt):
        """Hash a password with the given salt"""
        # In a real application, you'd use a more robust method like Argon2
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest()
    
    def register_user(self, username, email, password, first_name=None, last_name=None):
        """Register a new user"""
        session = db_manager.get_session()
        if not session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Validate input
            if not self._validate_username(username):
                return {"success": False, "error": "Invalid username. Use 3-20 characters, letters, numbers, and underscores only."}
            
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email address."}
            
            if not self._validate_password(password):
                return {"success": False, "error": "Password must be at least 8 characters long."}
            
            # Check if username or email already exists
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return {"success": False, "error": "Username already taken."}
                else:
                    return {"success": False, "error": "Email already registered."}
            
            # Create the user
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            session.add(new_user)
            session.commit()
            
            return {
                "success": True, 
                "message": "User registered successfully", 
                "user_id": new_user.id
            }
        
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            session.close()
    
    def login(self, username_or_email, password, ip_address=None, user_agent=None):
        """Log in a user and create a session"""
        session = db_manager.get_session()
        if not session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Find the user
            user = session.query(User).filter(
                ((User.username == username_or_email) | (User.email == username_or_email)) &
                (User.is_active == True)
            ).first()
            
            if not user:
                return {"success": False, "error": "Invalid username/email or password."}
            
            # Verify password
            hashed_attempt = self._hash_password(password, user.salt)
            if hashed_attempt != user.password_hash:
                return {"success": False, "error": "Invalid username/email or password."}
            
            # Update last login time
            user.last_login = datetime.datetime.utcnow()
            
            # Create a new session
            session_token = secrets.token_hex(32)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Session valid for 7 days
            
            user_session = Session(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            session.add(user_session)
            session.commit()
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user.to_dict(),
                "session_token": session_token,
                "expires_at": expires_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error during login: {e}")
            session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            session.close()
    
    def validate_session(self, session_token):
        """Validate a user session"""
        if not session_token:
            return {"success": False, "error": "No session token provided."}
        
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Find the session
            user_session = db_session.query(Session).filter_by(session_token=session_token).first()
            
            if not user_session:
                return {"success": False, "error": "Invalid session."}
            
            # Check if session is expired
            if not user_session.is_valid():
                return {"success": False, "error": "Session expired."}
            
            # Check if user is still active
            if not user_session.user.is_active:
                return {"success": False, "error": "User account is inactive."}
            
            return {
                "success": True,
                "user": user_session.user.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def logout(self, session_token):
        """Log out a user by invalidating their session"""
        if not session_token:
            return {"success": False, "error": "No session token provided."}
        
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Find and delete the session
            user_session = db_session.query(Session).filter_by(session_token=session_token).first()
            
            if user_session:
                db_session.delete(user_session)
                db_session.commit()
            
            return {"success": True, "message": "Logged out successfully."}
        
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            db_session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def get_user_profile(self, user_id):
        """Get a user's profile"""
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {"success": False, "error": "User not found."}
            
            return {"success": True, "user": user.to_dict()}
        
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def update_user_profile(self, user_id, profile_data):
        """Update a user's profile"""
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {"success": False, "error": "User not found."}
            
            # Fields that can be updated
            allowed_fields = [
                'first_name', 'last_name', 'profile_image', 
                'theme', 'default_view', 'notifications_enabled'
            ]
            
            # Update allowed fields
            for field in allowed_fields:
                if field in profile_data:
                    setattr(user, field, profile_data[field])
            
            db_session.commit()
            
            return {
                "success": True, 
                "message": "Profile updated successfully",
                "user": user.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            db_session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password"""
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {"success": False, "error": "User not found."}
            
            # Verify current password
            hashed_attempt = self._hash_password(current_password, user.salt)
            if hashed_attempt != user.password_hash:
                return {"success": False, "error": "Current password is incorrect."}
            
            # Validate new password
            if not self._validate_password(new_password):
                return {"success": False, "error": "New password must be at least 8 characters long."}
            
            # Update password
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(new_password, salt)
            
            user.password_hash = password_hash
            user.salt = salt
            
            # Invalidate all existing sessions
            sessions = db_session.query(Session).filter_by(user_id=user_id).all()
            for session in sessions:
                db_session.delete(session)
            
            db_session.commit()
            
            return {"success": True, "message": "Password changed successfully."}
        
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            db_session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def _validate_username(self, username):
        """Validate a username"""
        if not username:
            return False
        
        # Username should be 3-20 characters, letters, numbers, and underscores only
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))
    
    def _validate_email(self, email):
        """Validate an email address"""
        if not email:
            return False
        
        # Simple email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password):
        """Validate a password"""
        # Minimum 8 characters
        return password and len(password) >= 8
    
    def get_all_users(self):
        """Get all users (admin function)"""
        db_session = db_manager.get_session()
        if not db_session:
            return []
        
        try:
            users = db_session.query(User).all()
            return [user.to_dict() for user in users]
        
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        
        finally:
            db_session.close()
    
    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {"success": False, "error": "User not found."}
            
            user.is_active = False
            
            # Invalidate all existing sessions
            sessions = db_session.query(Session).filter_by(user_id=user_id).all()
            for session in sessions:
                db_session.delete(session)
            
            db_session.commit()
            
            return {"success": True, "message": "User account deactivated."}
        
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            db_session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()
    
    def reactivate_user(self, user_id):
        """Reactivate a user account"""
        db_session = db_manager.get_session()
        if not db_session:
            return {"success": False, "error": "Database error"}
        
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {"success": False, "error": "User not found."}
            
            user.is_active = True
            db_session.commit()
            
            return {"success": True, "message": "User account reactivated."}
        
        except Exception as e:
            logger.error(f"Error reactivating user: {e}")
            db_session.rollback()
            return {"success": False, "error": "An unexpected error occurred."}
        
        finally:
            db_session.close()

# Singleton instance
account_manager = AccountManager()