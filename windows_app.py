"""
Drive-Manager Pro Desktop App (Windows Version)
This module provides a desktop application optimized for Windows with
features for importing APK files and handling various file operations.
"""

import sys
import os
import threading
import time
import hashlib
import zipfile
import tempfile
import platform
import requests
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTabWidget, QTableWidget, 
    QTableWidgetItem, QProgressBar, QMessageBox, QListWidget, 
    QListWidgetItem, QComboBox, QLineEdit, QGroupBox, QFormLayout,
    QTextEdit, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont

from file_system import FileSystemManager, FileMetadata, FileType

class DuplicateScanThread(QThread):
    """Thread for scanning duplicate files without blocking the UI"""
    progress_update = pyqtSignal(int)
    scan_completed = pyqtSignal(list, dict)
    
    def __init__(self, file_system_manager, directory_path, recursive=True):
        super().__init__()
        self.file_system_manager = file_system_manager
        self.directory_path = directory_path
        self.recursive = recursive
        
    def run(self):
        # Connect signals from file system manager to emit our own signals
        def on_progress(progress):
            self.progress_update.emit(progress)
            
        def on_completed(duplicate_groups, stats):
            self.scan_completed.emit(duplicate_groups, stats)
        
        # Connect signals
        self.file_system_manager.duplicate_scan_progress.connect(on_progress)
        self.file_system_manager.duplicate_scan_completed.connect(on_completed)
        
        # Start the scan
        self.file_system_manager.find_duplicates(self.directory_path, self.recursive)


class APKImportThread(QThread):
    """Thread for importing APK files"""
    progress_update = pyqtSignal(int, str)
    import_completed = pyqtSignal(bool, str, str)
    
    def __init__(self, app_name=None, apk_path=None, save_dir=None):
        super().__init__()
        self.app_name = app_name
        self.apk_path = apk_path
        self.save_dir = save_dir or os.path.join(os.path.expanduser("~"), "Downloads", "ApkImports")
        
    def run(self):
        os.makedirs(self.save_dir, exist_ok=True)
        
        try:
            # Case 1: Import from Google Play Store
            if self.app_name and not self.apk_path:
                self.progress_update.emit(10, f"Looking up {self.app_name} on Google Play...")
                
                # In a real implementation, we would use a Google Play API library
                # For demo purposes, we'll simulate the download process
                
                self.progress_update.emit(30, f"Found {self.app_name}, downloading...")
                time.sleep(2)  # Simulate network delay
                
                self.progress_update.emit(60, f"Downloading APK file...")
                time.sleep(2)  # Simulate download time
                
                # Create a placeholder APK file
                sanitized_name = ''.join(c for c in self.app_name if c.isalnum() or c in (' ', '_', '-')).strip()
                output_path = os.path.join(self.save_dir, f"{sanitized_name}.apk")
                
                with open(output_path, 'w') as f:
                    f.write(f"Mock APK for {self.app_name}")
                    
                self.progress_update.emit(100, f"Import completed: {output_path}")
                self.import_completed.emit(True, f"Successfully imported {self.app_name}", output_path)
            
            # Case 2: Import from local file
            elif self.apk_path:
                filename = os.path.basename(self.apk_path)
                self.progress_update.emit(20, f"Importing {filename}...")
                
                # Copy the APK file to the save directory
                output_path = os.path.join(self.save_dir, filename)
                
                # Check if file already exists
                if os.path.exists(output_path):
                    base_name, extension = os.path.splitext(filename)
                    output_path = os.path.join(self.save_dir, f"{base_name}_{int(time.time())}{extension}")
                
                self.progress_update.emit(50, f"Copying APK file...")
                
                # Copy the file
                with open(self.apk_path, 'rb') as src, open(output_path, 'wb') as dst:
                    dst.write(src.read())
                
                self.progress_update.emit(100, f"Import completed: {output_path}")
                self.import_completed.emit(True, f"Successfully imported {filename}", output_path)
            
            else:
                self.import_completed.emit(False, "Error: No app name or APK file specified", "")
                
        except Exception as e:
            self.import_completed.emit(False, f"Error importing APK: {str(e)}", "")


class DuplicatesPanel(QWidget):
    """Panel for finding and managing duplicate files"""
    
    def __init__(self, file_system_manager):
        super().__init__()
        self.file_system_manager = file_system_manager
        self.initUI()
        
    def initUI(self):
        # Main layout
        layout = QVBoxLayout()
        
        # Controls area
        controls_layout = QHBoxLayout()
        
        # Directory selection
        self.path_label = QLabel("Directory:")
        self.path_edit = QLineEdit()
        self.path_edit.setText(os.path.expanduser("~"))
        self.path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        
        self.scan_button = QPushButton("Scan for Duplicates")
        self.scan_button.clicked.connect(self.start_scan)
        
        # Add controls to layout
        controls_layout.addWidget(self.path_label)
        controls_layout.addWidget(self.path_edit, 1)
        controls_layout.addWidget(self.browse_button)
        controls_layout.addWidget(self.scan_button)
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Statistics box
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        
        self.files_processed_label = QLabel("0")
        self.bytes_processed_label = QLabel("0 B")
        self.duplicate_sets_label = QLabel("0")
        self.duplicate_files_label = QLabel("0")
        self.wasted_space_label = QLabel("0 B")
        
        stats_layout.addRow("Files processed:", self.files_processed_label)
        stats_layout.addRow("Data processed:", self.bytes_processed_label)
        stats_layout.addRow("Duplicate sets:", self.duplicate_sets_label)
        stats_layout.addRow("Duplicate files:", self.duplicate_files_label)
        stats_layout.addRow("Wasted space:", self.wasted_space_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Duplicates table
        self.duplicates_table = QTableWidget()
        self.duplicates_table.setColumnCount(6)
        self.duplicates_table.setHorizontalHeaderLabels(
            ["Group", "Files", "File Size", "Wasted Space", "Hash", "Actions"]
        )
        self.duplicates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.duplicates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        self.duplicates_table.setColumnWidth(0, 60)  # Group
        self.duplicates_table.setColumnWidth(1, 60)  # Files
        self.duplicates_table.setColumnWidth(2, 120)  # File Size
        self.duplicates_table.setColumnWidth(3, 120)  # Wasted Space
        self.duplicates_table.setColumnWidth(4, 240)  # Hash
        self.duplicates_table.setColumnWidth(5, 120)  # Actions
        
        layout.addWidget(self.duplicates_table, 1)
        
        # Details area
        self.details_label = QLabel("Select a duplicate group to view details")
        layout.addWidget(self.details_label)
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels(
            ["File Name", "Path", "Size", "Modified Date", "Actions"]
        )
        self.details_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.details_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        self.details_table.setColumnWidth(0, 200)  # File Name
        self.details_table.setColumnWidth(1, 300)  # Path
        self.details_table.setColumnWidth(2, 120)  # Size
        self.details_table.setColumnWidth(3, 180)  # Modified Date
        self.details_table.setColumnWidth(4, 120)  # Actions
        
        layout.addWidget(self.details_table, 1)
        
        self.setLayout(layout)
        
        # Connect signals
        self.duplicates_table.cellClicked.connect(self.show_duplicate_details)
        
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan", self.path_edit.text()
        )
        if directory:
            self.path_edit.setText(directory)
        
    def start_scan(self):
        directory = self.path_edit.text()
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Invalid Directory", 
                              "Please select a valid directory to scan.")
            return
        
        self.duplicates_table.setRowCount(0)
        self.details_table.setRowCount(0)
        self.progress_bar.setValue(0)
        
        # Reset statistics
        self.files_processed_label.setText("0")
        self.bytes_processed_label.setText("0 B")
        self.duplicate_sets_label.setText("0")
        self.duplicate_files_label.setText("0")
        self.wasted_space_label.setText("0 B")
        
        # Disable scan button during scan
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning...")
        
        # Start scan thread
        self.scan_thread = DuplicateScanThread(self.file_system_manager, directory)
        self.scan_thread.progress_update.connect(self.update_progress)
        self.scan_thread.scan_completed.connect(self.scan_completed)
        self.scan_thread.start()
        
    def update_progress(self, progress):
        self.progress_bar.setValue(progress)
        
    def scan_completed(self, duplicate_groups, stats):
        # Update statistics
        self.files_processed_label.setText(str(stats['files_processed']))
        self.bytes_processed_label.setText(stats.get('formatted_bytes_processed', '0 B'))
        self.duplicate_sets_label.setText(str(stats['duplicate_sets']))
        self.duplicate_files_label.setText(str(stats['duplicate_files']))
        self.wasted_space_label.setText(stats.get('formatted_wasted_space', '0 B'))
        
        # Populate duplicate groups table
        self.duplicates_table.setRowCount(len(duplicate_groups))
        
        for row, group in enumerate(duplicate_groups):
            # Group number
            self.duplicates_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            # Number of files
            self.duplicates_table.setItem(row, 1, QTableWidgetItem(str(group['count'])))
            
            # File size
            size_item = QTableWidgetItem()
            if len(group['files']) > 0:
                size_item.setText(group['files'][0]['formatted_size'])
            self.duplicates_table.setItem(row, 2, size_item)
            
            # Wasted space
            waste_text = self._format_size(group['wasted_space'])
            self.duplicates_table.setItem(row, 3, QTableWidgetItem(waste_text))
            
            # Hash
            hash_item = QTableWidgetItem(group['hash'][:16] + "...")
            hash_item.setToolTip(group['hash'])
            self.duplicates_table.setItem(row, 4, hash_item)
            
            # Actions button
            view_button = QPushButton("View")
            view_button.clicked.connect(lambda checked, row=row: self.show_duplicate_details(row, 0))
            self.duplicates_table.setCellWidget(row, 5, view_button)
            
        # Re-enable scan button
        self.scan_button.setEnabled(True)
        self.scan_button.setText("Scan for Duplicates")
        
        # Show completion message
        QMessageBox.information(self, "Scan Completed", 
                              f"Found {stats['duplicate_sets']} sets of duplicate files, wasting {stats.get('formatted_wasted_space', '0 B')} of space.")
        
    def show_duplicate_details(self, row, column):
        if self.duplicates_table.rowCount() <= row:
            return
            
        # Get the duplicate group
        group_number = int(self.duplicates_table.item(row, 0).text())
        
        # Get the duplicate files for this group
        duplicate_groups = self.file_system_manager.duplicate_detector.get_duplicate_groups()
        if group_number <= len(duplicate_groups):
            group = duplicate_groups[group_number - 1]
            files = group['files']
            
            # Update details label
            self.details_label.setText(f"Group {group_number}: {len(files)} files with hash {group['hash'][:16]}...")
            
            # Populate details table
            self.details_table.setRowCount(len(files))
            
            for file_row, file_info in enumerate(files):
                # File name
                self.details_table.setItem(file_row, 0, QTableWidgetItem(file_info['name']))
                
                # Path
                path_item = QTableWidgetItem(file_info['path'])
                path_item.setToolTip(file_info['path'])
                self.details_table.setItem(file_row, 1, path_item)
                
                # Size
                self.details_table.setItem(file_row, 2, QTableWidgetItem(file_info['formatted_size']))
                
                # Modified date
                self.details_table.setItem(file_row, 3, QTableWidgetItem(file_info['formatted_date']))
                
                # Actions
                if file_row == 0:
                    # First file is considered the "original"
                    action_widget = QLabel("Original")
                    action_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    action_widget.setStyleSheet("color: green;")
                    self.details_table.setCellWidget(file_row, 4, action_widget)
                else:
                    # Create actions for duplicate files
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    actions_layout.setSpacing(2)
                    
                    delete_button = QPushButton("Delete")
                    delete_button.setStyleSheet("background-color: #ff6b6b;")
                    delete_button.clicked.connect(
                        lambda checked, path=file_info['path']: self.delete_duplicate(path)
                    )
                    
                    actions_layout.addWidget(delete_button)
                    
                    action_widget = QWidget()
                    action_widget.setLayout(actions_layout)
                    self.details_table.setCellWidget(file_row, 4, action_widget)
                    
    def delete_duplicate(self, file_path):
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete this file?\n{file_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "Success", f"File deleted: {file_path}")
                
                # Refresh the display
                self.start_scan()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting file: {str(e)}")
    
    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024


class APKImporterPanel(QWidget):
    """Panel for importing APK files"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Main layout
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("APK Importer")
        title_label.setFont(QFont('Arial', 16))
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel("Import APK files from Google Play Store or your local system.")
        layout.addWidget(instructions)
        
        # Add some spacing
        layout.addSpacing(10)
        
        # Import methods tabs
        tabs = QTabWidget()
        
        # Tab 1: Google Play Store
        play_store_tab = QWidget()
        play_store_layout = QVBoxLayout()
        
        # App name input
        form_layout = QFormLayout()
        self.app_name_edit = QLineEdit()
        form_layout.addRow("App Name:", self.app_name_edit)
        play_store_layout.addLayout(form_layout)
        
        # Import button
        self.play_store_import_button = QPushButton("Import from Google Play")
        self.play_store_import_button.clicked.connect(self.import_from_play_store)
        play_store_layout.addWidget(self.play_store_import_button)
        
        play_store_tab.setLayout(play_store_layout)
        tabs.addTab(play_store_tab, "Google Play Store")
        
        # Tab 2: Local File
        local_file_tab = QWidget()
        local_file_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_apk_file)
        
        file_layout.addWidget(self.file_path_edit, 1)
        file_layout.addWidget(browse_button)
        local_file_layout.addLayout(file_layout)
        
        # Import button
        self.local_import_button = QPushButton("Import Local APK")
        self.local_import_button.clicked.connect(self.import_local_apk)
        local_file_layout.addWidget(self.local_import_button)
        
        local_file_tab.setLayout(local_file_layout)
        tabs.addTab(local_file_tab, "Local File")
        
        layout.addWidget(tabs)
        
        # Progress area
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to import")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Imported apps list
        list_group = QGroupBox("Imported Apps")
        list_layout = QVBoxLayout()
        
        self.imported_list = QListWidget()
        list_layout.addWidget(self.imported_list)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, 1)
        
        self.setLayout(layout)
        
        # Add some sample items to the list
        self.add_sample_apps()
        
    def browse_apk_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select APK File", "", "APK Files (*.apk);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            
    def import_from_play_store(self):
        app_name = self.app_name_edit.text().strip()
        if not app_name:
            QMessageBox.warning(self, "Missing App Name", "Please enter the name of the app to import.")
            return
            
        # Start import thread
        self.import_thread = APKImportThread(app_name=app_name)
        self.import_thread.progress_update.connect(self.update_import_progress)
        self.import_thread.import_completed.connect(self.import_completed)
        
        # Disable buttons during import
        self.play_store_import_button.setEnabled(False)
        self.local_import_button.setEnabled(False)
        
        # Start the thread
        self.import_thread.start()
        
    def import_local_apk(self):
        file_path = self.file_path_edit.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid APK file to import.")
            return
            
        # Start import thread
        self.import_thread = APKImportThread(apk_path=file_path)
        self.import_thread.progress_update.connect(self.update_import_progress)
        self.import_thread.import_completed.connect(self.import_completed)
        
        # Disable buttons during import
        self.play_store_import_button.setEnabled(False)
        self.local_import_button.setEnabled(False)
        
        # Start the thread
        self.import_thread.start()
        
    def update_import_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    def import_completed(self, success, message, file_path):
        # Re-enable buttons
        self.play_store_import_button.setEnabled(True)
        self.local_import_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Import Successful", message)
            
            # Add to list
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.imported_list.addItem(item)
        else:
            QMessageBox.critical(self, "Import Failed", message)
        
    def add_sample_apps(self):
        # Add a few sample items to demonstrate the UI
        samples = [
            "com.example.game1.apk",
            "social_media_app.apk",
            "productivity_tool.apk",
            "photo_editor.apk"
        ]
        
        for sample in samples:
            item = QListWidgetItem(sample)
            item.setToolTip(f"Sample app: {sample}")
            self.imported_list.addItem(item)


class MainWindow(QMainWindow):
    """Main window for the Drive-Manager Pro desktop application"""
    
    def __init__(self):
        super().__init__()
        self.file_system_manager = FileSystemManager()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Drive-Manager Pro - Windows Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Header area
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title and logo
        logo_label = QLabel("Drive-Manager Pro")
        logo_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        header_layout.addWidget(logo_label)
        
        # Add a spacer to push the next widget to the right
        header_layout.addStretch(1)
        
        # System info
        system_info = self.get_system_info()
        system_label = QLabel(system_info)
        system_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(system_label)
        
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        # Main tab widget
        self.tabs = QTabWidget()
        
        # Add tab 1: Duplicate Files
        self.duplicates_panel = DuplicatesPanel(self.file_system_manager)
        self.tabs.addTab(self.duplicates_panel, "Duplicate Files")
        
        # Add tab 2: APK Importer
        self.apk_importer_panel = APKImporterPanel()
        self.tabs.addTab(self.apk_importer_panel, "APK Importer")
        
        # Add tabs to layout
        main_layout.addWidget(self.tabs)
        
        # Set the main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Set up status bar
        self.statusBar().showMessage("Ready")
        
    def get_system_info(self):
        """Get formatted system information for display"""
        system = platform.system()
        if system == "Windows":
            version = platform.version()
            release = platform.release()
            return f"Windows {release} ({version})"
        else:
            return platform.platform()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()