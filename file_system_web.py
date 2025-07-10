"""
File system operations module for Drive-Manager Pro web version.
Handles file browsing, metadata collection, and file operations.
This version doesn't rely on PyQt6 for web compatibility.
"""

import os
import time
import hashlib
import shutil
import threading
from datetime import datetime

class FileType:
    """Enumeration of file types"""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    FOLDER = "folder"
    OTHER = "other"

class FileMetadata:
    """Class for storing file metadata"""
    
    def __init__(self, path, include_hash=False):
        self.path = path
        self.name = os.path.basename(path)
        self.is_dir = os.path.isdir(path)
        
        # Get basic file stats
        try:
            stats = os.stat(path)
            self.size = stats.st_size if not self.is_dir else 0
            self.modified_time = stats.st_mtime
            self.created_time = stats.st_ctime
            self.accessed_time = stats.st_atime
        except (FileNotFoundError, PermissionError):
            self.size = 0
            self.modified_time = 0
            self.created_time = 0
            self.accessed_time = 0
        
        # Determine file type
        self.file_type = self._determine_file_type()
        
        # Calculate hash if requested and if it's a file
        self.hash = None
        if include_hash and not self.is_dir:
            self.hash = self._calculate_hash()
    
    def _determine_file_type(self):
        """Determine file type based on extension"""
        if self.is_dir:
            return FileType.FOLDER
            
        extension = os.path.splitext(self.path)[1].lower()
        
        # Documents
        if extension in ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.md', '.rtf']:
            return FileType.DOCUMENT
            
        # Images
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return FileType.IMAGE
            
        # Audio
        elif extension in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma']:
            return FileType.AUDIO
            
        # Video
        elif extension in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mpeg', '.3gp']:
            return FileType.VIDEO
            
        # Archives
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.apk', '.ipa']:
            return FileType.ARCHIVE
            
        # Executables
        elif extension in ['.exe', '.bat', '.dll', '.msi', '.app', '.sh', '.py', '.js', '.deb', '.rpm']:
            return FileType.EXECUTABLE
            
        # Other
        else:
            return FileType.OTHER
    
    def _calculate_hash(self):
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (FileNotFoundError, PermissionError):
            return None
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'path': self.path,
            'name': self.name,
            'is_dir': self.is_dir,
            'size': self.size,
            'modified_time': self.modified_time,
            'created_time': self.created_time,
            'accessed_time': self.accessed_time,
            'file_type': self.file_type,
            'hash': self.hash,
            'formatted_size': self._format_size(),
            'formatted_modified_time': self._format_time(self.modified_time),
            'formatted_created_time': self._format_time(self.created_time),
            'formatted_accessed_time': self._format_time(self.accessed_time)
        }
    
    def _format_size(self):
        """Format size in bytes to human-readable format"""
        if self.is_dir:
            return "Directory"
            
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024 or unit == 'TB':
                return f"{size:.2f} {unit}"
            size /= 1024
    
    def _format_time(self, timestamp):
        """Format timestamp to human-readable format"""
        if timestamp == 0:
            return "Unknown"
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


class DuplicateDetector:
    """Class for detecting duplicate files based on content hash"""
    
    def __init__(self):
        self.duplicate_groups = []
        self.file_hashes = {}
        self.stats = {
            'files_processed': 0,
            'bytes_processed': 0,
            'duplicate_sets': 0,
            'duplicate_files': 0,
            'wasted_space': 0
        }
        
        # Event-based callbacks for progress reporting
        self.on_progress = None
        self.on_completed = None
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
    
    def find_duplicates(self, directory_path, recursive=True):
        """Find duplicate files in a directory"""
        if not os.path.isdir(directory_path):
            if self.on_completed:
                self.on_completed([], self.stats)
            return []
            
        # Reset state
        self.duplicate_groups = []
        self.file_hashes = {}
        self.stats = {
            'files_processed': 0,
            'bytes_processed': 0,
            'duplicate_sets': 0,
            'duplicate_files': 0,
            'wasted_space': 0
        }
        
        # Collect all files
        files = []
        if recursive:
            for root, dirs, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        if os.path.isfile(file_path):
                            files.append(file_path)
                    except (PermissionError, FileNotFoundError):
                        continue
        else:
            for item in os.listdir(directory_path):
                file_path = os.path.join(directory_path, item)
                try:
                    if os.path.isfile(file_path):
                        files.append(file_path)
                except (PermissionError, FileNotFoundError):
                    continue
        
        total_files = len(files)
        processed_files = 0
        
        # Process each file
        for file_path in files:
            try:
                file_size = os.path.getsize(file_path)
                
                # Calculate hash
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    with self.lock:
                        if file_hash in self.file_hashes:
                            self.file_hashes[file_hash].append({
                                'path': file_path,
                                'size': file_size,
                                'name': os.path.basename(file_path),
                                'formatted_size': self._format_size(file_size),
                                'modified': os.path.getmtime(file_path),
                                'formatted_date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                            })
                        else:
                            self.file_hashes[file_hash] = [{
                                'path': file_path,
                                'size': file_size,
                                'name': os.path.basename(file_path),
                                'formatted_size': self._format_size(file_size),
                                'modified': os.path.getmtime(file_path),
                                'formatted_date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                            }]
                            
                        # Update stats
                        self.stats['files_processed'] += 1
                        self.stats['bytes_processed'] += file_size
            except (PermissionError, FileNotFoundError):
                continue
                
            # Update progress
            processed_files += 1
            if self.on_progress:
                progress = int(processed_files / total_files * 100)
                self.on_progress(progress)
        
        # Format byte sizes
        self.stats['formatted_bytes_processed'] = self._format_size(self.stats['bytes_processed'])
        
        # Find duplicate groups
        for file_hash, files in self.file_hashes.items():
            if len(files) > 1:
                duplicate_group = {
                    'hash': file_hash,
                    'files': files,
                    'count': len(files),
                    'wasted_space': sum(f['size'] for f in files[1:])  # Count all but the first as waste
                }
                
                self.duplicate_groups.append(duplicate_group)
                
                # Update stats
                self.stats['duplicate_sets'] += 1
                self.stats['duplicate_files'] += len(files) - 1  # Count all but the first as duplicate
                self.stats['wasted_space'] += duplicate_group['wasted_space']
        
        # Format wasted space
        self.stats['formatted_wasted_space'] = self._format_size(self.stats['wasted_space'])
        
        # Sort by wasted space (largest first)
        self.duplicate_groups.sort(key=lambda g: g['wasted_space'], reverse=True)
        
        # Notify completion
        if self.on_completed:
            self.on_completed(self.duplicate_groups, self.stats)
        
        return self.duplicate_groups
    
    def get_duplicate_groups(self):
        """Get the list of duplicate groups"""
        return self.duplicate_groups
    
    def get_stats(self):
        """Get the duplication stats"""
        return self.stats
    
    def _calculate_file_hash(self, file_path, chunk_size=8192):
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (FileNotFoundError, PermissionError):
            return None
    
    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024


class FileSystemManager:
    """Manager class for file system operations"""
    
    def __init__(self):
        """Initialize the file system manager"""
        self.duplicate_detector = DuplicateDetector()
        
        # Create callback attributes
        self.duplicate_scan_progress = EventHook()
        self.duplicate_scan_completed = EventHook()
        
        # Connect the callbacks to the duplicate detector
        self.duplicate_detector.on_progress = self.duplicate_scan_progress.fire
        self.duplicate_detector.on_completed = self.duplicate_scan_completed.fire
    
    def list_directory(self, directory_path):
        """List contents of a directory"""
        try:
            contents = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                contents.append(FileMetadata(item_path))
            
            # Sort: directories first, then files alphabetically
            contents.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            
            return {
                'success': True,
                'path': directory_path,
                'contents': [item.to_dict() for item in contents]
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Directory not found: {directory_path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied: {directory_path}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error listing directory: {str(e)}"
            }
    
    def get_file_metadata(self, file_path, include_hash=False):
        """Get metadata for a file"""
        try:
            metadata = FileMetadata(file_path, include_hash)
            return {
                'success': True,
                'metadata': metadata.to_dict()
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"File not found: {file_path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied: {file_path}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting file metadata: {str(e)}"
            }
    
    def copy_file(self, source_path, destination_path, overwrite=False):
        """Copy a file or directory"""
        try:
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                return {
                    'success': False,
                    'error': f"Destination already exists: {destination_path}"
                }
                
            if os.path.isdir(source_path):
                # Copy directory
                if os.path.exists(destination_path):
                    # Remove existing directory if overwrite is True
                    if overwrite:
                        shutil.rmtree(destination_path)
                    else:
                        return {
                            'success': False,
                            'error': f"Destination directory already exists: {destination_path}"
                        }
                
                shutil.copytree(source_path, destination_path)
            else:
                # Copy file
                shutil.copy2(source_path, destination_path)
                
            return {
                'success': True,
                'message': f"Copied from {source_path} to {destination_path}"
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Source not found: {source_path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error copying: {str(e)}"
            }
    
    def move_file(self, source_path, destination_path, overwrite=False):
        """Move a file or directory"""
        try:
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                return {
                    'success': False,
                    'error': f"Destination already exists: {destination_path}"
                }
                
            if os.path.exists(destination_path) and overwrite:
                # Remove existing destination if overwrite is True
                if os.path.isdir(destination_path):
                    shutil.rmtree(destination_path)
                else:
                    os.remove(destination_path)
                    
            # Move the file or directory
            shutil.move(source_path, destination_path)
                
            return {
                'success': True,
                'message': f"Moved from {source_path} to {destination_path}"
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Source not found: {source_path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error moving: {str(e)}"
            }
    
    def delete_file(self, path, use_trash=True):
        """Delete a file or directory"""
        try:
            if use_trash:
                # Using trash is platform-specific and would require additional libraries
                # For this implementation, we'll just do a regular delete
                pass
                
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
                
            return {
                'success': True,
                'message': f"Deleted: {path}"
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Path not found: {path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied: {path}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error deleting: {str(e)}"
            }
    
    def create_directory(self, path):
        """Create a new directory"""
        try:
            os.makedirs(path, exist_ok=True)
            return {
                'success': True,
                'message': f"Created directory: {path}"
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied: {path}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error creating directory: {str(e)}"
            }
    
    def rename_file(self, old_path, new_path):
        """Rename a file or directory"""
        try:
            if os.path.exists(new_path):
                return {
                    'success': False,
                    'error': f"Destination already exists: {new_path}"
                }
                
            os.rename(old_path, new_path)
            return {
                'success': True,
                'message': f"Renamed from {old_path} to {new_path}"
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Source not found: {old_path}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error renaming: {str(e)}"
            }
    
    def find_duplicates(self, directory_path, recursive=True):
        """Find duplicate files in a directory"""
        return self.duplicate_detector.find_duplicates(directory_path, recursive)
    
    def search_files(self, directory_path, query, case_sensitive=False, recursive=True, search_content=False):
        """Search for files matching the given query"""
        # Advanced search functionality would be implemented here
        pass


class EventHook:
    """Simple event hook implementation for callbacks"""
    
    def __init__(self):
        self.__handlers = []
        
    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self
        
    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self
        
    def fire(self, *args, **kwargs):
        for handler in self.__handlers:
            handler(*args, **kwargs)


# Create an instance for use in the application
file_system_manager = FileSystemManager()