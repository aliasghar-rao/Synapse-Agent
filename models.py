"""
Database models for Drive-Manager Pro.
Contains SQLAlchemy ORM models for files, tags, user preferences, and other data.
"""

import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class File(Base):
    """Model representing a file in the file system"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    name = Column(String, nullable=False)
    extension = Column(String)
    size = Column(Integer)
    is_directory = Column(Boolean, default=False)
    file_type = Column(String)  # image, video, document, etc.
    created_time = Column(DateTime)
    modified_time = Column(DateTime)
    accessed_time = Column(DateTime)
    hash_value = Column(String)  # For detecting duplicates
    
    tags = relationship("Tag", secondary="file_tags", back_populates="files")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<File(name='{self.name}', path='{self.path}')>"
    
class Tag(Base):
    """Model representing a tag for files"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    color = Column(String)
    
    files = relationship("File", secondary="file_tags", back_populates="tags")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Tag(name='{self.name}')>"

class FileTag(Base):
    """Model representing the many-to-many relationship between files and tags"""
    __tablename__ = 'file_tags'
    
    file_id = Column(Integer, ForeignKey('files.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserPreference(Base):
    """Model representing user preferences"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    preference_key = Column(String, nullable=False)
    preference_value = Column(String)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference(key='{self.preference_key}', value='{self.preference_value}')>"

class Application(Base):
    """Model representing an application in the application launcher"""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)
    icon_path = Column(String)
    category = Column(String)
    description = Column(Text)
    is_favorite = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Application(name='{self.name}', command='{self.command}')>"

class CloudSync(Base):
    """Model representing cloud synchronization state"""
    __tablename__ = 'cloud_syncs'
    
    id = Column(Integer, primary_key=True)
    local_path = Column(String, nullable=False)
    remote_path = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # Google Drive, Dropbox, etc.
    status = Column(String, nullable=False)  # synced, pending, error
    last_synced = Column(DateTime)
    sync_direction = Column(String)  # up, down, both
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<CloudSync(local='{self.local_path}', remote='{self.remote_path}', provider='{self.provider}')>"

class Recommendation(Base):
    """Model representing a file/tag recommendation"""
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    recommendation_type = Column(String, nullable=False)  # duplicate, obsolete, organization
    description = Column(Text)
    severity = Column(Integer)  # 1-5 (5 being highest priority)
    is_dismissed = Column(Boolean, default=False)
    
    file = relationship("File")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Recommendation(type='{self.recommendation_type}', severity={self.severity})>"

class OllamaModelCache(Base):
    """Model representing cached results from laptop-hosted Ollama models for learning"""
    __tablename__ = 'ollama_model_cache'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    parameters = Column(Text, nullable=False)  # Stored as JSON
    result_hash = Column(String, nullable=False)  # Hash of the result for quick lookup
    result_data = Column(LargeBinary)  # The actual result data (image or video)
    thumbnail = Column(LargeBinary)  # Thumbnail for quick preview
    media_type = Column(String, nullable=False)  # image, video
    width = Column(Integer)
    height = Column(Integer)
    seed = Column(Integer)
    duration = Column(Float)  # For videos
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<OllamaModelCache(model='{self.model_name}', type='{self.media_type}')>"

# Ensure all models are created
def create_all_tables(engine):
    Base.metadata.create_all(engine)