"""
Drive-Manager Pro - Cross-platform file management application
with neural link-based interface and AI-driven organization.

Main application entry point.
"""

import os
import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QSplitter, QLabel, QStatusBar,
                           QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QSize, QTimer, QRect
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPalette

# Import modules
import config
import platform_utils
import file_system
import mind_map
import ai_analysis
import cloud_storage
import tools_panel
from assets import icons

class MainWindow(QMainWindow):
    """Main application window for Drive-Manager Pro"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.file_system_manager = file_system.FileSystemManager()
        self.ai_manager = ai_analysis.AIAnalysisManager()
        self.cloud_manager = cloud_storage.CloudStorageManager()
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load initial data
        self.load_initial_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Window properties
        self.setWindowTitle(f"{config.APP_NAME} {config.APP_VERSION}")
        self.setMinimumSize(1000, 700)
        
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create main splitter to divide top and bottom sections
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section (75% of height) - Contains three panels
        self.top_section = QWidget()
        self.top_layout = QHBoxLayout(self.top_section)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(10)
        
        # Create the three panel widgets
        self.create_ai_panel()
        self.create_cloud_panel()
        self.create_tools_panel()
        
        # Add three panels to top section
        self.top_layout.addWidget(self.ai_widget)
        self.top_layout.addWidget(self.cloud_widget)
        self.top_layout.addWidget(self.tools_widget)
        
        # Bottom section (25% of height) - Mind map
        self.create_mind_map()
        
        # Add sections to the main splitter
        self.main_splitter.addWidget(self.top_section)
        self.main_splitter.addWidget(self.mind_map_widget)
        
        # Set initial sizes (75% top, 25% bottom)
        self.main_splitter.setSizes([75, 25])
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.main_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Apply styles
        self.apply_styles()
    
    def create_ai_panel(self):
        """Create AI Analysis panel"""
        self.ai_widget = QWidget()
        self.ai_widget.setObjectName("aiAnalysisWidget")
        self.ai_layout = QVBoxLayout(self.ai_widget)
        
        # Header
        self.ai_header = QLabel("AI Analysis")
        self.ai_header.setProperty("class", "section-header")
        self.ai_layout.addWidget(self.ai_header)
        
        # Tags section
        self.tags_header = QLabel("File Tags")
        self.tags_header.setStyleSheet("font-weight: bold;")
        self.ai_layout.addWidget(self.tags_header)
        
        self.tags_container = QWidget()
        self.tags_container_layout = QVBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout = QHBoxLayout()
        self.tags_container_layout.addLayout(self.tags_layout)
        self.ai_layout.addWidget(self.tags_container)
        
        # Show placeholder tags
        self.update_tags_display([])
        
        # Links section
        self.links_header = QLabel("Neural Links")
        self.links_header.setStyleSheet("font-weight: bold;")
        self.ai_layout.addWidget(self.links_header)
        
        self.links_container = QWidget()
        self.links_container_layout = QVBoxLayout(self.links_container)
        self.links_container_layout.setContentsMargins(0, 0, 0, 0)
        self.ai_layout.addWidget(self.links_container)
        
        # Recommendations section
        self.recommendations_header = QLabel("Recommendations")
        self.recommendations_header.setStyleSheet("font-weight: bold;")
        self.ai_layout.addWidget(self.recommendations_header)
        
        self.recommendations_container = QWidget()
        self.recommendations_container_layout = QVBoxLayout(self.recommendations_container)
        self.recommendations_container_layout.setContentsMargins(0, 0, 0, 0)
        self.ai_layout.addWidget(self.recommendations_container)
        
        # Stretch to fill remaining space
        self.ai_layout.addStretch()
    
    def create_cloud_panel(self):
        """Create Cloud Storage panel"""
        self.cloud_widget = QWidget()
        self.cloud_widget.setObjectName("cloudStorageWidget")
        self.cloud_layout = QVBoxLayout(self.cloud_widget)
        
        # Header
        self.cloud_header = QLabel("Cloud Storage")
        self.cloud_header.setProperty("class", "section-header")
        self.cloud_layout.addWidget(self.cloud_header)
        
        # Cloud providers section
        self.providers_header = QLabel("Connected Services")
        self.providers_header.setStyleSheet("font-weight: bold;")
        self.cloud_layout.addWidget(self.providers_header)
        
        self.providers_container = QWidget()
        self.providers_container_layout = QHBoxLayout(self.providers_container)
        self.providers_container_layout.setContentsMargins(0, 0, 0, 0)
        self.cloud_layout.addWidget(self.providers_container)
        
        # Add provider buttons
        self.google_drive_btn = self.create_cloud_provider_button(
            "Google Drive", icons.GOOGLE_DRIVE_ICON, 
            lambda: self.connect_cloud_provider(cloud_storage.CloudProvider.GOOGLE_DRIVE.value)
        )
        self.dropbox_btn = self.create_cloud_provider_button(
            "Dropbox", icons.DROPBOX_ICON,
            lambda: self.connect_cloud_provider(cloud_storage.CloudProvider.DROPBOX.value)
        )
        self.onedrive_btn = self.create_cloud_provider_button(
            "OneDrive", icons.ONEDRIVE_ICON,
            lambda: self.connect_cloud_provider(cloud_storage.CloudProvider.ONEDRIVE.value)
        )
        
        self.providers_container_layout.addWidget(self.google_drive_btn)
        self.providers_container_layout.addWidget(self.dropbox_btn)
        self.providers_container_layout.addWidget(self.onedrive_btn)
        self.providers_container_layout.addStretch()
        
        # Cloud files section
        self.cloud_files_header = QLabel("Cloud Files")
        self.cloud_files_header.setStyleSheet("font-weight: bold;")
        self.cloud_layout.addWidget(self.cloud_files_header)
        
        self.cloud_files_container = QWidget()
        self.cloud_files_container_layout = QVBoxLayout(self.cloud_files_container)
        self.cloud_files_container_layout.setContentsMargins(0, 0, 0, 0)
        self.cloud_layout.addWidget(self.cloud_files_container)
        
        # Status section
        self.cloud_status = QLabel("Not connected to any cloud service")
        self.cloud_status.setStyleSheet("font-style: italic; color: #666666;")
        self.cloud_layout.addWidget(self.cloud_status)
        
        # Stretch to fill remaining space
        self.cloud_layout.addStretch()
    
    def create_tools_panel(self):
        """Create Tools & Functionalities panel"""
        self.tools_widget = tools_panel.ToolsWidget()
        self.tools_widget.setObjectName("toolsWidget")
    
    def create_mind_map(self):
        """Create Mind Map visualization"""
        self.mind_map_widget = mind_map.CustomMindMapWidget()
        self.mind_map_widget.setObjectName("mindMapWidget")
    
    def create_cloud_provider_button(self, name, icon_path, click_handler):
        """Create a cloud provider button"""
        button = QPushButton(name)
        button.setProperty("class", "cloud")
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(24, 24))
        button.clicked.connect(click_handler)
        button.setMinimumWidth(120)
        return button
    
    def apply_styles(self):
        """Apply styles to the application"""
        # Set background color
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(config.COLORS['main_bg']))
        self.setPalette(palette)
        
        # Set stylesheet from file
        try:
            with open("assets/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            
            # Fallback styles
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{
                    background-color: {config.COLORS['main_bg']};
                }}
                
                QWidget#mindMapWidget {{
                    background-color: {config.COLORS['mind_map_bg']};
                }}
                
                QWidget#aiAnalysisWidget, QWidget#cloudStorageWidget, QWidget#toolsWidget {{
                    background-color: {config.COLORS['section_bg']};
                    border: 1px solid {config.COLORS['border']};
                    border-radius: 4px;
                }}
                
                QPushButton {{
                    background-color: {config.COLORS['primary']};
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }}
                
                QPushButton:hover {{
                    background-color: {config.COLORS['highlight']};
                }}
                
                QPushButton.cloud {{
                    background-color: {config.COLORS['cloud']};
                }}
                
                QPushButton.cloud:hover {{
                    background-color: #D35400;
                }}
                
                QLabel.section-header {{
                    font-size: 12pt;
                    font-weight: bold;
                    padding: 5px;
                    border-bottom: 1px solid {config.COLORS['border']};
                }}
            """)
    
    def connect_signals(self):
        """Connect signals between components"""
        # File system signals
        self.file_system_manager.file_list_updated.connect(self.update_file_list)
        self.file_system_manager.file_operation_completed.connect(self.handle_file_operation_result)
        
        # Tools panel signals
        self.tools_widget.file_selected.connect(self.handle_file_selected)
        self.tools_widget.directory_changed.connect(self.handle_directory_changed)
        self.tools_widget.operation_requested.connect(self.handle_file_operation)
        self.tools_widget.tag_modified.connect(self.handle_tag_modification)
        
        # Mind map signals
        self.mind_map_widget.node_selected.connect(self.handle_mind_map_node_selected)
        
        # AI manager signals
        self.ai_manager.analysis_complete.connect(self.handle_file_analysis)
        self.ai_manager.recommendation_available.connect(self.handle_recommendations)
        
        # Cloud manager signals
        self.cloud_manager.status_changed.connect(self.handle_cloud_status)
        self.cloud_manager.files_listed.connect(self.handle_cloud_files_listed)
        self.cloud_manager.error_occurred.connect(self.handle_cloud_error)
    
    def load_initial_data(self):
        """Load initial data on startup"""
        # Get home directory and list files
        home_dir = platform_utils.get_home_directory()
        self.file_system_manager.navigate_to(home_dir)
        self.tools_widget.set_current_directory(home_dir)
        
        # Generate mock AI recommendations for demo
        self.ai_manager.generate_mock_recommendations()
        
        # Generate mock cloud data for demo
        self.cloud_manager.generate_mock_data()
        
        # Update status
        self.status_bar.showMessage(f"Loaded {home_dir}")
    
    def update_file_list(self, files):
        """Update file list in tools panel"""
        self.tools_widget.update_file_list(files)
        
        # Update mind map with these files
        self.mind_map_widget.update_with_files(files)
        
        # Analyze files with AI manager
        QTimer.singleShot(500, lambda: self.ai_manager.analyze_directory(files))
    
    def handle_file_selected(self, file_path):
        """Handle file selection from tools panel"""
        # Find file metadata in current directory
        for file_meta in self.file_system_manager.get_current_directory_contents():
            if file_meta.path == file_path:
                # Update tag editor with selected file
                self.tools_widget.set_current_file(file_meta)
                
                # Update AI panel
                self.update_tags_display(file_meta.tags)
                
                # Highlight in mind map
                self.mind_map_widget.highlight_node(file_meta.name)
                
                # Show status
                self.status_bar.showMessage(f"Selected: {file_meta.name}")
                return
                
        # If not found in current directory, it may be from search results
        # We would need to load this file's metadata
        self.status_bar.showMessage(f"Selected file: {os.path.basename(file_path)}")
    
    def handle_directory_changed(self, path):
        """Handle directory navigation"""
        self.file_system_manager.navigate_to(path)
        self.status_bar.showMessage(f"Navigated to: {path}")
    
    def handle_file_operation(self, operation, source, target=""):
        """Handle file operations"""
        if operation == "delete":
            self.file_system_manager.delete_item(source)
        elif operation == "copy":
            # Show file dialog to select destination
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            
            if dialog.exec():
                selected_dirs = dialog.selectedFiles()
                if selected_dirs:
                    dest_dir = selected_dirs[0]
                    dest_path = os.path.join(dest_dir, os.path.basename(source))
                    self.file_system_manager.copy_item(source, dest_path)
        elif operation == "move":
            # Show file dialog to select destination
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            
            if dialog.exec():
                selected_dirs = dialog.selectedFiles()
                if selected_dirs:
                    dest_dir = selected_dirs[0]
                    dest_path = os.path.join(dest_dir, os.path.basename(source))
                    self.file_system_manager.move_item(source, dest_path)
        elif operation == "rename":
            self.file_system_manager.rename_item(source, os.path.basename(target))
        elif operation == "new_folder":
            self.file_system_manager.create_directory(target)
    
    def handle_file_operation_result(self, success, message):
        """Handle result of file operations"""
        if success:
            self.status_bar.showMessage(message)
        else:
            QMessageBox.warning(self, "Operation Failed", message)
            self.status_bar.showMessage("Operation failed")
    
    def handle_mind_map_node_selected(self, node_id, node_type):
        """Handle selection of a node in mind map"""
        self.status_bar.showMessage(f"Selected {node_type}: {node_id}")
        
        if node_type == "file":
            # Find the file in current directory
            for file_meta in self.file_system_manager.get_current_directory_contents():
                if file_meta.name == node_id:
                    # Update tag editor with selected file
                    self.tools_widget.set_current_file(file_meta)
                    
                    # Update AI panel
                    self.update_tags_display(file_meta.tags)
                    return
        elif node_type == "app":
            # Show app-related files
            self.status_bar.showMessage(f"Showing files related to {node_id}")
        elif node_type == "tag":
            # Show files with this tag
            self.status_bar.showMessage(f"Showing files with tag: {node_id}")
    
    def update_tags_display(self, tags):
        """Update tags display in AI panel"""
        # Clear existing tags
        self.clear_layout(self.tags_layout)
        
        if not tags:
            # Show placeholder
            no_tags = QLabel("No tags assigned")
            no_tags.setStyleSheet("font-style: italic; color: #666666;")
            self.tags_layout.addWidget(no_tags)
            return
            
        # Add tag buttons
        for tag in tags:
            tag_btn = QPushButton(tag)
            tag_btn.setProperty("class", "tag")
            tag_btn.setMaximumHeight(24)
            self.tags_layout.addWidget(tag_btn)
            
        # Add stretch at the end
        self.tags_layout.addStretch()
    
    def handle_file_analysis(self, analysis_data):
        """Handle file analysis results"""
        # In a real implementation, this would update the AI panel
        # with analysis results for the current file
        pass
    
    def handle_recommendations(self, recommendations_data):
        """Handle AI recommendations"""
        # Clear existing recommendations
        self.clear_layout(self.recommendations_container_layout)
        
        # Get recommendations list
        recommendations = recommendations_data.get('recommendations', [])
        
        if not recommendations:
            # Show placeholder
            no_recs = QLabel("No recommendations available")
            no_recs.setStyleSheet("font-style: italic; color: #666666;")
            self.recommendations_container_layout.addWidget(no_recs)
            return
        
        # Add recommendation items (limited to top 3 for UI space)
        for i, rec in enumerate(recommendations[:3]):
            rec_widget = QWidget()
            rec_layout = QHBoxLayout(rec_widget)
            rec_layout.setContentsMargins(0, 3, 0, 3)
            
            # Icon based on recommendation type
            icon_label = QLabel()
            if rec['type'] == 'duplicate':
                icon_label.setPixmap(QIcon(icons.DUPLICATE_ICON).pixmap(16, 16))
            elif rec['type'] == 'obsolete':
                icon_label.setPixmap(QIcon(icons.OBSOLETE_ICON).pixmap(16, 16))
            elif rec['type'] == 'organization':
                icon_label.setPixmap(QIcon(icons.ORGANIZE_ICON).pixmap(16, 16))
            else:
                icon_label.setPixmap(QIcon(icons.RECOMMENDATION_ICON).pixmap(16, 16))
                
            rec_layout.addWidget(icon_label)
            
            # Recommendation text
            action_text = rec['action'].capitalize()
            rec_text = QLabel(f"{action_text} {rec['name']}: {rec['details']}")
            rec_layout.addWidget(rec_text)
            
            # Action button
            action_btn = QPushButton("Apply")
            action_btn.setProperty("class", "primary")
            action_btn.setMaximumWidth(60)
            action_btn.clicked.connect(lambda _, r=rec: self.apply_recommendation(r))
            rec_layout.addWidget(action_btn)
            
            self.recommendations_container_layout.addWidget(rec_widget)
        
        # If there are more recommendations than shown
        if len(recommendations) > 3:
            more_label = QLabel(f"+ {len(recommendations) - 3} more recommendations")
            more_label.setStyleSheet("font-style: italic; color: #666666;")
            self.recommendations_container_layout.addWidget(more_label)
    
    def apply_recommendation(self, recommendation):
        """Apply an AI recommendation"""
        rec_type = recommendation['type']
        action = recommendation['action']
        path = recommendation['path']
        
        if rec_type == 'duplicate' and action == 'delete':
            # Delete duplicate file
            self.file_system_manager.delete_item(path)
        elif rec_type == 'obsolete' and action == 'archive':
            # Archive obsolete file (implemented as move to archive folder)
            archive_dir = os.path.join(platform_utils.get_home_directory(), "Archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            dest_path = os.path.join(archive_dir, os.path.basename(path))
            self.file_system_manager.move_item(path, dest_path)
        elif rec_type == 'organization' and action == 'move':
            # Move file to suggested location
            target_path = recommendation.get('target_path', '')
            if target_path:
                dest_path = os.path.join(target_path, os.path.basename(path))
                self.file_system_manager.move_item(path, dest_path)
        
        # Show status message
        self.status_bar.showMessage(f"Applied recommendation: {action} {os.path.basename(path)}")
    
    def connect_cloud_provider(self, provider_name):
        """Connect to a cloud storage provider"""
        # In a real implementation, this would authenticate with the provider
        result = self.cloud_manager.connect_provider(provider_name)
        
        if result:
            # List root files
            self.cloud_manager.list_files("/", provider_name)
            
            # Update provider button to show connected state
            if provider_name == cloud_storage.CloudProvider.GOOGLE_DRIVE.value:
                self.google_drive_btn.setStyleSheet("background-color: #27AE60;")
            elif provider_name == cloud_storage.CloudProvider.DROPBOX.value:
                self.dropbox_btn.setStyleSheet("background-color: #27AE60;")
            elif provider_name == cloud_storage.CloudProvider.ONEDRIVE.value:
                self.onedrive_btn.setStyleSheet("background-color: #27AE60;")
    
    def handle_cloud_status(self, message):
        """Handle cloud status updates"""
        self.cloud_status.setText(message)
    
    def handle_cloud_files_listed(self, files):
        """Handle cloud files listing"""
        # Clear existing files
        self.clear_layout(self.cloud_files_container_layout)
        
        if not files:
            # Show placeholder
            no_files = QLabel("No cloud files available")
            no_files.setStyleSheet("font-style: italic; color: #666666;")
            self.cloud_files_container_layout.addWidget(no_files)
            return
        
        # Add file items (limited to top 5 for UI space)
        for i, file in enumerate(files[:5]):
            file_widget = QWidget()
            file_layout = QHBoxLayout(file_widget)
            file_layout.setContentsMargins(0, 3, 0, 3)
            
            # Icon based on file type
            icon_label = QLabel()
            if file.is_folder:
                icon_label.setPixmap(QIcon(icons.FOLDER_ICON).pixmap(16, 16))
            else:
                icon_label.setPixmap(QIcon(icons.FILE_ICON).pixmap(16, 16))
                
            file_layout.addWidget(icon_label)
            
            # File name and info
            file_info = QLabel(f"{file.name} ({file.get_formatted_size()})")
            file_layout.addWidget(file_info)
            
            # Sync status indicator
            status_label = QLabel()
            status_label.setFixedSize(12, 12)
            status_color = file.get_sync_status_color()
            status_label.setStyleSheet(f"background-color: {status_color}; border-radius: 6px;")
            file_layout.addWidget(status_label)
            
            self.cloud_files_container_layout.addWidget(file_widget)
        
        # If there are more files than shown
        if len(files) > 5:
            more_label = QLabel(f"+ {len(files) - 5} more files")
            more_label.setStyleSheet("font-style: italic; color: #666666;")
            self.cloud_files_container_layout.addWidget(more_label)
    
    def handle_cloud_error(self, error_message):
        """Handle cloud error"""
        QMessageBox.warning(self, "Cloud Error", error_message)
        self.status_bar.showMessage(f"Cloud error: {error_message}")
    
    def handle_tag_modification(self, file_path, tags):
        """Handle tag modifications"""
        # Update AI panel if this is the currently selected file
        for file_meta in self.file_system_manager.get_current_directory_contents():
            if file_meta.path == file_path:
                self.update_tags_display(file_meta.tags)
                break
    
    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

def main():
    """Main application entry point"""
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    
    # Set application-wide properties
    platform_style = platform_utils.get_platform_style()
    app.setStyle(platform_style['style'])
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # For Replit: Create a simple HTTP server to indicate the app is running
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Drive-Manager Pro is running in Qt mode</h1>")
            self.wfile.write(b"<p>This is a desktop application running with PyQt6. The actual application UI is not accessible via web browser.</p>")
            self.wfile.write(b"</body></html>")
    
    def run_server():
        server = HTTPServer(('0.0.0.0', 5000), SimpleHandler)
        server.serve_forever()
    
    # Start the server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
