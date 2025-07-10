"""
Database utilities for Drive-Manager Pro.
Handles database connections and operations.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from models import Base, File, Tag, Application, CloudSync, Recommendation, UserPreference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for Drive-Manager Pro"""
    
    def __init__(self):
        """Initialize the database manager"""
        self.engine = None
        self.session_factory = None
        self.Session = None
        self.is_connected = False
        
        # Try to connect to the database
        self.connect()
    
    def connect(self):
        """Establish a connection to the database"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                return False
            
            self.engine = create_engine(database_url)
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            self.is_connected = True
            logger.info("Successfully connected to the database")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            self.is_connected = False
            return False
    
    def get_session(self):
        """Get a database session"""
        if not self.is_connected:
            self.connect()
        
        if self.is_connected:
            return self.Session()
        else:
            logger.error("Cannot create session, not connected to database")
            return None
    
    def close_session(self, session):
        """Close a database session"""
        if session:
            session.close()
    
    def add_file(self, file_metadata):
        """Add a file to the database"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            # Check if the file already exists
            existing_file = session.query(File).filter_by(path=file_metadata.path).first()
            
            if existing_file:
                # Update existing file
                existing_file.name = file_metadata.name
                existing_file.size = file_metadata.size
                existing_file.extension = file_metadata.extension
                existing_file.is_directory = file_metadata.is_dir
                existing_file.file_type = file_metadata.file_type
                existing_file.created_time = file_metadata.created
                existing_file.modified_time = file_metadata.modified
                existing_file.accessed_time = file_metadata.accessed
                existing_file.hash_value = file_metadata.hash
                
                file = existing_file
            else:
                # Create new file
                file = File(
                    path=file_metadata.path,
                    name=file_metadata.name,
                    size=file_metadata.size,
                    extension=file_metadata.extension,
                    is_directory=file_metadata.is_dir,
                    file_type=file_metadata.file_type,
                    created_time=file_metadata.created,
                    modified_time=file_metadata.modified,
                    accessed_time=file_metadata.accessed,
                    hash_value=file_metadata.hash
                )
                session.add(file)
            
            # Commit the changes
            session.commit()
            return file.id
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding file to database: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def add_tag(self, tag_name, color=None):
        """Add a tag to the database"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            # Check if the tag already exists
            existing_tag = session.query(Tag).filter_by(name=tag_name).first()
            
            if existing_tag:
                # Update color if provided
                if color:
                    existing_tag.color = color
                
                tag = existing_tag
            else:
                # Create new tag
                tag = Tag(name=tag_name, color=color)
                session.add(tag)
            
            # Commit the changes
            session.commit()
            return tag.id
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding tag to database: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def add_tag_to_file(self, file_id, tag_id):
        """Associate a tag with a file"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            file = session.query(File).get(file_id)
            tag = session.query(Tag).get(tag_id)
            
            if file and tag and tag not in file.tags:
                file.tags.append(tag)
                session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding tag to file: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def remove_tag_from_file(self, file_id, tag_id):
        """Remove a tag association from a file"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            file = session.query(File).get(file_id)
            tag = session.query(Tag).get(tag_id)
            
            if file and tag and tag in file.tags:
                file.tags.remove(tag)
                session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Error removing tag from file: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def get_files_by_tag(self, tag_name):
        """Get all files with a specific tag"""
        if not self.is_connected:
            return []
        
        session = self.get_session()
        try:
            tag = session.query(Tag).filter_by(name=tag_name).first()
            
            if tag:
                return tag.files
            
            return []
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting files by tag: {e}")
            return []
        finally:
            self.close_session(session)
    
    def add_application(self, name, path=None, icon_path=None):
        """Add an application to the database"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            # Check if the application already exists
            existing_app = session.query(Application).filter_by(name=name).first()
            
            if existing_app:
                # Update fields if provided
                if path:
                    existing_app.path = path
                if icon_path:
                    existing_app.icon_path = icon_path
                
                app = existing_app
            else:
                # Create new application
                app = Application(name=name, path=path, icon_path=icon_path)
                session.add(app)
            
            # Commit the changes
            session.commit()
            return app.id
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding application to database: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def add_recommendation(self, file_id, rec_type, action, details, priority="medium"):
        """Add a recommendation to the database"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            # Create new recommendation
            recommendation = Recommendation(
                file_id=file_id,
                recommendation_type=rec_type,
                action=action,
                details=details,
                priority=priority,
                is_applied=False
            )
            
            session.add(recommendation)
            session.commit()
            return recommendation.id
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding recommendation to database: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def get_recommendations(self, applied=False):
        """Get all recommendations with the specified applied status"""
        if not self.is_connected:
            return []
        
        session = self.get_session()
        try:
            recommendations = session.query(Recommendation).filter_by(is_applied=applied).all()
            return recommendations
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
        finally:
            self.close_session(session)
    
    def set_user_preference(self, key, value):
        """Set a user preference"""
        if not self.is_connected:
            return False
        
        session = self.get_session()
        try:
            # Check if the preference already exists
            existing_pref = session.query(UserPreference).filter_by(key=key).first()
            
            if existing_pref:
                # Update the value
                existing_pref.value = value
            else:
                # Create new preference
                preference = UserPreference(key=key, value=value)
                session.add(preference)
            
            # Commit the changes
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Error setting user preference: {e}")
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def get_user_preference(self, key, default=None):
        """Get a user preference"""
        if not self.is_connected:
            return default
        
        session = self.get_session()
        try:
            preference = session.query(UserPreference).filter_by(key=key).first()
            
            if preference:
                return preference.value
            
            return default
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user preference: {e}")
            return default
        finally:
            self.close_session(session)

# Create a global instance of the database manager
db_manager = DatabaseManager()