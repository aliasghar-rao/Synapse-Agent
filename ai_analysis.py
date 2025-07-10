"""
AI Analysis module for Drive-Manager Pro.
Provides file analysis, tagging, and recommendations using a tiered approach.
"""

import os
import io
import json
import datetime
import random
import hashlib
import logging
import time
import requests
from database import db_manager
from models import Base, File, Tag, Recommendation, OllamaModelCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Multiple service endpoints for tiered approach
LOCAL_ANALYSIS_ENDPOINT = "http://localhost:5001/api/analyze"  # Local lightweight models
REMOTE_ANALYSIS_ENDPOINT = "http://192.168.1.100:5002/api/analyze"  # Remote laptop service
CLOUD_ANALYSIS_ENDPOINT = "https://ai-analysis.cloud.example.com/analyze"  # Cloud service

# Default to local for initial setup
DEFAULT_ANALYSIS_ENDPOINT = LOCAL_ANALYSIS_ENDPOINT

# Model categories by tier
TIER1_MODELS = ["tinybert", "fasttagger", "smallanalyzer"]  # Lightweight local models
TIER2_MODELS = ["bert-base", "file-analyzer", "tag-generator-large"]  # Remote laptop models
TIER3_MODELS = ["gpt-4o", "claude-3", "gemini-pro"]  # External API models

class AIAnalysisManager:
    """Manager for AI file analysis functionality using a tiered approach"""
    
    def __init__(self):
        self.analysis_results = {}
        self.analysis_cache = {}
        
        # Track the available endpoints
        self.endpoints = {
            "tier1": {
                "url": LOCAL_ANALYSIS_ENDPOINT,
                "available": self._check_endpoint_available(LOCAL_ANALYSIS_ENDPOINT),
                "models": TIER1_MODELS
            },
            "tier2": {
                "url": REMOTE_ANALYSIS_ENDPOINT,
                "available": self._check_endpoint_available(REMOTE_ANALYSIS_ENDPOINT),
                "models": TIER2_MODELS,
                "learning_enabled": True
            },
            "tier3": {
                "url": None,  # External APIs don't have a single URL
                "available": True,  # Assume external APIs are available
                "models": TIER3_MODELS
            }
        }
    
    def _check_endpoint_available(self, url):
        """Check if an endpoint is available"""
        try:
            response = requests.get(f"{url}/status", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
        
    def _calculate_file_hash(self, file_path):
        """Calculate a hash for a file to check for cached analysis results"""
        try:
            if not os.path.exists(file_path):
                return None
                
            # For small files, use the entire file
            if os.path.getsize(file_path) < 10 * 1024 * 1024:  # 10MB
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                return file_hash
            
            # For larger files, sample the beginning, middle, and end
            with open(file_path, 'rb') as f:
                # Read first 1MB
                beginning = f.read(1024 * 1024)
                
                # Go to the middle and read 1MB
                f.seek(os.path.getsize(file_path) // 2)
                middle = f.read(1024 * 1024)
                
                # Go to the end (minus 1MB) and read 1MB
                f.seek(-1024 * 1024, 2)
                end = f.read(1024 * 1024)
                
                # Combine samples and hash
                file_hash = hashlib.md5(beginning + middle + end).hexdigest()
                
            return file_hash
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None
    
    def analyze_file(self, file_metadata):
        """Analyze a single file and extract information using tiered approach"""
        # Check if we have cached results
        file_hash = self._calculate_file_hash(file_metadata.path)
        if file_hash and file_hash in self.analysis_cache:
            logger.info(f"Using cached analysis for {file_metadata.name}")
            return self.analysis_cache[file_hash]
        
        # Check if file exists and is accessible
        if not os.path.exists(file_metadata.path) or not os.access(file_metadata.path, os.R_OK):
            logger.warning(f"File {file_metadata.path} does not exist or is not readable")
            return self._generate_basic_analysis(file_metadata)
        
        # Try to analyze with tiered approach
        analysis = None
        
        # Tier 1: Local lightweight analysis
        if self.endpoints["tier1"]["available"]:
            logger.info(f"Using Tier 1 analysis for {file_metadata.name}")
            analysis = self._analyze_with_endpoint(
                self.endpoints["tier1"]["url"], 
                file_metadata, 
                self.endpoints["tier1"]["models"][0]  # Use first available model
            )
        
        # Tier 2: Remote laptop service with learning
        if not analysis and self.endpoints["tier2"]["available"]:
            logger.info(f"Using Tier 2 analysis for {file_metadata.name}")
            analysis = self._analyze_with_endpoint(
                self.endpoints["tier2"]["url"], 
                file_metadata,
                self.endpoints["tier2"]["models"][0]  # Use first available model
            )
            
            # If analysis succeeded and learning is enabled, store results
            if analysis and self.endpoints["tier2"]["learning_enabled"]:
                self._store_analysis_in_cache(file_metadata, analysis, file_hash)
        
        # Tier 3: External API (OpenAI, etc.)
        if not analysis:
            logger.info(f"Using Tier 3 analysis for {file_metadata.name}")
            try:
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    analysis = self._analyze_with_openai(file_metadata, api_key)
            except Exception as e:
                logger.error(f"Error using OpenAI for analysis: {e}")
        
        # Fallback to basic analysis if all tiers failed
        if not analysis:
            logger.warning(f"All tiers failed, using basic analysis for {file_metadata.name}")
            analysis = self._generate_basic_analysis(file_metadata)
        
        # Cache the result
        if file_hash:
            self.analysis_cache[file_hash] = analysis
            
        return analysis
    
    def _analyze_with_endpoint(self, endpoint_url, file_metadata, model_name):
        """Analyze a file using a specific endpoint"""
        try:
            # For text files: Read content and send it
            if self._is_text_file(file_metadata.path):
                with open(file_metadata.path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1024 * 1024)  # Limit to 1MB
                
                payload = {
                    "filename": file_metadata.name,
                    "file_type": "text",
                    "content": content,
                    "metadata": {
                        "size": file_metadata.size,
                        "created": file_metadata.created_time.isoformat() if file_metadata.created_time else None,
                        "modified": file_metadata.modified_time.isoformat() if file_metadata.modified_time else None,
                        "path": file_metadata.path
                    },
                    "model": model_name
                }
                
                # In a real implementation:
                # response = requests.post(f"{endpoint_url}/text", json=payload, timeout=30)
                # if response.status_code == 200:
                #     return response.json()
                
                # For demonstration, use the mock analysis
                return self._generate_mock_analysis(file_metadata)
            
            # For binary files: Send metadata only
            else:
                payload = {
                    "filename": file_metadata.name,
                    "file_type": "binary",
                    "metadata": {
                        "size": file_metadata.size,
                        "extension": os.path.splitext(file_metadata.name)[1],
                        "created": file_metadata.created_time.isoformat() if file_metadata.created_time else None,
                        "modified": file_metadata.modified_time.isoformat() if file_metadata.modified_time else None,
                        "path": file_metadata.path
                    },
                    "model": model_name
                }
                
                # In a real implementation:
                # response = requests.post(f"{endpoint_url}/binary", json=payload, timeout=30)
                # if response.status_code == 200:
                #     return response.json()
                
                # For demonstration, use the mock analysis
                return self._generate_mock_analysis(file_metadata)
                
        except Exception as e:
            logger.error(f"Error analyzing with endpoint {endpoint_url}: {e}")
            return None
    
    def _analyze_with_openai(self, file_metadata, api_key):
        """Analyze a file using OpenAI's API"""
        try:
            # Import here to avoid dependency if not using OpenAI
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Only analyze text files with OpenAI
            if not self._is_text_file(file_metadata.path):
                return self._generate_basic_analysis(file_metadata)
            
            # Read the file content
            with open(file_metadata.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024 * 1024)  # Limit to 1MB
            
            # Prepare the prompt
            prompt = f"""
            Analyze this file:
            Filename: {file_metadata.name}
            Size: {file_metadata.size} bytes
            Content type: {self._guess_content_type(file_metadata.name)}
            
            Content excerpt:
            {content[:2000]}... (truncated)
            
            Generate a detailed analysis including:
            1. What this file is about
            2. Appropriate tags for organizing this file
            3. Any recommendations for file organization
            4. File classification (document, code, etc.)
            
            Respond in valid JSON format with these keys:
            - summary
            - tags (array)
            - content_type
            - recommendations (array)
            - classification
            """
            
            # Call the API
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Format the analysis
            analysis = {
                'filename': file_metadata.name,
                'extension': os.path.splitext(file_metadata.name)[1],
                'size': file_metadata.size,
                'content_type': result.get('content_type', self._guess_content_type(file_metadata.name)),
                'summary': result.get('summary', ''),
                'suggested_tags': result.get('tags', []),
                'classification': result.get('classification', ''),
                'recommendations': result.get('recommendations', []),
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error using OpenAI for analysis: {e}")
            return None
    
    def _store_analysis_in_cache(self, file_metadata, analysis, file_hash):
        """Store analysis results in the database cache for learning"""
        session = db_manager.get_session()
        if not session:
            return
        
        try:
            # Check if this file hash already exists in the cache
            existing_entry = session.query(OllamaModelCache).filter_by(
                result_hash=file_hash,
                media_type="analysis"
            ).first()
            
            # If it exists, update it
            if existing_entry:
                existing_entry.result_data = json.dumps(analysis).encode()
                existing_entry.updated_at = datetime.datetime.now()
            else:
                # Create a new cache entry
                cache_entry = OllamaModelCache(
                    model_name="file-analyzer",
                    prompt=file_metadata.path,
                    parameters=json.dumps({"filename": file_metadata.name, "size": file_metadata.size}),
                    result_hash=file_hash,
                    result_data=json.dumps(analysis).encode(),
                    media_type="analysis"
                )
                
                session.add(cache_entry)
                
            session.commit()
            logger.info(f"Stored analysis in cache for {file_metadata.name}")
            
        except Exception as e:
            logger.error(f"Error storing analysis in cache: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def analyze_directory(self, file_metadatas):
        """Analyze a group of files from a directory using tiered approach"""
        # Analyze each file with our tiered approach
        analyses = []
        for metadata in file_metadatas:
            analyses.append(self.analyze_file(metadata))
        
        common_tags = self._find_common_tags(analyses)
        return {
            'file_analyses': analyses,
            'common_tags': common_tags,
            'file_count': len(analyses),
            'total_size': sum(a.get('size', 0) for a in analyses),
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def detect_duplicates(self):
        """Detect duplicate files based on hash using tiered approach"""
        # In a real implementation, this would scan for duplicate files using content hash
        # and utilize the tiered approach for complex comparison
        
        # For demonstration, return mock duplicates
        duplicates = [
            {
                'original': {'name': 'document.pdf', 'path': '/documents/work/document.pdf', 'size': 1024*1024},
                'duplicates': [
                    {'name': 'document_copy.pdf', 'path': '/documents/personal/document_copy.pdf', 'size': 1024*1024},
                    {'name': 'document_backup.pdf', 'path': '/backups/document_backup.pdf', 'size': 1024*1024}
                ]
            },
            {
                'original': {'name': 'image.jpg', 'path': '/photos/vacation/image.jpg', 'size': 2*1024*1024},
                'duplicates': [
                    {'name': 'image_edited.jpg', 'path': '/photos/edited/image_edited.jpg', 'size': 2*1024*1024}
                ]
            }
        ]
        return duplicates
    
    def detect_obsolete_files(self):
        """Detect potentially obsolete files (not accessed in a long time) using tiered approach"""
        # In a real implementation, this would use the tiered approach for analysis
        
        # For demonstration, return mock obsolete files
        obsolete_files = [
            {'name': 'old_project.zip', 'path': '/archives/old_project.zip', 'last_accessed': '2022-01-15', 'size': 1024*1024*5},
            {'name': 'meeting_notes_2021.docx', 'path': '/documents/meeting_notes_2021.docx', 'last_accessed': '2022-02-20', 'size': 1024*50},
            {'name': 'temp_file.tmp', 'path': '/temp/temp_file.tmp', 'last_accessed': '2022-03-10', 'size': 1024*1024}
        ]
        return obsolete_files
    
    def generate_recommendations(self):
        """Generate recommendations based on analysis using tiered approach"""
        # In a real implementation, this would use the tiered approach for analysis
        
        # For demonstration, generate mock recommendations
        recommendations = self._generate_mock_recommendations()
        
        # Store recommendations in the database
        self._store_recommendations(recommendations)
        
        return recommendations
    
    def _store_recommendations(self, recommendations):
        """Store recommendations in the database"""
        session = db_manager.get_session()
        if not session:
            return
        
        try:
            for rec in recommendations:
                # Create a file record for reference if needed
                file_id = None
                if 'details' in rec and 'path' in rec['details']:
                    # Check if the file exists in the database
                    file = session.query(File).filter_by(path=rec['details']['path']).first()
                    if file:
                        file_id = file.id
                
                # Create the recommendation
                recommendation = Recommendation(
                    file_id=file_id,
                    recommendation_type=rec['type'],
                    description=rec['description'],
                    severity=rec['severity'],
                    is_dismissed=False
                )
                
                session.add(recommendation)
            
            session.commit()
            logger.info(f"Stored {len(recommendations)} recommendations in the database")
            
        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def suggest_tags(self, file_metadata):
        """Suggest tags for a file based on content and context using tiered approach"""
        # In a real implementation, this would use the tiered approach for analysis
        
        # For demonstration, return tags based on file extension
        extension = os.path.splitext(file_metadata.name)[1].lower()
        
        tag_sets = {
            '.pdf': ['document', 'report', 'reading'],
            '.docx': ['document', 'writing', 'work'],
            '.xlsx': ['spreadsheet', 'data', 'finance'],
            '.pptx': ['presentation', 'slides', 'meeting'],
            '.jpg': ['image', 'photo', 'visual'],
            '.png': ['image', 'graphic', 'screenshot'],
            '.mp3': ['audio', 'music', 'sound'],
            '.mp4': ['video', 'movie', 'media'],
            '.zip': ['archive', 'compressed', 'backup'],
            '.py': ['code', 'python', 'development'],
            '.js': ['code', 'javascript', 'web'],
            '.html': ['code', 'web', 'frontend'],
            '.css': ['code', 'web', 'style']
        }
        
        # Return default tags or extension-specific tags
        return tag_sets.get(extension, ['file', 'document', 'data'])
    
    def _generate_basic_analysis(self, file_metadata):
        """Generate basic analysis with minimal information (fallback)"""
        return {
            'filename': file_metadata.name,
            'extension': os.path.splitext(file_metadata.name)[1],
            'size': file_metadata.size,
            'content_type': self._guess_content_type(file_metadata.name),
            'suggested_tags': self.suggest_tags(file_metadata),
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def _generate_mock_analysis(self, file_metadata):
        """Generate more detailed mock analysis for demonstration"""
        extension = os.path.splitext(file_metadata.name)[1].lower()
        
        # Base analysis
        analysis = self._generate_basic_analysis(file_metadata)
        
        # Add more details based on extension
        if extension in ['.pdf', '.docx', '.txt']:
            analysis['document_type'] = 'text'
            analysis['estimated_word_count'] = random.randint(500, 5000)
            analysis['estimated_read_time'] = f"{random.randint(2, 30)} minutes"
            analysis['contains_images'] = random.choice([True, False])
            analysis['language'] = random.choice(['English', 'Spanish', 'French', 'German'])
            analysis['summary'] = "This document appears to contain text content related to business or technical documentation."
            
        elif extension in ['.jpg', '.png', '.gif']:
            analysis['document_type'] = 'image'
            analysis['dimensions'] = f"{random.randint(800, 3000)}x{random.randint(600, 2000)}"
            analysis['color_profile'] = random.choice(['RGB', 'CMYK', 'Grayscale'])
            analysis['estimated_objects'] = random.randint(1, 10)
            analysis['contains_people'] = random.choice([True, False])
            analysis['summary'] = "This image likely contains visual content that may include people, landscapes, or objects."
            
        elif extension in ['.mp3', '.wav', '.flac']:
            analysis['document_type'] = 'audio'
            analysis['duration'] = f"{random.randint(1, 10)}:{random.randint(0, 59):02d}"
            analysis['bitrate'] = f"{random.choice([128, 192, 256, 320])} kbps"
            analysis['channels'] = random.choice(['Mono', 'Stereo'])
            analysis['summary'] = "This audio file contains sound that may be music, voice, or other audio content."
            
        elif extension in ['.mp4', '.avi', '.mov']:
            analysis['document_type'] = 'video'
            analysis['duration'] = f"{random.randint(1, 120)}:{random.randint(0, 59):02d}"
            analysis['resolution'] = random.choice(['720p', '1080p', '4K'])
            analysis['fps'] = random.choice([24, 30, 60])
            analysis['has_audio'] = random.choice([True, False])
            analysis['summary'] = "This video file contains moving visual content that may include people, scenes, or animations."
            
        elif extension in ['.py', '.js', '.html', '.css', '.java', '.cpp']:
            analysis['document_type'] = 'code'
            analysis['estimated_line_count'] = random.randint(50, 1000)
            analysis['functions_count'] = random.randint(5, 50)
            analysis['language'] = self._get_programming_language(extension)
            analysis['has_comments'] = random.choice([True, False])
            analysis['summary'] = f"This file contains {self._get_programming_language(extension)} code with multiple functions and classes."
            
        return analysis
    
    def _generate_mock_recommendations(self):
        """Generate mock recommendations for demonstration"""
        recommendations = [
            {
                'id': 1,
                'type': 'duplicate_files',
                'severity': 4,
                'description': 'Found 5 sets of duplicate files taking up 1.2 GB of space',
                'details': {
                    'duplicate_sets': 5,
                    'total_size': 1.2 * 1024 * 1024 * 1024,
                    'potential_saving': '1.2 GB'
                },
                'action': 'review_duplicates',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'id': 2,
                'type': 'obsolete_files',
                'severity': 3,
                'description': 'Found 12 files not accessed in over 1 year',
                'details': {
                    'file_count': 12,
                    'total_size': 0.5 * 1024 * 1024 * 1024,
                    'oldest_file': '2.5 years old'
                },
                'action': 'review_obsolete',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'id': 3,
                'type': 'organization',
                'severity': 2,
                'description': 'Large number of mixed file types in Downloads folder',
                'details': {
                    'folder': 'Downloads',
                    'file_count': 45,
                    'different_types': 8,
                    'suggestion': 'Create subfolders by file type'
                },
                'action': 'organize_folder',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'id': 4,
                'type': 'backup',
                'severity': 5,
                'description': 'Important documents folder not backed up recently',
                'details': {
                    'folder': 'Documents/Important',
                    'last_backup': '65 days ago',
                    'file_count': 23,
                    'suggestion': 'Schedule regular backups'
                },
                'action': 'backup_folder',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'id': 5,
                'type': 'large_files',
                'severity': 3,
                'description': 'Found 3 unusually large files that may be candidates for archiving',
                'details': {
                    'file_count': 3,
                    'total_size': 4.5 * 1024 * 1024 * 1024,
                    'largest_file': 'project_backup.zip (2.2 GB)',
                    'suggestion': 'Consider archiving to external storage'
                },
                'action': 'review_large_files',
                'timestamp': datetime.datetime.now().isoformat()
            }
        ]
        return recommendations
    
    def _guess_content_type(self, filename):
        """Guess the content type of a file based on extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.zip': 'application/zip',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.py': 'text/x-python',
            '.c': 'text/x-c',
            '.cpp': 'text/x-c++',
            '.java': 'text/x-java',
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def _get_programming_language(self, extension):
        """Get the programming language based on file extension"""
        languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.ts': 'TypeScript',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.rs': 'Rust'
        }
        
        return languages.get(extension, 'Unknown')
    
    def _is_text_file(self, file_path):
        """Check if a file is a text file based on extension and content"""
        # Check extension first
        extension = os.path.splitext(file_path)[1].lower()
        text_extensions = ['.txt', '.md', '.html', '.css', '.js', '.py', '.java', '.c', '.cpp', 
                          '.h', '.json', '.xml', '.csv', '.log', '.sh', '.bat', '.ps1', '.yaml', 
                          '.yml', '.ini', '.cfg', '.conf', '.php', '.rb', '.ts', '.go', '.rs']
        
        if extension in text_extensions:
            return True
        
        # If file doesn't exist or is too large, consider it binary
        if not os.path.exists(file_path) or os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
            return False
        
        # Try to open and read as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 1024 bytes
                sample = f.read(1024)
                
                # Check for null bytes (common in binary files)
                if '\0' in sample:
                    return False
                
                # Check if at least 90% of characters are printable ASCII
                printable_count = sum(1 for c in sample if 32 <= ord(c) <= 126 or c in '\n\r\t')
                if printable_count / len(sample) < 0.9:
                    return False
                
                return True
        except Exception:
            return False
    
    def _find_common_tags(self, analyses):
        """Find common tags across multiple files"""
        if not analyses:
            return []
        
        # Extract all tags from all analyses
        all_tags = {}
        for analysis in analyses:
            for tag in analysis.get('suggested_tags', []):
                all_tags[tag] = all_tags.get(tag, 0) + 1
        
        # Find tags that appear in more than 50% of files
        common_threshold = len(analyses) * 0.5
        common_tags = [tag for tag, count in all_tags.items() if count >= common_threshold]
        
        return common_tags

# Create an instance
ai_analysis_manager = AIAnalysisManager()