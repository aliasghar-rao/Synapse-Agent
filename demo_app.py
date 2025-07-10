"""
Drive-Manager Pro Demo (Web Version)
A simplified web-based demonstration of the Drive-Manager Pro application concept.
"""

import os
import json
import threading
import time
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

# Import database modules
import logging
import hashlib
from database import db_manager
from models import File, Tag, Application, CloudSync, Recommendation, UserPreference
from app_generator import app_generator
from account_manager import account_manager
from ai_media_generator import ai_media_generator
from file_system_web import FileMetadata, DuplicateDetector
from apk_manager import apk_manager
from module_manager import module_manager

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve the main page
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html_content().encode('utf-8'))
        
        # Serve API endpoints
        elif path == "/api/files":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_files_from_db()).encode())
        
        elif path == "/api/recommendations":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_recommendations_from_db()).encode())
        
        elif path == "/api/cloud":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_cloud_files_from_db()).encode())
        
        elif path == "/api/mindmap":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_mock_mindmap_data()).encode())
            
        # App generator API endpoints
        elif path == "/api/app-templates":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(app_generator.get_templates()).encode())
            
        elif path == "/api/generated-apps":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(app_generator.get_generated_apps()).encode())
        
        # Serve static CSS
        elif path.endswith(".css"):
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(self.get_css_content().encode('utf-8'))
        
        # Serve static JavaScript
        elif path.endswith(".js"):
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.get_js_content().encode('utf-8'))
        
        # Module management GET endpoints
        elif path == "/api/modules/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = module_manager.get_module_status()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/api/modules/ui-components":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = module_manager.get_ui_component_states()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/api/modules/config":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = module_manager.get_module_configuration()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/api/modules/build-config":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = module_manager.get_build_configuration()
            self.wfile.write(json.dumps(result).encode())
        
        # Handle 404 for everything else
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Get content length from headers
        content_length = int(self.headers['Content-Length'])
        
        # Read and parse the request body
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        
        # App generation endpoint
        if path == "/api/generate-app":
            prompt = request_data.get('prompt', '')
            name = request_data.get('name', None)
            
            if not prompt:
                self._send_json_response(400, {"error": "Prompt is required"})
                return
            
            # Call the app generator
            result = app_generator.create_app(prompt, name)
            
            if "error" in result:
                self._send_json_response(400, result)
            else:
                self._send_json_response(200, result)
                
        # User registration endpoint
        elif path == "/api/auth/register":
            username = request_data.get('username', '')
            email = request_data.get('email', '')
            password = request_data.get('password', '')
            first_name = request_data.get('first_name', None)
            last_name = request_data.get('last_name', None)
            
            if not username or not email or not password:
                self._send_json_response(400, {"error": "Username, email, and password are required"})
                return
            
            # Register the user
            result = account_manager.register_user(username, email, password, first_name, last_name)
            
            if result.get("success"):
                self._send_json_response(201, result)
            else:
                self._send_json_response(400, result)
        
        # User login endpoint
        elif path == "/api/auth/login":
            username_or_email = request_data.get('username_or_email', '')
            password = request_data.get('password', '')
            
            if not username_or_email or not password:
                self._send_json_response(400, {"error": "Username/email and password are required"})
                return
            
            # Get client information for session tracking
            ip_address = self.client_address[0]
            user_agent = self.headers.get('User-Agent', '')
            
            # Login the user
            result = account_manager.login(username_or_email, password, ip_address, user_agent)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(401, result)
        
        # Session validation endpoint
        elif path == "/api/auth/session":
            session_token = request_data.get('session_token', '')
            
            if not session_token:
                self._send_json_response(400, {"error": "Session token is required"})
                return
            
            # Validate the session
            result = account_manager.validate_session(session_token)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(401, result)
                
        # User logout endpoint
        elif path == "/api/auth/logout":
            session_token = request_data.get('session_token', '')
            
            if not session_token:
                self._send_json_response(400, {"error": "Session token is required"})
                return
            
            # Logout the user
            result = account_manager.logout(session_token)
            self._send_json_response(200, result)
            
        # Update user profile endpoint
        elif path == "/api/users/profile":
            user_id = request_data.get('user_id', None)
            profile_data = request_data.get('profile_data', {})
            
            if not user_id:
                self._send_json_response(400, {"error": "User ID is required"})
                return
            
            # Update the user profile
            result = account_manager.update_user_profile(user_id, profile_data)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
                
        # Change password endpoint
        elif path == "/api/auth/change-password":
            user_id = request_data.get('user_id', None)
            current_password = request_data.get('current_password', '')
            new_password = request_data.get('new_password', '')
            
            if not user_id or not current_password or not new_password:
                self._send_json_response(400, {"error": "User ID, current password, and new password are required"})
                return
            
            # Change the password
            result = account_manager.change_password(user_id, current_password, new_password)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
                
        # AI Image Generation endpoint
        elif path == "/api/media/generate-image":
            prompt = request_data.get('prompt', '')
            model_name = request_data.get('model_name', None)
            negative_prompt = request_data.get('negative_prompt', None)
            width = request_data.get('width', None)
            height = request_data.get('height', None)
            seed = request_data.get('seed', None)
            parameters = request_data.get('parameters', None)
            save_path = request_data.get('save_path', None)
            
            if not prompt:
                self._send_json_response(400, {"error": "Prompt is required"})
                return
            
            # Generate the image
            result = ai_media_generator.generate_image(
                prompt, model_name, negative_prompt, width, height, seed, parameters, save_path
            )
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # AI Video Generation endpoint
        elif path == "/api/media/generate-video":
            prompt = request_data.get('prompt', '')
            model_name = request_data.get('model_name', None)
            negative_prompt = request_data.get('negative_prompt', None)
            width = request_data.get('width', None)
            height = request_data.get('height', None)
            duration = request_data.get('duration', None)
            fps = request_data.get('fps', None)
            seed = request_data.get('seed', None)
            parameters = request_data.get('parameters', None)
            save_path = request_data.get('save_path', None)
            
            if not prompt:
                self._send_json_response(400, {"error": "Prompt is required"})
                return
            
            # Generate the video
            result = ai_media_generator.generate_video(
                prompt, model_name, negative_prompt, width, height, duration, fps, seed, parameters, save_path
            )
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Get AI Media Models endpoint
        elif path == "/api/media/models":
            media_type = request_data.get('media_type', None)
            
            # Get available models
            models = ai_media_generator.get_models(media_type)
            self._send_json_response(200, {"success": True, "models": models})
        
        # Check Media Generation Status endpoint
        elif path == "/api/media/status":
            media_id = request_data.get('media_id', None)
            
            if not media_id:
                self._send_json_response(400, {"error": "Media ID is required"})
                return
            
            # Check the status
            result = ai_media_generator.check_generation_status(media_id)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Get Generated Media endpoint
        elif path == "/api/media/list":
            media_type = request_data.get('media_type', None)
            status = request_data.get('status', None)
            limit = request_data.get('limit', 20)
            offset = request_data.get('offset', 0)
            
            # Get the media items
            media_items = ai_media_generator.get_generated_media(
                None, media_type, status, limit, offset
            )
            
            self._send_json_response(200, {
                "success": True,
                "media_items": media_items,
                "count": len(media_items)
            })
        
        # APK Management endpoints
        
        # Create APK endpoint
        elif path == "/api/apk/create":
            app_spec = request_data.get('app_spec', {})
            
            if not app_spec:
                self._send_json_response(400, {"error": "App specification is required"})
                return
            
            # Create the APK
            result = apk_manager.create_apk(app_spec)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Create APK from template endpoint
        elif path == "/api/apk/create-from-template":
            template_name = request_data.get('template_name', '')
            custom_params = request_data.get('custom_params', None)
            
            if not template_name:
                self._send_json_response(400, {"error": "Template name is required"})
                return
            
            # Create APK from template
            result = apk_manager.create_from_template(template_name, custom_params)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Import APK endpoint
        elif path == "/api/apk/import":
            apk_file_path = request_data.get('apk_file_path', '')
            
            if not apk_file_path:
                self._send_json_response(400, {"error": "APK file path is required"})
                return
            
            # Import the APK
            result = apk_manager.import_apk(apk_file_path)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Analyze APK endpoint
        elif path == "/api/apk/analyze":
            apk_path = request_data.get('apk_path', '')
            
            if not apk_path:
                self._send_json_response(400, {"error": "APK path is required"})
                return
            
            # Analyze the APK
            result = apk_manager.get_apk_analysis(apk_path)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Extract APK endpoint
        elif path == "/api/apk/extract":
            apk_path = request_data.get('apk_path', '')
            extract_features = request_data.get('extract_features', True)
            
            if not apk_path:
                self._send_json_response(400, {"error": "APK path is required"})
                return
            
            # Extract the APK
            result = apk_manager.extract_apk(apk_path, extract_features)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Get stored APKs endpoint
        elif path == "/api/apk/list":
            # Get stored APKs
            result = apk_manager.get_stored_apks()
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Delete APK endpoint
        elif path == "/api/apk/delete":
            apk_path = request_data.get('apk_path', '')
            
            if not apk_path:
                self._send_json_response(400, {"error": "APK path is required"})
                return
            
            # Delete the APK
            result = apk_manager.delete_apk(apk_path)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Compare APKs endpoint
        elif path == "/api/apk/compare":
            apk_path1 = request_data.get('apk_path1', '')
            apk_path2 = request_data.get('apk_path2', '')
            
            if not apk_path1 or not apk_path2:
                self._send_json_response(400, {"error": "Both APK paths are required"})
                return
            
            # Compare the APKs
            result = apk_manager.compare_apks(apk_path1, apk_path2)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Get APK templates endpoint
        elif path == "/api/apk/templates":
            # Get available templates
            result = apk_manager.get_available_templates()
            self._send_json_response(200, result)
        
        # Module Management endpoints
        
        # Get module status endpoint
        elif path == "/api/modules/status":
            module_id = request_data.get('module_id', None)
            result = module_manager.get_module_status(module_id)
            self._send_json_response(200, result)
        
        # Toggle module endpoint
        elif path == "/api/modules/toggle":
            module_id = request_data.get('module_id', '')
            enabled = request_data.get('enabled', None)
            
            if not module_id:
                self._send_json_response(400, {"error": "Module ID is required"})
                return
            
            result = module_manager.toggle_module(module_id, enabled)
            
            if result.get("success"):
                self._send_json_response(200, result)
            else:
                self._send_json_response(400, result)
        
        # Get UI component states endpoint
        elif path == "/api/modules/ui-components":
            result = module_manager.get_ui_component_states()
            self._send_json_response(200, result)
        
        # Get module configuration endpoint
        elif path == "/api/modules/config":
            result = module_manager.get_module_configuration()
            self._send_json_response(200, result)
        
        # Reset modules to defaults endpoint
        elif path == "/api/modules/reset":
            result = module_manager.reset_to_defaults()
            self._send_json_response(200, result)
        
        # Get build configuration endpoint
        elif path == "/api/modules/build-config":
            result = module_manager.get_build_configuration()
            self._send_json_response(200, result)
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})
    
    def _send_json_response(self, status_code, data):
        """Helper method to send JSON responses"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Serve the main page
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html_content().encode('utf-8'))
        
        # Serve API endpoints
        elif path == "/api/files":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_files_from_db()).encode())
        
        elif path == "/api/recommendations":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_recommendations_from_db()).encode())
        
        elif path == "/api/cloud":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_cloud_files_from_db()).encode())
        
        elif path == "/api/mindmap":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_mock_mindmap_data()).encode())
            
        # App generator API endpoints
        elif path == "/api/app-templates":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(app_generator.get_templates()).encode())
            
        elif path == "/api/generated-apps":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(app_generator.get_generated_apps()).encode())
        
        # Serve static CSS
        elif path.endswith(".css"):
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(self.get_css_content().encode('utf-8'))
        
        # Serve static JavaScript
        elif path.endswith(".js"):
            self.send_response(200)
            self.send_header('Content-type', 'text/javascript')
            self.end_headers()
            self.wfile.write(self.get_js_content().encode('utf-8'))
        
        # 404 Not Found for anything else
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("404 Not Found".encode('utf-8'))

    def get_html_content(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drive-Manager Pro</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-icon">
                <i class="fas fa-brain"></i>
            </div>
        </div>
        <h1>Drive-Manager Pro</h1>
        <p>Intelligent file management with neural link visualization</p>
    </header>
    
    <div class="container">
        <div class="top-section">
            <div class="panel" id="ai-panel" data-module-component="ai-analysis-panel">
                <h2><i class="fas fa-brain"></i> AI Analysis</h2>
                <div class="panel-content">
                    <div class="panel-header-action">
                        <button class="action-button refresh-btn" data-module-component="ai-analysis-panel"><i class="fas fa-sync-alt"></i> Analyze</button>
                    </div>
                    
                    <h3>File Tags</h3>
                    <div id="tags-container" class="tags" data-module-component="smart-tags"></div>
                    
                    <h3>Neural Links</h3>
                    <div id="links-container" data-module-component="ai-analysis-panel"></div>
                    
                    <h3>Smart Recommendations</h3>
                    <div id="recommendations-container" data-module-component="file-recommendations"></div>
                </div>
            </div>
            
            <div class="panel" id="cloud-panel" data-module-component="cloud-sync-panel">
                <h2><i class="fas fa-cloud"></i> Cloud Storage</h2>
                <div class="panel-content">
                    <h3>Connected Services</h3>
                    <div class="cloud-services" data-module-component="sync-settings">
                        <button class="cloud-btn google" data-module-component="sync-settings"><i class="fab fa-google-drive"></i> Google Drive</button>
                        <button class="cloud-btn dropbox" data-module-component="sync-settings"><i class="fab fa-dropbox"></i> Dropbox</button>
                        <button class="cloud-btn onedrive" data-module-component="sync-settings"><i class="fab fa-microsoft"></i> OneDrive</button>
                    </div>
                    
                    <h3>Cloud Files</h3>
                    <div id="cloud-files-container" data-module-component="cloud-sync-panel"></div>
                    <div class="status" data-module-component="cloud-status"><i class="fas fa-check-circle"></i> Connected to Google Drive</div>
                </div>
            </div>
            
            <div class="panel" id="tools-panel" data-module-component="file-browser">
                <h2><i class="fas fa-toolbox"></i> Tools & Functions</h2>
                <div class="panel-content">
                    <h3>File Explorer</h3>
                    <div class="search-bar" data-module-component="search-bar">
                        <i class="fas fa-search"></i>
                        <input type="text" placeholder="Search files..." data-module-component="advanced-search">
                    </div>
                    
                    <div class="path-nav" data-module-component="file-browser">
                        <i class="fas fa-folder-open"></i>
                        <span>Path: </span>
                        <span id="current-path">/home/user</span>
                        <button data-module-component="file-operations"><i class="fas fa-arrow-up"></i></button>
                    </div>
                    
                    <div id="file-list-container" data-module-component="file-metadata"></div>
                    
                    <div class="file-operations" data-module-component="file-operations">
                        <button data-module-component="file-operations"><i class="fas fa-folder-plus"></i> New Folder</button>
                        <button data-module-component="file-operations"><i class="fas fa-copy"></i> Copy</button>
                        <button data-module-component="file-operations"><i class="fas fa-cut"></i> Move</button>
                        <button data-module-component="file-operations"><i class="fas fa-trash-alt"></i> Delete</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="bottom-section" id="mind-map-container" data-module-component="mind-map-viewer">
            <h2><i class="fas fa-project-diagram"></i> Neural Link Mind Map</h2>
            <div class="mind-map-controls" data-module-component="visual-connections">
                <button class="control-btn" data-module-component="visual-connections"><i class="fas fa-plus"></i></button>
                <button class="control-btn" data-module-component="visual-connections"><i class="fas fa-minus"></i></button>
                <button class="control-btn" data-module-component="visual-connections"><i class="fas fa-expand"></i></button>
            </div>
            <div class="mind-map" data-module-component="relationship-graph">
                <canvas id="mind-map-canvas" data-module-component="relationship-graph"></canvas>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="footer-content">
            <p>Drive-Manager Pro | <i class="far fa-copyright"></i> 2025 | Intelligent File Management</p>
            <div class="footer-links">
                <a href="#"><i class="fas fa-question-circle"></i> Help</a>
                <a href="#"><i class="fas fa-cog"></i> Settings</a>
                <a href="#"><i class="fas fa-sync-alt"></i> Check for Updates</a>
            </div>
        </div>
    </footer>
    
    <script src="app.js"></script>
</body>
</html>
"""

    def get_css_content(self):
        return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');

:root {
    /* Modern color palette - Tailwind-inspired */
    --primary-color: #6366F1;
    --primary-light: #818CF8;
    --primary-dark: #4F46E5;
    --files-color: #10B981;
    --tools-color: #8B5CF6;
    --cloud-color: #F59E0B;
    --mind-map-bg: #1F2937;
    --section-bg: #FFFFFF;
    --main-bg: #F1F5F9;
    --text-color: #334155;
    --light-text: #64748B;
    --border-color: #E2E8F0;
    --highlight-color: #3B82F6;
    --hover-color: #EFF6FF;
    --selected-color: #DBEAFE;
    --warning-color: #F59E0B;
    --error-color: #EF4444;
    --success-color: #10B981;
    --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --panel-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --gradient-blue: linear-gradient(135deg, #6366F1, #4F46E5);
    --gradient-purple: linear-gradient(135deg, #8B5CF6, #7C3AED);
    --gradient-green: linear-gradient(135deg, #10B981, #059669);
    --gradient-orange: linear-gradient(135deg, #F59E0B, #D97706);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Inter', 'Poppins', sans-serif;
}

body {
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--main-bg);
    font-weight: 400;
    background-image: 
        radial-gradient(circle at 5% 5%, rgba(99, 102, 241, 0.05) 0%, transparent 25%),
        radial-gradient(circle at 95% 95%, rgba(139, 92, 246, 0.05) 0%, transparent 25%);
}

header {
    background: var(--gradient-blue);
    color: white;
    padding: 2rem;
    text-align: center;
    box-shadow: var(--panel-shadow);
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
    pointer-events: none;
}

header h1 {
    margin-bottom: 0.5rem;
    font-weight: 700;
    letter-spacing: -0.5px;
}

header p {
    opacity: 0.9;
    font-weight: 300;
    max-width: 600px;
    margin: 0 auto;
}

.container {
    max-width: 100%;
    margin: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.top-section {
    display: flex;
    gap: 1.5rem;
    height: 75vh;
}

.panel {
    flex: 1;
    background-color: var(--section-bg);
    border-radius: 12px;
    box-shadow: var(--panel-shadow);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.panel:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.panel h2 {
    position: relative;
    color: white;
    padding: 1rem 1.5rem;
    font-size: 1.25rem;
    font-weight: 600;
    display: flex;
    align-items: center;
}

.panel h2::before {
    content: '';
    display: inline-block;
    width: 18px;
    height: 18px;
    margin-right: 10px;
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
}

#ai-panel h2 {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
}

#cloud-panel h2 {
    background: linear-gradient(135deg, var(--cloud-color), #DD6B20);
}

#tools-panel h2 {
    background: linear-gradient(135deg, var(--tools-color), #7C3AED);
}

.panel-content {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
}

.panel-content h3 {
    margin-top: 1.25rem;
    margin-bottom: 0.75rem;
    font-size: 1rem;
    color: var(--text-color);
    font-weight: 600;
    position: relative;
    padding-bottom: 0.5rem;
}

.panel-content h3::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 40px;
    height: 3px;
    background-color: var(--primary-light);
    border-radius: 3px;
}

.bottom-section {
    background-color: var(--mind-map-bg);
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.1) 0%, transparent 20%),
        radial-gradient(circle at 90% 80%, rgba(124, 58, 237, 0.1) 0%, transparent 20%);
    border-radius: 12px;
    height: 25vh;
    color: white;
    padding: 1.5rem;
    box-shadow: var(--panel-shadow);
    position: relative;
    overflow: hidden;
}

.bottom-section h2 {
    margin-bottom: 0.75rem;
    font-size: 1.25rem;
    font-weight: 600;
    display: flex;
    align-items: center;
}

.bottom-section h2::before {
    content: '';
    display: inline-block;
    width: 18px;
    height: 18px;
    margin-right: 10px;
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
}

.mind-map {
    width: 100%;
    height: calc(100% - 2.5rem);
    position: relative;
}

canvas#mind-map-canvas {
    width: 100%;
    height: 100%;
}

/* Element Styles */
button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
}

button:hover {
    background-color: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

button:active {
    transform: translateY(0);
}

.cloud-btn {
    margin-right: 0.75rem;
    margin-bottom: 0.75rem;
    padding: 0.75rem 1.25rem;
    border-radius: 10px;
    position: relative;
    overflow: hidden;
    z-index: 1;
}

.cloud-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(rgba(255,255,255,0.1), rgba(255,255,255,0));
    z-index: -1;
}

.cloud-btn.google {
    background: linear-gradient(135deg, #4285F4, #0F9D58);
}

.cloud-btn.dropbox {
    background: linear-gradient(135deg, #0061FF, #0043B8);
}

.cloud-btn.onedrive {
    background: linear-gradient(135deg, #0078D4, #00598C);
}

.path-nav {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
    background-color: white;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.path-nav span {
    margin-right: 0.5rem;
}

.path-nav button {
    padding: 0.3rem 0.6rem;
    margin-left: auto;
    border-radius: 6px;
}

#file-list-container {
    margin-bottom: 1rem;
    max-height: 300px;
    overflow-y: auto;
    border-radius: 10px;
    background-color: white;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.file-item {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.file-item:last-child {
    border-bottom: none;
}

.file-item:hover {
    background-color: var(--hover-color);
    transform: translateX(5px);
}

.file-item.folder {
    background-color: rgba(239, 246, 255, 0.5);
}

.file-icon {
    margin-right: 0.75rem;
    color: var(--files-color);
    font-size: 1.2rem;
}

.folder-icon {
    color: var(--primary-color);
    font-size: 1.2rem;
}

.file-operations {
    display: flex;
    gap: 0.75rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.tag {
    background-color: var(--tools-color);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    display: inline-flex;
    align-items: center;
}

.tag::before {
    content: '#';
    margin-right: 4px;
    opacity: 0.7;
}

.status {
    margin-top: 1rem;
    font-style: italic;
    color: var(--light-text);
    padding: 0.5rem 0;
    border-top: 1px dashed var(--border-color);
}

.recommendation-item {
    background-color: var(--hover-color);
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-radius: 10px;
    border-left: 4px solid var(--primary-color);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease;
}

.recommendation-item:hover {
    transform: translateX(5px);
}

.recommendation-action {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.3rem 0.8rem;
    background-color: var(--primary-color);
    color: white;
    font-size: 0.8rem;
    font-weight: 500;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.recommendation-action:hover {
    background-color: var(--primary-dark);
}

.cloud-file-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
    transition: all 0.2s ease;
}

.cloud-file-item:hover {
    background-color: var(--hover-color);
}

.cloud-file-item .status-icon {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 0.75rem;
    position: relative;
}

.status-synced {
    background-color: var(--success-color);
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.status-syncing {
    background-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    animation: pulse 1.5s infinite;
}

.status-pending {
    background-color: var(--warning-color);
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

.status-error {
    background-color: var(--error-color);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4);
    }
    70% {
        box-shadow: 0 0 0 6px rgba(99, 102, 241, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(99, 102, 241, 0);
    }
}

footer {
    text-align: center;
    padding: 1.5rem;
    color: var(--light-text);
    font-size: 0.9rem;
    background-color: var(--section-bg);
    border-top: 1px solid var(--border-color);
    margin-top: 1rem;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* Module Toggle Styles */
.module-disabled {
    opacity: 0.4;
    filter: grayscale(70%);
    pointer-events: none;
    position: relative;
}

.module-disabled::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(128, 128, 128, 0.2);
    border-radius: inherit;
    z-index: 1;
}

.module-toggle-panel {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    width: 320px;
    max-height: 70vh;
    overflow-y: auto;
    z-index: 1000;
    transition: all 0.3s ease;
    transform: translateX(100%);
}

.module-toggle-panel.active {
    transform: translateX(0);
}

.module-toggle-btn {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    transition: all 0.3s ease;
}

.module-toggle-btn:hover {
    transform: scale(1.1);
    background: var(--primary-dark);
}

.module-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-color);
}

.module-item:last-child {
    border-bottom: none;
}

.module-info {
    flex: 1;
}

.module-name {
    font-weight: 600;
    color: var(--text-color);
    margin-bottom: 0.25rem;
}

.module-desc {
    font-size: 0.8rem;
    color: var(--light-text);
}

.module-toggle {
    position: relative;
    width: 50px;
    height: 26px;
    background-color: #ccc;
    border-radius: 13px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.module-toggle.enabled {
    background-color: var(--primary-color);
}

.module-toggle::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 22px;
    height: 22px;
    background-color: white;
    border-radius: 50%;
    transition: transform 0.3s;
}

.module-toggle.enabled::before {
    transform: translateX(24px);
}

.module-toggle.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.dependency-warning {
    background-color: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 0.75rem;
    margin: 0.5rem 0;
    font-size: 0.8rem;
    color: #92400e;
}

.core-module {
    background-color: #f0f9ff;
    border-left: 4px solid var(--primary-color);
    padding-left: 0.75rem;
    border-radius: 0 8px 8px 0;
}

@media (max-width: 768px) {
    .top-section {
        flex-direction: column;
        height: auto;
    }
    
    .panel {
        height: 350px;
    }
    
    .module-toggle-panel {
        width: calc(100vw - 40px);
        right: 20px;
        left: 20px;
    }
}
"""

    def get_js_content(self):
        return """
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    fetchData();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize mind map
    initMindMap();
    
    // Initialize module manager
    initModuleManager();
});

function fetchData() {
    // Fetch files
    fetch('/api/files')
        .then(response => response.json())
        .then(data => {
            renderFiles(data);
        })
        .catch(error => console.error('Error fetching files:', error));
    
    // Fetch recommendations
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(data => {
            renderRecommendations(data);
        })
        .catch(error => console.error('Error fetching recommendations:', error));
    
    // Fetch cloud files
    fetch('/api/cloud')
        .then(response => response.json())
        .then(data => {
            renderCloudFiles(data);
        })
        .catch(error => console.error('Error fetching cloud files:', error));
    
    // Fetch mind map data (for initial state)
    fetch('/api/mindmap')
        .then(response => response.json())
        .then(data => {
            updateMindMap(data);
        })
        .catch(error => console.error('Error fetching mind map data:', error));
}

function setupEventListeners() {
    // Cloud provider buttons
    document.querySelectorAll('.cloud-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelector('.status').textContent = 'Connected to ' + this.textContent;
        });
    });
    
    // Path navigation
    document.querySelector('.path-nav button').addEventListener('click', function() {
        const currentPath = document.getElementById('current-path').textContent;
        const pathParts = currentPath.split('/');
        pathParts.pop(); // Remove last part
        
        if (pathParts.length > 1) {
            const newPath = pathParts.join('/');
            document.getElementById('current-path').textContent = newPath || '/';
        }
    });
}

function renderFiles(files) {
    const container = document.getElementById('file-list-container');
    container.innerHTML = '';
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item ${file.is_dir ? 'folder' : ''}`;
        
        const icon = document.createElement('span');
        icon.className = file.is_dir ? 'folder-icon' : 'file-icon';
        icon.innerHTML = file.is_dir ? '📁' : '📄';
        
        const name = document.createElement('span');
        name.textContent = file.name;
        
        fileItem.appendChild(icon);
        fileItem.appendChild(name);
        
        // Add click event to show file tags when clicked
        fileItem.addEventListener('click', function() {
            if (!file.is_dir) {
                renderTags(file.tags || []);
                highlightMindMapNode(file.name);
            } else {
                document.getElementById('current-path').textContent += '/' + file.name;
            }
        });
        
        container.appendChild(fileItem);
    });
}

function renderTags(tags) {
    const container = document.getElementById('tags-container');
    container.innerHTML = '';
    
    if (tags.length === 0) {
        const emptyMessage = document.createElement('p');
        emptyMessage.textContent = 'No tags available';
        emptyMessage.style.fontStyle = 'italic';
        emptyMessage.style.color = 'var(--light-text)';
        container.appendChild(emptyMessage);
        return;
    }
    
    tags.forEach(tag => {
        const tagElement = document.createElement('span');
        tagElement.className = 'tag';
        tagElement.textContent = tag;
        
        container.appendChild(tagElement);
    });
}

function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = '';
    
    if (recommendations.length === 0) {
        const emptyMessage = document.createElement('p');
        emptyMessage.textContent = 'No recommendations available';
        emptyMessage.style.fontStyle = 'italic';
        emptyMessage.style.color = 'var(--light-text)';
        container.appendChild(emptyMessage);
        return;
    }
    
    recommendations.forEach(rec => {
        const recItem = document.createElement('div');
        recItem.className = 'recommendation-item';
        
        const title = document.createElement('div');
        title.textContent = rec.name;
        title.style.fontWeight = 'bold';
        
        const details = document.createElement('div');
        details.textContent = rec.details;
        details.style.fontSize = '0.9rem';
        
        const action = document.createElement('span');
        action.className = 'recommendation-action';
        action.textContent = rec.action;
        
        recItem.appendChild(title);
        recItem.appendChild(details);
        recItem.appendChild(action);
        
        container.appendChild(recItem);
    });
}

function renderCloudFiles(files) {
    const container = document.getElementById('cloud-files-container');
    container.innerHTML = '';
    
    if (files.length === 0) {
        const emptyMessage = document.createElement('p');
        emptyMessage.textContent = 'No cloud files available';
        emptyMessage.style.fontStyle = 'italic';
        emptyMessage.style.color = 'var(--light-text)';
        container.appendChild(emptyMessage);
        return;
    }
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'cloud-file-item';
        
        const statusIcon = document.createElement('div');
        statusIcon.className = `status-icon status-${file.status.toLowerCase()}`;
        
        const icon = document.createElement('span');
        icon.innerHTML = file.is_folder ? '📁' : '📄';
        icon.style.marginRight = '0.5rem';
        
        const name = document.createElement('span');
        name.textContent = file.name;
        name.style.flex = 1;
        
        const size = document.createElement('span');
        size.textContent = file.size;
        size.style.marginLeft = '0.5rem';
        size.style.fontSize = '0.8rem';
        size.style.color = 'var(--light-text)';
        
        fileItem.appendChild(statusIcon);
        fileItem.appendChild(icon);
        fileItem.appendChild(name);
        fileItem.appendChild(size);
        
        container.appendChild(fileItem);
    });
}

function initMindMap() {
    const canvas = document.getElementById('mind-map-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas dimensions
    function resizeCanvas() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
    }
    
    // Call once to initialize
    resizeCanvas();
    
    // Listen for window resize
    window.addEventListener('resize', resizeCanvas);
    
    // Draw initial state
    drawMindMap(ctx, {nodes: [], edges: []});
}

function drawMindMap(ctx, data) {
    const { nodes, edges } = data;
    const width = ctx.canvas.width;
    const height = ctx.canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw connections first (so they're behind nodes)
    edges.forEach(edge => {
        const sourceNode = nodes.find(node => node.id === edge.source);
        const targetNode = nodes.find(node => node.id === edge.target);
        
        if (sourceNode && targetNode) {
            ctx.beginPath();
            ctx.moveTo(sourceNode.x * width, sourceNode.y * height);
            ctx.lineTo(targetNode.x * width, targetNode.y * height);
            ctx.strokeStyle = edge.color || '#666';
            ctx.lineWidth = edge.highlighted ? 2 : 1;
            ctx.globalAlpha = edge.highlighted ? 1 : 0.7;
            ctx.stroke();
            ctx.globalAlpha = 1;
        }
    });
    
    // Draw nodes
    nodes.forEach(node => {
        // Node circle
        ctx.beginPath();
        ctx.arc(node.x * width, node.y * height, node.size || 10, 0, Math.PI * 2);
        ctx.fillStyle = node.color || '#0078D7';
        ctx.fill();
        
        if (node.highlighted) {
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.stroke();
        }
        
        // Node label
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.label, node.x * width, (node.y * height) + 20);
    });
}

function updateMindMap(data) {
    const canvas = document.getElementById('mind-map-canvas');
    const ctx = canvas.getContext('2d');
    drawMindMap(ctx, data);
}

function highlightMindMapNode(nodeName) {
    fetch(`/api/mindmap?highlight=${nodeName}`)
        .then(response => response.json())
        .then(data => {
            updateMindMap(data);
        })
        .catch(error => console.error('Error highlighting node:', error));
}

// Module Manager Functions
function initModuleManager() {
    // Create module toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'module-toggle-btn';
    toggleBtn.innerHTML = '⚙️';
    toggleBtn.title = 'Module Settings';
    toggleBtn.onclick = toggleModulePanel;
    document.body.appendChild(toggleBtn);
    
    // Create module panel
    const panel = document.createElement('div');
    panel.className = 'module-toggle-panel';
    panel.id = 'module-panel';
    document.body.appendChild(panel);
    
    // Load initial module states
    loadModuleStates();
    
    // Apply initial UI states
    applyModuleStates();
}

function toggleModulePanel() {
    const panel = document.getElementById('module-panel');
    panel.classList.toggle('active');
    
    if (panel.classList.contains('active')) {
        loadModuleStates();
    }
}

function loadModuleStates() {
    fetch('/api/modules/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderModulePanel(data.config);
                applyModuleStates(data.config.ui_components);
            }
        })
        .catch(error => console.error('Error loading module states:', error));
}

function renderModulePanel(config) {
    const panel = document.getElementById('module-panel');
    
    let html = '<h3>Module Settings</h3>';
    html += '<div class="module-list">';
    
    config.modules.forEach(module => {
        const isCore = module.core;
        const isEnabled = module.enabled;
        const isAvailable = module.available;
        
        html += `<div class="module-item ${isCore ? 'core-module' : ''}">`;
        html += '<div class="module-info">';
        html += `<div class="module-name">${module.name} ${isCore ? '(Core)' : ''}</div>`;
        html += `<div class="module-desc">${module.description}</div>`;
        
        if (module.dependencies.length > 0) {
            html += `<div style="font-size: 0.7rem; color: #666; margin-top: 0.25rem;">`;
            html += `Requires: ${module.dependencies.map(dep => {
                const depModule = config.modules.find(m => m.id === dep);
                return depModule ? depModule.name : dep;
            }).join(', ')}`;
            html += '</div>';
        }
        
        html += '</div>';
        
        if (!isCore) {
            html += `<div class="module-toggle ${isEnabled ? 'enabled' : ''} ${!isAvailable ? 'disabled' : ''}" 
                          onclick="toggleModule('${module.id}', ${!isEnabled})" 
                          title="${!isAvailable ? 'Dependencies not satisfied' : ''}">
                     </div>`;
        } else {
            html += '<div style="font-size: 0.7rem; color: #666;">Always On</div>';
        }
        
        html += '</div>';
        
        if (!isAvailable && module.dependencies.length > 0) {
            html += '<div class="dependency-warning">';
            html += 'This module requires other modules to be enabled first.';
            html += '</div>';
        }
    });
    
    html += '</div>';
    html += '<div style="margin-top: 1rem; text-align: center;">';
    html += '<button onclick="resetModules()" style="background: #6b7280; margin-right: 0.5rem;">Reset to Defaults</button>';
    html += '<button onclick="toggleModulePanel()" style="background: #ef4444;">Close</button>';
    html += '</div>';
    
    panel.innerHTML = html;
}

function toggleModule(moduleId, enable) {
    fetch('/api/modules/toggle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            module_id: moduleId,
            enabled: enable
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload module states
            loadModuleStates();
            
            // Show notification
            showNotification(`${data.module_name} ${enable ? 'enabled' : 'disabled'}`, 'success');
            
            if (data.dependent_modules_disabled && data.dependent_modules_disabled.length > 0) {
                showNotification(`Also disabled dependent modules`, 'warning');
            }
        } else {
            showNotification(data.error || 'Failed to toggle module', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling module:', error);
        showNotification('Error toggling module', 'error');
    });
}

function resetModules() {
    if (confirm('Reset all modules to default settings?')) {
        fetch('/api/modules/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadModuleStates();
                showNotification('Modules reset to defaults', 'success');
            } else {
                showNotification('Failed to reset modules', 'error');
            }
        })
        .catch(error => {
            console.error('Error resetting modules:', error);
            showNotification('Error resetting modules', 'error');
        });
    }
}

function applyModuleStates(uiComponents) {
    if (!uiComponents) {
        // Load UI components if not provided
        fetch('/api/modules/ui-components')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    applyModuleStates(data.components);
                }
            })
            .catch(error => console.error('Error loading UI components:', error));
        return;
    }
    
    // Apply states to UI components
    Object.keys(uiComponents).forEach(componentId => {
        const component = uiComponents[componentId];
        const elements = document.querySelectorAll(`[data-module-component="${componentId}"]`);
        
        elements.forEach(element => {
            if (component.enabled) {
                element.classList.remove('module-disabled');
            } else {
                element.classList.add('module-disabled');
            }
        });
        
        // Apply to panels based on their content
        applyPanelStates(componentId, component.enabled);
    });
}

function applyPanelStates(componentId, enabled) {
    // Map component IDs to actual UI elements
    const componentMappings = {
        'ai-analysis-panel': ['.panel:nth-child(3)'], // AI Recommendations panel
        'smart-tags': ['.tags'],
        'file-recommendations': ['.panel:nth-child(3)'],
        'duplicate-scanner': ['.file-operations button[onclick*="scan"]'],
        'cloud-sync-panel': ['.panel:nth-child(2)'], // Cloud Storage panel
        'cloud-status': ['.cloud-file-item .status-icon'],
        'sync-settings': ['.cloud-btn'],
        'media-viewer': ['.file-item[data-type*="image"], .file-item[data-type*="video"]'],
        'thumbnail-grid': ['.file-item img'],
        'ai-generator': ['.file-operations button[onclick*="generate"]'],
        'apk-creator': ['.file-operations button[onclick*="apk"]'],
        'apk-analyzer': ['.file-operations button[onclick*="analyze"]'],
        'mind-map-viewer': ['.bottom-section'], // Mind map section
        'relationship-graph': ['canvas#mind-map-canvas'],
        'visual-connections': ['.bottom-section'],
        'search-bar': ['input[type="search"]'],
        'filter-panel': ['.file-operations select'],
        'advanced-search': ['.file-operations button[onclick*="search"]']
    };
    
    if (componentMappings[componentId]) {
        componentMappings[componentId].forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (enabled) {
                    element.classList.remove('module-disabled');
                } else {
                    element.classList.add('module-disabled');
                }
            });
        });
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#6366f1'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        z-index: 1001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
        font-size: 0.9rem;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}
"""

def initialize_database():
    """Initialize the database with sample data if it's empty"""
    # Check if we already have files in the database
    session = db_manager.get_session()
    if session:
        file_count = session.query(File).count()
        db_manager.close_session(session)
        
        if file_count > 0:
            return  # Database already has data
    
    # Sample files to add
    sample_files = [
        {"name": "Documents", "path": "/home/user/Documents", "is_dir": True, "type": "folder", "size": 0, 
         "modified": datetime.datetime(2024, 4, 15, 14, 32), "tags": []},
        {"name": "Downloads", "path": "/home/user/Downloads", "is_dir": True, "type": "folder", "size": 0, 
         "modified": datetime.datetime(2024, 4, 20, 10, 15), "tags": []},
        {"name": "Pictures", "path": "/home/user/Pictures", "is_dir": True, "type": "folder", "size": 0, 
         "modified": datetime.datetime(2024, 4, 18, 9, 45), "tags": []},
        {"name": "script.py", "path": "/home/user/script.py", "is_dir": False, "type": "code", "size": 4300, 
         "modified": datetime.datetime(2024, 4, 19, 16, 22), "tags": ["Python", "Code", "ProjectX"]},
        {"name": "report.docx", "path": "/home/user/report.docx", "is_dir": False, "type": "document", "size": 1800000, 
         "modified": datetime.datetime(2024, 4, 12, 11, 5), "tags": ["Document", "Report", "ProjectX"]},
        {"name": "presentation.pptx", "path": "/home/user/presentation.pptx", "is_dir": False, "type": "document", "size": 5700000, 
         "modified": datetime.datetime(2024, 4, 10, 14, 25), "tags": ["Presentation", "ProjectX"]},
        {"name": "image.jpg", "path": "/home/user/image.jpg", "is_dir": False, "type": "image", "size": 2400000, 
         "modified": datetime.datetime(2024, 4, 5, 8, 30), "tags": ["Image", "ProjectX"]},
        {"name": "data.csv", "path": "/home/user/data.csv", "is_dir": False, "type": "document", "size": 512000, 
         "modified": datetime.datetime(2024, 4, 17, 13, 40), "tags": ["Data", "ProjectX"]}
    ]
    
    # Create sample tags
    tags = {
        "Python": db_manager.add_tag("Python", "#4B8BBE"),
        "Code": db_manager.add_tag("Code", "#8B5CF6"),
        "Document": db_manager.add_tag("Document", "#10B981"),
        "Report": db_manager.add_tag("Report", "#3B82F6"),
        "Presentation": db_manager.add_tag("Presentation", "#F59E0B"),
        "Image": db_manager.add_tag("Image", "#EF4444"),
        "Data": db_manager.add_tag("Data", "#6366F1"),
        "ProjectX": db_manager.add_tag("ProjectX", "#EC4899")
    }
    
    # Add files to database
    for file_data in sample_files:
        # Create a file metadata object
        class FileMetadata:
            def __init__(self, data):
                self.path = data["path"]
                self.name = data["name"]
                self.is_dir = data["is_dir"]
                self.size = data["size"]
                self.extension = os.path.splitext(data["name"])[1] if "." in data["name"] else ""
                self.file_type = data["type"]
                self.modified = data["modified"]
                self.created = data["modified"]
                self.accessed = data["modified"]
                self.hash = ""
                self.tags = data["tags"]
        
        # Add file to database
        file_meta = FileMetadata(file_data)
        file_id = db_manager.add_file(file_meta)
        
        # Associate tags with file
        if file_id:
            for tag_name in file_data["tags"]:
                if tag_name in tags and tags[tag_name]:
                    db_manager.add_tag_to_file(file_id, tags[tag_name])
    
    # Add sample recommendations
    session = db_manager.get_session()
    if session:
        # Find the files for recommendations
        duplicate_file = session.query(File).filter_by(name="report-copy.docx").first()
        if not duplicate_file:
            duplicate_file = File(
                path="/home/user/Documents/report-copy.docx",
                name="report-copy.docx",
                size=1800000,
                extension=".docx",
                is_directory=False,
                file_type="document",
                created_time=datetime.datetime.now() - datetime.timedelta(days=30),
                modified_time=datetime.datetime.now() - datetime.timedelta(days=30),
                accessed_time=datetime.datetime.now() - datetime.timedelta(days=30)
            )
            session.add(duplicate_file)
            session.commit()
        
        old_file = session.query(File).filter_by(name="old-notes.txt").first()
        if not old_file:
            old_file = File(
                path="/home/user/Documents/old-notes.txt",
                name="old-notes.txt",
                size=24000,
                extension=".txt",
                is_directory=False,
                file_type="document",
                created_time=datetime.datetime.now() - datetime.timedelta(days=120),
                modified_time=datetime.datetime.now() - datetime.timedelta(days=120),
                accessed_time=datetime.datetime.now() - datetime.timedelta(days=120)
            )
            session.add(old_file)
            session.commit()
        
        vacation_pic = session.query(File).filter_by(name="vacation.jpg").first()
        if not vacation_pic:
            vacation_pic = File(
                path="/home/user/Downloads/vacation.jpg",
                name="vacation.jpg",
                size=3200000,
                extension=".jpg",
                is_directory=False,
                file_type="image",
                created_time=datetime.datetime.now() - datetime.timedelta(days=15),
                modified_time=datetime.datetime.now() - datetime.timedelta(days=15),
                accessed_time=datetime.datetime.now() - datetime.timedelta(days=15)
            )
            session.add(vacation_pic)
            session.commit()
        
        # Add recommendations
        if duplicate_file:
            orig_file = session.query(File).filter_by(name="report.docx").first()
            if orig_file:
                # Create recommendation directly with the session
                recommendation1 = Recommendation(
                    file_id=duplicate_file.id,
                    recommendation_type="duplicate",
                    action="delete",
                    details=f"Duplicate of {orig_file.name}",
                    priority="high"
                )
                session.add(recommendation1)
        
        if old_file:
            # Create recommendation directly with the session
            recommendation2 = Recommendation(
                file_id=old_file.id,
                recommendation_type="obsolete",
                action="archive",
                details="Not accessed since 2024-01-15",
                priority="medium"
            )
            session.add(recommendation2)
        
        if vacation_pic:
            pics_folder = session.query(File).filter_by(name="Pictures").first()
            if pics_folder:
                # Create recommendation directly with the session
                recommendation3 = Recommendation(
                    file_id=vacation_pic.id,
                    recommendation_type="organization",
                    action="move",
                    details=f"Move to Pictures folder",
                    priority="low"
                )
                session.add(recommendation3)
                
        # Make sure to commit all changes before closing
        session.commit()
        db_manager.close_session(session)

def get_files_from_db():
    """Get files from the database"""
    session = db_manager.get_session()
    if not session:
        return get_mock_files()
    
    try:
        files = []
        db_files = session.query(File).all()
        
        for db_file in db_files:
            # Skip system files starting with '.'
            if db_file.name.startswith('.'):
                continue
                
            # Format the modified time
            modified_str = db_file.modified_time.strftime("%Y-%m-%d %H:%M") if db_file.modified_time else ""
            
            # Format the size
            if db_file.is_directory:
                size_str = "Folder"
            else:
                size_bytes = db_file.size or 0
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes/(1024*1024):.1f} MB"
                else:
                    size_str = f"{size_bytes/(1024*1024*1024):.1f} GB"
            
            # Get tags
            tags = [tag.name for tag in db_file.tags]
            
            file_data = {
                "name": db_file.name,
                "path": db_file.path,
                "is_dir": db_file.is_directory,
                "type": db_file.file_type,
                "size": size_str,
                "modified": modified_str,
                "tags": tags
            }
            
            files.append(file_data)
        
        # Sort: folders first, then by name
        files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return files
    
    except Exception as e:
        logging.error(f"Error retrieving files from database: {e}")
        return get_mock_files()
    
    finally:
        db_manager.close_session(session)

def get_mock_files():
    """Generate mock file data as fallback"""
    return [
        {"name": "Documents", "path": "/home/user/Documents", "is_dir": True, "type": "folder", "size": "Folder", "modified": "2024-04-15 14:32"},
        {"name": "Downloads", "path": "/home/user/Downloads", "is_dir": True, "type": "folder", "size": "Folder", "modified": "2024-04-20 10:15"},
        {"name": "Pictures", "path": "/home/user/Pictures", "is_dir": True, "type": "folder", "size": "Folder", "modified": "2024-04-18 09:45"},
        {"name": "script.py", "path": "/home/user/script.py", "is_dir": False, "type": "code", "size": "4.2 KB", "modified": "2024-04-19 16:22", "tags": ["Python", "Code", "ProjectX"]},
        {"name": "report.docx", "path": "/home/user/report.docx", "is_dir": False, "type": "document", "size": "1.8 MB", "modified": "2024-04-12 11:05", "tags": ["Document", "Report", "ProjectX"]},
        {"name": "presentation.pptx", "path": "/home/user/presentation.pptx", "is_dir": False, "type": "document", "size": "5.7 MB", "modified": "2024-04-10 14:25", "tags": ["Presentation", "ProjectX"]},
        {"name": "image.jpg", "path": "/home/user/image.jpg", "is_dir": False, "type": "image", "size": "2.4 MB", "modified": "2024-04-05 08:30", "tags": ["Image", "ProjectX"]},
        {"name": "data.csv", "path": "/home/user/data.csv", "is_dir": False, "type": "document", "size": "512 KB", "modified": "2024-04-17 13:40", "tags": ["Data", "ProjectX"]}
    ]

def get_recommendations_from_db():
    """Get recommendations from the database"""
    recommendations = []
    session = db_manager.get_session()
    
    if not session:
        return get_mock_recommendations()
    
    try:
        db_recommendations = session.query(Recommendation).filter_by(is_applied=False).all()
        
        for rec in db_recommendations:
            # Get the associated file
            file = session.query(File).get(rec.file_id)
            if not file:
                continue
                
            recommendation = {
                "type": rec.recommendation_type,
                "action": rec.action.capitalize(),
                "path": file.path,
                "name": file.name,
                "details": rec.details,
                "priority": rec.priority
            }
            
            # Add reference path for duplicates
            if rec.recommendation_type == "duplicate" and "Duplicate of" in rec.details:
                # Extract original file name
                original_name = rec.details.replace("Duplicate of ", "")
                original_file = session.query(File).filter_by(name=original_name).first()
                if original_file:
                    recommendation["reference_path"] = original_file.path
            
            # Add target path for move recommendations
            if rec.recommendation_type == "organization" and rec.action == "move" and "Move to" in rec.details:
                # Extract folder name
                folder_name = rec.details.replace("Move to ", "").replace(" folder", "")
                folder = session.query(File).filter_by(name=folder_name, is_directory=True).first()
                if folder:
                    recommendation["target_path"] = folder.path
            
            recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logging.error(f"Error retrieving recommendations from database: {e}")
        return get_mock_recommendations()
    
    finally:
        db_manager.close_session(session)

def get_mock_recommendations():
    """Generate mock recommendation data for the demo as fallback"""
    return [
        {
            "type": "duplicate",
            "action": "Delete",
            "path": "/home/user/Documents/report-copy.docx",
            "name": "report-copy.docx",
            "details": "Duplicate of report.docx",
            "reference_path": "/home/user/Documents/report.docx",
            "priority": "high"
        },
        {
            "type": "obsolete",
            "action": "Archive",
            "path": "/home/user/Documents/old-notes.txt",
            "name": "old-notes.txt",
            "details": "Not accessed since 2024-01-15",
            "priority": "medium"
        },
        {
            "type": "organization",
            "action": "Move",
            "path": "/home/user/Downloads/vacation.jpg",
            "name": "vacation.jpg",
            "details": "Move to Pictures folder",
            "target_path": "/home/user/Pictures/",
            "priority": "low"
        }
    ]

def initialize_cloud_database():
    """Initialize cloud sync data in the database"""
    session = db_manager.get_session()
    if not session:
        return
    
    try:
        # Check if we already have cloud syncs
        sync_count = session.query(CloudSync).count()
        if sync_count > 0:
            db_manager.close_session(session)
            return
        
        # Add some cloud files - first, get reference to existing files
        presentation = session.query(File).filter_by(name="presentation.pptx").first()
        if presentation:
            presentation_sync = CloudSync(
                file_id=presentation.id,
                provider="Google Drive",
                cloud_path="/presentation.pptx",
                sync_status="Syncing",
                last_synced=datetime.datetime.now() - datetime.timedelta(minutes=5)
            )
            session.add(presentation_sync)
        
        # Add new cloud-only files
        project_plan = File(
            path="/home/user/Documents/project_plan.docx",
            name="project_plan.docx",
            size=2500000,
            extension=".docx",
            is_directory=False,
            file_type="document",
            created_time=datetime.datetime.now() - datetime.timedelta(days=10),
            modified_time=datetime.datetime.now() - datetime.timedelta(days=2),
            accessed_time=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        session.add(project_plan)
        session.flush()  # Get ID before creating the sync
        
        project_plan_sync = CloudSync(
            file_id=project_plan.id,
            provider="Google Drive",
            cloud_path="/Documents/project_plan.docx",
            sync_status="Synced",
            last_synced=datetime.datetime.now() - datetime.timedelta(hours=2)
        )
        session.add(project_plan_sync)
        
        meeting_notes = File(
            path="/home/user/Documents/meeting_notes.txt",
            name="meeting_notes.txt",
            size=24000,
            extension=".txt",
            is_directory=False,
            file_type="document",
            created_time=datetime.datetime.now() - datetime.timedelta(days=5),
            modified_time=datetime.datetime.now() - datetime.timedelta(days=1),
            accessed_time=datetime.datetime.now() - datetime.timedelta(hours=12)
        )
        session.add(meeting_notes)
        session.flush()
        
        meeting_notes_sync = CloudSync(
            file_id=meeting_notes.id,
            provider="Google Drive",
            cloud_path="/Documents/meeting_notes.txt",
            sync_status="Pending",
            last_synced=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        session.add(meeting_notes_sync)
        
        budget = File(
            path="/home/user/Documents/budget.xlsx",
            name="budget.xlsx",
            size=1800000,
            extension=".xlsx",
            is_directory=False,
            file_type="document",
            created_time=datetime.datetime.now() - datetime.timedelta(days=15),
            modified_time=datetime.datetime.now() - datetime.timedelta(days=3),
            accessed_time=datetime.datetime.now() - datetime.timedelta(days=2)
        )
        session.add(budget)
        session.flush()
        
        budget_sync = CloudSync(
            file_id=budget.id,
            provider="Google Drive",
            cloud_path="/Documents/budget.xlsx",
            sync_status="Error",
            last_synced=datetime.datetime.now() - datetime.timedelta(days=3)
        )
        session.add(budget_sync)
        
        # Create folder entry for Documents in cloud
        documents_folder = session.query(File).filter_by(name="Documents").first()
        if documents_folder:
            documents_sync = CloudSync(
                file_id=documents_folder.id,
                provider="Google Drive",
                cloud_path="/Documents",
                sync_status="Synced",
                last_synced=datetime.datetime.now() - datetime.timedelta(hours=1)
            )
            session.add(documents_sync)
        
        session.commit()
    
    except Exception as e:
        logging.error(f"Error initializing cloud database: {e}")
        session.rollback()
    
    finally:
        db_manager.close_session(session)

def get_cloud_files_from_db():
    """Get cloud files from the database"""
    session = db_manager.get_session()
    if not session:
        return get_mock_cloud_files()
    
    try:
        cloud_files = []
        db_syncs = session.query(CloudSync).all()
        
        for sync in db_syncs:
            file = session.query(File).get(sync.file_id)
            if not file:
                continue
            
            # Format the size
            if file.is_directory:
                size_str = "Folder"
            else:
                size_bytes = file.size or 0
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes/(1024*1024):.1f} MB"
                else:
                    size_str = f"{size_bytes/(1024*1024*1024):.1f} GB"
            
            cloud_file = {
                "name": file.name,
                "path": sync.cloud_path,
                "provider": sync.provider,
                "is_folder": file.is_directory,
                "size": size_str,
                "status": sync.sync_status.capitalize()
            }
            
            cloud_files.append(cloud_file)
        
        # Sort: folders first, then by name
        cloud_files.sort(key=lambda x: (not x["is_folder"], x["name"].lower()))
        return cloud_files
    
    except Exception as e:
        logging.error(f"Error retrieving cloud files from database: {e}")
        return get_mock_cloud_files()
    
    finally:
        db_manager.close_session(session)

def get_mock_cloud_files():
    """Generate mock cloud storage files as fallback"""
    return [
        {"name": "Documents", "path": "/Documents", "provider": "Google Drive", "is_folder": True, "size": "Folder", "status": "Synced"},
        {"name": "project_plan.docx", "path": "/Documents/project_plan.docx", "provider": "Google Drive", "is_folder": False, "size": "2.5 MB", "status": "Synced"},
        {"name": "meeting_notes.txt", "path": "/Documents/meeting_notes.txt", "provider": "Google Drive", "is_folder": False, "size": "24 KB", "status": "Pending"},
        {"name": "budget.xlsx", "path": "/Documents/budget.xlsx", "provider": "Google Drive", "is_folder": False, "size": "1.8 MB", "status": "Error"},
        {"name": "presentation.pptx", "path": "/presentation.pptx", "provider": "Google Drive", "is_folder": False, "size": "4.6 MB", "status": "Syncing"}
    ]

def get_mock_mindmap_data():
    """Generate mock mind map data for the demo"""
    # This data represents a network graph with files, apps, and tags
    nodes = [
        {"id": "script.py", "label": "script.py", "x": 0.2, "y": 0.3, "size": 15, "color": "#2ECC71", "type": "file"},
        {"id": "document.docx", "label": "document.docx", "x": 0.3, "y": 0.1, "size": 15, "color": "#2ECC71", "type": "file"},
        {"id": "image.jpg", "label": "image.jpg", "x": 0.1, "y": 0.4, "size": 15, "color": "#2ECC71", "type": "file"},
        {"id": "presentation.pptx", "label": "presentation.pptx", "x": 0.5, "y": 0.3, "size": 15, "color": "#2ECC71", "type": "file"},
        {"id": "data.csv", "label": "data.csv", "x": 0.4, "y": 0.0, "size": 15, "color": "#2ECC71", "type": "file"},
        
        {"id": "VSCode", "label": "VSCode", "x": 0.6, "y": 0.5, "size": 20, "color": "#0078D7", "type": "app"},
        {"id": "Word", "label": "Word", "x": 0.7, "y": 0.3, "size": 20, "color": "#0078D7", "type": "app"},
        {"id": "Photoshop", "label": "Photoshop", "x": 0.3, "y": 0.7, "size": 20, "color": "#0078D7", "type": "app"},
        {"id": "PowerPoint", "label": "PowerPoint", "x": 0.8, "y": 0.5, "size": 20, "color": "#0078D7", "type": "app"},
        {"id": "Excel", "label": "Excel", "x": 0.8, "y": 0.2, "size": 20, "color": "#0078D7", "type": "app"},
        
        {"id": "Python", "label": "Python", "x": 0.4, "y": 0.7, "size": 10, "color": "#9B59B6", "type": "tag"},
        {"id": "Document", "label": "Document", "x": 0.5, "y": 0.6, "size": 10, "color": "#9B59B6", "type": "tag"},
        {"id": "Image", "label": "Image", "x": 0.5, "y": 0.5, "size": 10, "color": "#9B59B6", "type": "tag"},
        {"id": "Presentation", "label": "Presentation", "x": 0.9, "y": 0.2, "size": 10, "color": "#9B59B6", "type": "tag"},
        {"id": "Data", "label": "Data", "x": 0.7, "y": 0.0, "size": 10, "color": "#9B59B6", "type": "tag"},
        {"id": "ProjectX", "label": "ProjectX", "x": 0.0, "y": 0.0, "size": 10, "color": "#9B59B6", "type": "tag"}
    ]
    
    edges = [
        {"source": "script.py", "target": "VSCode", "color": "#0078D7", "type": "dependency"},
        {"source": "document.docx", "target": "Word", "color": "#0078D7", "type": "dependency"},
        {"source": "image.jpg", "target": "Photoshop", "color": "#0078D7", "type": "dependency"},
        {"source": "presentation.pptx", "target": "PowerPoint", "color": "#0078D7", "type": "dependency"},
        {"source": "data.csv", "target": "Excel", "color": "#0078D7", "type": "dependency"},
        
        {"source": "script.py", "target": "Python", "color": "#9B59B6", "type": "tag"},
        {"source": "document.docx", "target": "Document", "color": "#9B59B6", "type": "tag"},
        {"source": "image.jpg", "target": "Image", "color": "#9B59B6", "type": "tag"},
        {"source": "presentation.pptx", "target": "Presentation", "color": "#9B59B6", "type": "tag"},
        {"source": "data.csv", "target": "Data", "color": "#9B59B6", "type": "tag"},
        
        {"source": "script.py", "target": "ProjectX", "color": "#E67E22", "type": "project"},
        {"source": "document.docx", "target": "ProjectX", "color": "#E67E22", "type": "project"},
        {"source": "image.jpg", "target": "ProjectX", "color": "#E67E22", "type": "project"},
        {"source": "presentation.pptx", "target": "ProjectX", "color": "#E67E22", "type": "project"},
        {"source": "data.csv", "target": "ProjectX", "color": "#E67E22", "type": "project"}
    ]
    
    # Check if we need to highlight a node
    return {"nodes": nodes, "edges": edges}

def initialize_app_tables():
    """Initialize the database tables for the app generator"""
    # Create the app generator tables in the database
    try:
        from app_generator import Base, AppTemplate, GeneratedApp
        from sqlalchemy import create_engine
        
        # Connect to database
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            engine = create_engine(db_url)
            
            # Create app generator tables
            Base.metadata.create_all(engine)
            
            # Initialize app templates
            app_generator.initialize_templates()
            
            print("App generator tables initialized successfully")
        else:
            print("DATABASE_URL not set, skipping app generator table initialization")
    except Exception as e:
        print(f"Error initializing app generator tables: {e}")
        # Continue anyway - we'll fall back to mock data if needed

def run_server():
    """Run the HTTP server"""
    # Initialize the database with sample data
    initialize_database()
    initialize_cloud_database()
    initialize_app_tables()
    
    # Start the server
    server = ThreadedHTTPServer(('0.0.0.0', 5000), DemoHandler)
    print(f"Starting Drive-Manager Pro Demo server on port 5000...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()