"""
File system operations module for Drive-Manager Pro.
Handles file browsing, metadata collection, and file operations.
"""

import os
import time
import hashlib
import shutil
import threading
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class FileType:
    """Enumeration of file types"""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    CODE = "code"
    FOLDER = "folder"
    UNKNOWN = "unknown"


class FileMetadata:
    """Class to store and manage file metadata"""
    
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.is_dir = os.path.isdir(path)
        self.size = 0
        self.created = 0
        self.modified = 0
        self.accessed = 0
        self.file_type = FileType.FOLDER if self.is_dir else FileType.UNKNOWN
        self.extension = ""
        self.hash = ""
        self.tags = []
        self.linked_apps = []
        
        self.update_metadata()
    
    def update_metadata(self):
        """Update file metadata from the filesystem"""
        try:
            if not self.is_dir:
                self.size = os.path.getsize(self.path)
                self.extension = os.path.splitext(self.path)[1].lower()
                self.file_type = self._determine_file_type()
            
            # Get timestamps
            stat_info = os.stat(self.path)
            self.created = stat_info.st_ctime
            self.modified = stat_info.st_mtime
            self.accessed = stat_info.st_atime
            
        except Exception as e:
            print(f"Error updating metadata for {self.path}: {e}")
    
    def _determine_file_type(self):
        """Determine file type based on extension"""
        # Document types
        if self.extension in ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.md']:
            return FileType.DOCUMENT
        # Image types
        elif self.extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            return FileType.IMAGE
        # Audio types
        elif self.extension in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']:
            return FileType.AUDIO
        # Video types
        elif self.extension in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
            return FileType.VIDEO
        # Archive types
        elif self.extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return FileType.ARCHIVE
        # Executable types
        elif self.extension in ['.exe', '.bat', '.sh', '.app', '.msi', '.bin']:
            return FileType.EXECUTABLE
        # Code types
        elif self.extension in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php']:
            return FileType.CODE
        # Unknown
        return FileType.UNKNOWN
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of file contents (for duplicate detection)"""
        if self.is_dir:
            return ""
        
        try:
            hash_sha256 = hashlib.sha256()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            self.hash = hash_sha256.hexdigest()
            return self.hash
        except Exception as e:
            print(f"Error calculating hash for {self.path}: {e}")
            return ""
    
    def get_formatted_size(self):
        """Get human-readable file size"""
        if self.is_dir:
            return "Folder"
        
        # Convert bytes to appropriate unit
        bytes_value = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024 or unit == 'TB':
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
    
    def get_formatted_date(self, timestamp):
        """Convert timestamp to human-readable date"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def add_tag(self, tag):
        """Add a tag to the file"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag):
        """Remove a tag from the file"""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def add_linked_app(self, app):
        """Add a linked application to the file"""
        if app not in self.linked_apps:
            self.linked_apps.append(app)


class DuplicateDetector:
    """Class for detecting duplicate files using SHA-256 hashing"""
    
    def __init__(self, file_system_manager):
        self.file_system_manager = file_system_manager
        # Maps hash values to lists of file paths that have that hash
        self.hash_map = {}
        # Statistics about the duplicate search
        self.stats = {
            'files_processed': 0,
            'bytes_processed': 0,
            'duplicate_sets': 0,
            'duplicate_files': 0,
            'wasted_space': 0
        }
        # For progress tracking
        self.total_files = 0
        self.progress = 0
        
    def reset_stats(self):
        """Reset the duplicate detection statistics"""
        self.hash_map = {}
        self.stats = {
            'files_processed': 0,
            'bytes_processed': 0,
            'duplicate_sets': 0,
            'duplicate_files': 0,
            'wasted_space': 0
        }
        self.total_files = 0
        self.progress = 0
    
    def scan_directory(self, directory_path, recursive=True):
        """Scan a directory for duplicate files"""
        self.reset_stats()
        file_list = []
        
        # First, count the total files to process for progress tracking
        self._count_files(directory_path, recursive, file_list)
        self.total_files = len(file_list)
        
        # Process each file
        for file_path in file_list:
            self._process_file(file_path)
            self.progress += 1
        
        # Calculate statistics about duplicates
        self._calculate_stats()
        
        return self.get_duplicate_groups()
    
    def _count_files(self, directory_path, recursive, file_list):
        """Count files in directory for progress tracking"""
        try:
            for item in os.listdir(directory_path):
                path = os.path.join(directory_path, item)
                
                # Skip hidden files
                if item.startswith('.'):
                    continue
                
                if os.path.isdir(path) and recursive:
                    self._count_files(path, recursive, file_list)
                elif os.path.isfile(path):
                    file_list.append(path)
        except Exception as e:
            print(f"Error counting files in {directory_path}: {e}")
    
    def _process_file(self, file_path):
        """Process a single file for duplicate detection"""
        try:
            # Get or create metadata
            if file_path in self.file_system_manager.file_metadata_cache:
                metadata = self.file_system_manager.file_metadata_cache[file_path]
            else:
                metadata = FileMetadata(file_path)
                self.file_system_manager.file_metadata_cache[file_path] = metadata
            
            # Calculate hash if not already done
            if not metadata.hash:
                metadata.calculate_hash()
            
            # Skip if hash calculation failed
            if not metadata.hash:
                return
            
            # Add to hash map
            if metadata.hash in self.hash_map:
                self.hash_map[metadata.hash].append(file_path)
            else:
                self.hash_map[metadata.hash] = [file_path]
            
            self.stats['files_processed'] += 1
            self.stats['bytes_processed'] += metadata.size
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def _calculate_stats(self):
        """Calculate statistics about the duplicates found"""
        self.stats['duplicate_sets'] = 0
        self.stats['duplicate_files'] = 0
        self.stats['wasted_space'] = 0
        
        for hash_value, file_paths in self.hash_map.items():
            if len(file_paths) > 1:  # This is a set of duplicates
                self.stats['duplicate_sets'] += 1
                self.stats['duplicate_files'] += len(file_paths) - 1  # Count all but one as duplicates
                
                # Calculate wasted space (size of all copies after the first)
                if file_paths[0] in self.file_system_manager.file_metadata_cache:
                    file_size = self.file_system_manager.file_metadata_cache[file_paths[0]].size
                    self.stats['wasted_space'] += file_size * (len(file_paths) - 1)
    
    def get_duplicate_groups(self):
        """Get groups of duplicate files"""
        duplicate_groups = []
        
        for hash_value, file_paths in self.hash_map.items():
            if len(file_paths) > 1:  # This is a set of duplicates
                # Get full metadata for each file
                files_metadata = []
                for path in file_paths:
                    if path in self.file_system_manager.file_metadata_cache:
                        metadata = self.file_system_manager.file_metadata_cache[path]
                        files_metadata.append({
                            'path': path,
                            'name': metadata.name,
                            'size': metadata.size,
                            'modified': metadata.modified,
                            'formatted_size': metadata.get_formatted_size(),
                            'formatted_date': metadata.get_formatted_date(metadata.modified)
                        })
                
                # Sort by modification date (newest first)
                files_metadata.sort(key=lambda x: x['modified'], reverse=True)
                
                duplicate_groups.append({
                    'hash': hash_value,
                    'files': files_metadata,
                    'count': len(files_metadata),
                    'total_size': files_metadata[0]['size'] if files_metadata else 0,
                    'wasted_space': files_metadata[0]['size'] * (len(files_metadata) - 1) if files_metadata else 0
                })
        
        # Sort by wasted space (largest first)
        duplicate_groups.sort(key=lambda x: x['wasted_space'], reverse=True)
        
        return duplicate_groups
    
    def get_stats(self):
        """Get statistics about the duplicate search"""
        # Format the sizes for better readability
        formatted_stats = self.stats.copy()
        formatted_stats['formatted_bytes_processed'] = self._format_size(self.stats['bytes_processed'])
        formatted_stats['formatted_wasted_space'] = self._format_size(self.stats['wasted_space'])
        
        return formatted_stats
    
    def get_progress(self):
        """Get the current progress as a percentage"""
        if self.total_files == 0:
            return 100
        return int((self.progress / self.total_files) * 100)
    
    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024


class EventEmitter:
    """Simple event emitter to replace QObject signals"""
    
    def __init__(self):
        self.callbacks = {}
        
    def on(self, event_name, callback):
        """Register a callback for an event"""
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
        
    def emit(self, event_name, *args, **kwargs):
        """Emit an event with arguments"""
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback(*args, **kwargs)


class FileSystemManager(QObject):
    """Manager class for file system operations"""
    
    file_list_updated = pyqtSignal(list)
    file_operation_completed = pyqtSignal(bool, str)
    duplicate_scan_progress = pyqtSignal(int)  # Progress percentage
    duplicate_scan_completed = pyqtSignal(list, dict)  # Duplicate groups, stats
    
    def __init__(self):
        super().__init__()
        self.current_path = os.path.expanduser("~")
        self.file_metadata_cache = {}
        self.duplicate_detector = DuplicateDetector(self)
    
    def get_current_directory_contents(self):
        """Get contents of the current directory"""
        try:
            items = os.listdir(self.current_path)
            file_items = []
            
            for item in items:
                path = os.path.join(self.current_path, item)
                
                # Skip hidden files
                if item.startswith('.'):
                    continue
                
                # Get or create metadata
                if path in self.file_metadata_cache:
                    metadata = self.file_metadata_cache[path]
                    metadata.update_metadata()
                else:
                    metadata = FileMetadata(path)
                    self.file_metadata_cache[path] = metadata
                
                file_items.append(metadata)
            
            # Sort: folders first, then by name
            file_items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            
            self.file_list_updated.emit(file_items)
            return file_items
            
        except Exception as e:
            print(f"Error reading directory {self.current_path}: {e}")
            self.file_operation_completed.emit(False, f"Error: {str(e)}")
            return []
    
    def navigate_to(self, path):
        """Navigate to a directory"""
        if os.path.isdir(path):
            self.current_path = path
            return self.get_current_directory_contents()
        return []
    
    def navigate_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:  # Avoid infinite loop at root
            return self.navigate_to(parent)
        return self.get_current_directory_contents()
    
    def create_directory(self, name):
        """Create a new directory"""
        try:
            new_dir = os.path.join(self.current_path, name)
            os.makedirs(new_dir)
            self.file_operation_completed.emit(True, f"Created directory: {name}")
            self.get_current_directory_contents()
            return True
        except Exception as e:
            self.file_operation_completed.emit(False, f"Error creating directory: {str(e)}")
            return False
    
    def delete_item(self, path):
        """Delete a file or directory"""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
                
            if path in self.file_metadata_cache:
                del self.file_metadata_cache[path]
                
            self.file_operation_completed.emit(True, f"Deleted: {os.path.basename(path)}")
            self.get_current_directory_contents()
            return True
        except Exception as e:
            self.file_operation_completed.emit(False, f"Error deleting item: {str(e)}")
            return False
    
    def copy_item(self, source, destination):
        """Copy a file or directory"""
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
                
            self.file_operation_completed.emit(True, f"Copied: {os.path.basename(source)}")
            self.get_current_directory_contents()
            return True
        except Exception as e:
            self.file_operation_completed.emit(False, f"Error copying item: {str(e)}")
            return False
    
    def move_item(self, source, destination):
        """Move a file or directory"""
        try:
            shutil.move(source, destination)
            
            if source in self.file_metadata_cache:
                del self.file_metadata_cache[source]
                
            self.file_operation_completed.emit(True, f"Moved: {os.path.basename(source)}")
            self.get_current_directory_contents()
            return True
        except Exception as e:
            self.file_operation_completed.emit(False, f"Error moving item: {str(e)}")
            return False
    
    def rename_item(self, path, new_name):
        """Rename a file or directory"""
        try:
            dir_path = os.path.dirname(path)
            new_path = os.path.join(dir_path, new_name)
            
            if os.path.exists(new_path):
                self.file_operation_completed.emit(False, f"Cannot rename: {new_name} already exists")
                return False
                
            os.rename(path, new_path)
            
            if path in self.file_metadata_cache:
                metadata = self.file_metadata_cache[path]
                del self.file_metadata_cache[path]
                metadata.path = new_path
                metadata.name = new_name
                self.file_metadata_cache[new_path] = metadata
                
            self.file_operation_completed.emit(True, f"Renamed to: {new_name}")
            self.get_current_directory_contents()
            return True
        except Exception as e:
            self.file_operation_completed.emit(False, f"Error renaming item: {str(e)}")
            return False
            
    def find_duplicates(self, directory_path=None, recursive=True):
        """Find duplicate files in the specified directory using SHA-256 hashing"""
        import threading
        
        if not directory_path:
            directory_path = self.current_path
            
        # Run in a separate thread to avoid freezing the UI
        def run_duplicate_scan():
            try:
                # Emit progress updates periodically
                def update_progress():
                    while True:
                        progress = self.duplicate_detector.get_progress()
                        self.duplicate_scan_progress.emit(progress)
                        
                        if progress >= 100:
                            break
                            
                        time.sleep(0.5)  # Update every 0.5 seconds
                
                # Start progress tracker in a separate thread
                progress_thread = threading.Thread(target=update_progress)
                progress_thread.daemon = True
                progress_thread.start()
                
                # Run the actual scan
                duplicate_groups = self.duplicate_detector.scan_directory(directory_path, recursive)
                stats = self.duplicate_detector.get_stats()
                
                # Emit completion signal with results
                self.duplicate_scan_completed.emit(duplicate_groups, stats)
                
            except Exception as e:
                print(f"Error scanning for duplicates: {e}")
                self.file_operation_completed.emit(False, f"Error scanning for duplicates: {str(e)}")
        
        # Start the scan thread
        scan_thread = threading.Thread(target=run_duplicate_scan)
        scan_thread.daemon = True
        scan_thread.start()
        
        return True
        
    def resolve_duplicate(self, action, file_path, reference_path=None):
        """Resolve a duplicate file by either deleting, moving, or comparing"""
        if action == "delete":
            return self.delete_item(file_path)
        elif action == "move":
            if not reference_path:
                self.file_operation_completed.emit(False, "Missing destination for move operation")
                return False
            return self.move_item(file_path, reference_path)
        elif action == "compare":
            # In a desktop app, this would open a comparison view
            # For demo, just emit a signal that would be handled by the UI
            self.file_operation_completed.emit(True, f"Comparing {os.path.basename(file_path)} with {os.path.basename(reference_path)}")
            return True
        else:
            self.file_operation_completed.emit(False, f"Unknown duplicate resolution action: {action}")
            return False
            
    def calculate_file_hash(self, file_path):
        """Calculate the SHA-256 hash of a file"""
        if file_path in self.file_metadata_cache:
            metadata = self.file_metadata_cache[file_path]
        else:
            metadata = FileMetadata(file_path)
            self.file_metadata_cache[file_path] = metadata
            
        # Calculate hash if not already done
        if not metadata.hash:
            metadata.calculate_hash()
            
        return metadata.hash
        
    def optimize_storage(self, directory_path=None):
        """Optimize storage by finding and suggesting actions for duplicates"""
        # This is a higher-level function that combines duplicate finding with recommendations
        if not directory_path:
            directory_path = self.current_path
            
        # First find duplicates
        self.find_duplicates(directory_path, recursive=True)
        
        # The recommendations will be handled when the duplicate_scan_completed signal is emitted
        return True
