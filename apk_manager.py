"""
APK Manager module for Drive-Manager Pro.
Manages APK creation, import, analysis, and extraction.
"""

import os
import json
import shutil
import threading
from datetime import datetime
from apk_creator import apk_creator
from apk_analyzer import APKAnalyzer
from ui_extractor import ui_extractor
from database import db_manager
from models import Application

class APKManager:
    """Comprehensive APK management system"""
    
    def __init__(self):
        """Initialize the APK manager"""
        self.apk_creator = apk_creator
        self.apk_analyzer = APKAnalyzer()
        self.ui_extractor = ui_extractor
        
        # Directories
        self.apk_storage_dir = os.path.join(os.getcwd(), "apk_storage")
        self.extracted_dir = os.path.join(os.getcwd(), "extracted_apks")
        self.generated_dir = os.path.join(os.getcwd(), "generated_apks")
        
        # Create directories
        for directory in [self.apk_storage_dir, self.extracted_dir, self.generated_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize with sample APKs
        self._initialize_sample_apks()
    
    def _initialize_sample_apks(self):
        """Create sample APKs if none exist"""
        try:
            # Check if we already have APKs in storage
            existing_apks = [f for f in os.listdir(self.apk_storage_dir) if f.endswith('.apk')]
            
            if len(existing_apks) < 3:  # Create samples if we have fewer than 3
                print("Creating sample APK files...")
                result = self.apk_creator.create_sample_apps()
                
                if result['success']:
                    # Move created APKs to storage directory
                    for apk_info in result['apks']:
                        source_path = apk_info['apk_path']
                        filename = os.path.basename(source_path)
                        dest_path = os.path.join(self.apk_storage_dir, filename)
                        
                        if os.path.exists(source_path):
                            shutil.move(source_path, dest_path)
                            
                            # Store in database
                            self._store_apk_in_database(dest_path, apk_info)
                
                print(f"Sample APKs initialized: {result.get('created_count', 0)} files")
                
        except Exception as e:
            print(f"Error initializing sample APKs: {str(e)}")
    
    def create_apk(self, app_specification):
        """Create a new APK from specification"""
        try:
            # Create the APK
            result = self.apk_creator.create_apk(app_specification)
            
            if result['success']:
                # Move to storage directory
                source_path = result['apk_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(self.apk_storage_dir, filename)
                
                if os.path.exists(source_path):
                    shutil.move(source_path, dest_path)
                    result['apk_path'] = dest_path
                    
                    # Store in database
                    self._store_apk_in_database(dest_path, result)
                    
                    # Analyze the created APK
                    analysis_result = self.analyze_apk(dest_path)
                    result['analysis'] = analysis_result
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create APK: {str(e)}"
            }
    
    def import_apk(self, apk_file_path):
        """Import an existing APK file"""
        try:
            if not os.path.exists(apk_file_path):
                return {
                    'success': False,
                    'error': "APK file not found"
                }
            
            if not apk_file_path.endswith('.apk'):
                return {
                    'success': False,
                    'error': "File is not an APK"
                }
            
            # Copy to storage directory
            filename = os.path.basename(apk_file_path)
            dest_path = os.path.join(self.apk_storage_dir, filename)
            
            # Handle duplicate names
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                new_filename = f"{base_name}_{counter}{ext}"
                dest_path = os.path.join(self.apk_storage_dir, new_filename)
                counter += 1
            
            shutil.copy2(apk_file_path, dest_path)
            
            # Analyze the imported APK
            analysis_result = self.analyze_apk(dest_path)
            
            if analysis_result['success']:
                # Store in database
                apk_info = {
                    'apk_path': dest_path,
                    'app_name': analysis_result['analysis'].get('app_name', 'Unknown'),
                    'package_name': analysis_result['analysis'].get('package_name', 'unknown.package'),
                    'version': analysis_result['analysis'].get('version_name', '1.0')
                }
                self._store_apk_in_database(dest_path, apk_info)
            
            return {
                'success': True,
                'apk_path': dest_path,
                'analysis': analysis_result,
                'message': f"APK imported successfully: {os.path.basename(dest_path)}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to import APK: {str(e)}"
            }
    
    def analyze_apk(self, apk_path):
        """Analyze an APK file"""
        try:
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'error': "APK file not found"
                }
            
            # Perform analysis
            analysis = self.apk_analyzer.analyze_apk(apk_path)
            
            return {
                'success': True,
                'analysis': analysis,
                'apk_path': apk_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to analyze APK: {str(e)}"
            }
    
    def extract_apk(self, apk_path, extract_features=True):
        """Extract APK contents and optionally extract features"""
        try:
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'error': "APK file not found"
                }
            
            # Create extraction directory
            apk_name = os.path.splitext(os.path.basename(apk_path))[0]
            extract_dir = os.path.join(self.extracted_dir, apk_name)
            
            # Extract APK contents
            extraction_result = self.apk_analyzer.extract_apk_contents(apk_path, extract_dir)
            
            result = {
                'success': True,
                'apk_path': apk_path,
                'extract_dir': extract_dir,
                'extraction_result': extraction_result
            }
            
            # Extract features if requested
            if extract_features:
                try:
                    feature_result = self.ui_extractor.extract_from_apk(apk_path)
                    result['features'] = feature_result
                except Exception as e:
                    result['feature_extraction_error'] = str(e)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract APK: {str(e)}"
            }
    
    def get_stored_apks(self):
        """Get list of stored APK files"""
        try:
            apks = []
            
            # Get APKs from storage directory
            for filename in os.listdir(self.apk_storage_dir):
                if filename.endswith('.apk'):
                    apk_path = os.path.join(self.apk_storage_dir, filename)
                    
                    # Get file info
                    stat_info = os.stat(apk_path)
                    file_size = stat_info.st_size
                    modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # Try to get analysis info from database
                    app_info = self._get_apk_from_database(apk_path)
                    
                    apk_info = {
                        'filename': filename,
                        'path': apk_path,
                        'size': file_size,
                        'formatted_size': self._format_size(file_size),
                        'modified_time': modified_time.isoformat(),
                        'formatted_time': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'app_name': app_info.get('app_name', 'Unknown') if app_info else 'Unknown',
                        'package_name': app_info.get('package_name', 'unknown') if app_info else 'unknown',
                        'version': app_info.get('version', '1.0') if app_info else '1.0'
                    }
                    
                    apks.append(apk_info)
            
            # Sort by modified time (newest first)
            apks.sort(key=lambda x: x['modified_time'], reverse=True)
            
            return {
                'success': True,
                'apks': apks,
                'count': len(apks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get stored APKs: {str(e)}"
            }
    
    def delete_apk(self, apk_path):
        """Delete an APK file"""
        try:
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'error': "APK file not found"
                }
            
            # Delete the file
            os.remove(apk_path)
            
            # Remove from database
            self._remove_apk_from_database(apk_path)
            
            # Clean up extraction directory if it exists
            apk_name = os.path.splitext(os.path.basename(apk_path))[0]
            extract_dir = os.path.join(self.extracted_dir, apk_name)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            
            return {
                'success': True,
                'message': f"APK deleted successfully: {os.path.basename(apk_path)}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to delete APK: {str(e)}"
            }
    
    def create_from_template(self, template_name, custom_params=None):
        """Create APK from template"""
        try:
            result = self.apk_creator.create_apk_from_template(template_name, custom_params)
            
            if result['success']:
                # Move to storage directory
                source_path = result['apk_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(self.apk_storage_dir, filename)
                
                if os.path.exists(source_path):
                    shutil.move(source_path, dest_path)
                    result['apk_path'] = dest_path
                    
                    # Store in database
                    self._store_apk_in_database(dest_path, result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create APK from template: {str(e)}"
            }
    
    def get_apk_analysis(self, apk_path):
        """Get detailed analysis of an APK"""
        try:
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'error': "APK file not found"
                }
            
            # Get basic analysis
            analysis_result = self.analyze_apk(apk_path)
            
            if not analysis_result['success']:
                return analysis_result
            
            # Get file information
            stat_info = os.stat(apk_path)
            file_info = {
                'filename': os.path.basename(apk_path),
                'path': apk_path,
                'size': stat_info.st_size,
                'formatted_size': self._format_size(stat_info.st_size),
                'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'formatted_time': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return {
                'success': True,
                'file_info': file_info,
                'analysis': analysis_result['analysis']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get APK analysis: {str(e)}"
            }
    
    def compare_apks(self, apk_path1, apk_path2):
        """Compare two APK files"""
        try:
            if not os.path.exists(apk_path1) or not os.path.exists(apk_path2):
                return {
                    'success': False,
                    'error': "One or both APK files not found"
                }
            
            # Compare using analyzer
            comparison_result = self.apk_analyzer.compare_apks(apk_path1, apk_path2)
            
            return {
                'success': True,
                'comparison': comparison_result,
                'apk1': apk_path1,
                'apk2': apk_path2
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to compare APKs: {str(e)}"
            }
    
    def _store_apk_in_database(self, apk_path, apk_info):
        """Store APK information in database"""
        try:
            session = db_manager.get_session()
            if not session:
                return
            
            # Check if application already exists
            existing_app = session.query(Application).filter_by(
                package_name=apk_info.get('package_name', 'unknown')
            ).first()
            
            if existing_app:
                # Update existing
                existing_app.name = apk_info.get('app_name', existing_app.name)
                existing_app.version = apk_info.get('version', existing_app.version)
                existing_app.apk_path = apk_path
                existing_app.updated_at = datetime.utcnow()
            else:
                # Create new
                new_app = Application(
                    name=apk_info.get('app_name', 'Unknown App'),
                    package_name=apk_info.get('package_name', 'unknown.package'),
                    version=apk_info.get('version', '1.0'),
                    description=f"Generated/imported APK: {apk_info.get('app_name', 'Unknown')}",
                    apk_path=apk_path,
                    category='imported',
                    source='created_by_drive_manager'
                )
                session.add(new_app)
            
            session.commit()
            session.close()
            
        except Exception as e:
            print(f"Error storing APK in database: {str(e)}")
    
    def _get_apk_from_database(self, apk_path):
        """Get APK information from database"""
        try:
            session = db_manager.get_session()
            if not session:
                return None
            
            app = session.query(Application).filter_by(apk_path=apk_path).first()
            session.close()
            
            if app:
                return {
                    'app_name': app.name,
                    'package_name': app.package_name,
                    'version': app.version,
                    'description': app.description,
                    'category': app.category
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting APK from database: {str(e)}")
            return None
    
    def _remove_apk_from_database(self, apk_path):
        """Remove APK information from database"""
        try:
            session = db_manager.get_session()
            if not session:
                return
            
            app = session.query(Application).filter_by(apk_path=apk_path).first()
            if app:
                session.delete(app)
                session.commit()
            
            session.close()
            
        except Exception as e:
            print(f"Error removing APK from database: {str(e)}")
    
    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    
    def get_available_templates(self):
        """Get list of available APK templates"""
        return {
            'success': True,
            'templates': [
                {
                    'name': 'basic_app',
                    'display_name': 'Basic App',
                    'description': 'Simple basic application template',
                    'category': 'basic'
                },
                {
                    'name': 'social_app',
                    'display_name': 'Social App',
                    'description': 'Social networking application template',
                    'category': 'social'
                },
                {
                    'name': 'productivity_app',
                    'display_name': 'Productivity App',
                    'description': 'Productivity and task management template',
                    'category': 'productivity'
                }
            ]
        }


# Create an instance for use in the application
apk_manager = APKManager()