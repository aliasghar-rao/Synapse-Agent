"""
Tools panel module for Drive-Manager Pro.
Provides file explorer, tag editor, search, and other tools.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QHeaderView, QTableWidgetItem, QLineEdit, QPushButton, 
                            QLabel, QComboBox, QCheckBox, QTabWidget, QFileDialog,
                            QInputDialog, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QColor

import os
import config
from file_system import FileType

class FileExplorerWidget(QWidget):
    """Widget for browsing and managing files"""
    
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    file_operation_requested = pyqtSignal(str, str, str)  # operation, source, target
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.selected_file = ""
        self.setupUI()
    
    def setupUI(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Path navigation
        nav_layout = QHBoxLayout()
        
        self.path_label = QLabel("Path:")
        nav_layout.addWidget(self.path_label)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        nav_layout.addWidget(self.path_edit)
        
        self.up_button = QPushButton("↑")
        self.up_button.setToolTip("Up one level")
        self.up_button.clicked.connect(self.navigate_up)
        nav_layout.addWidget(self.up_button)
        
        layout.addLayout(nav_layout)
        
        # File list
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.file_table.doubleClicked.connect(self.handle_double_click)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.file_table)
        
        # File operations
        operations_layout = QHBoxLayout()
        
        self.new_folder_button = QPushButton("New Folder")
        self.new_folder_button.clicked.connect(self.create_new_folder)
        operations_layout.addWidget(self.new_folder_button)
        
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(lambda: self.handle_operation("copy"))
        operations_layout.addWidget(self.copy_button)
        
        self.move_button = QPushButton("Move")
        self.move_button.clicked.connect(lambda: self.handle_operation("move"))
        operations_layout.addWidget(self.move_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(lambda: self.handle_operation("delete"))
        operations_layout.addWidget(self.delete_button)
        
        layout.addLayout(operations_layout)
        
        # Apply styles
        self.setStyleSheet(f"""
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
            
            QTableWidget {{
                border: 1px solid {config.COLORS['border']};
                gridline-color: {config.COLORS['border']};
            }}
            
            QHeaderView::section {{
                background-color: {config.COLORS['section_bg']};
                color: {config.COLORS['text']};
                padding: 5px;
                border: 1px solid {config.COLORS['border']};
            }}
        """)
    
    def update_file_list(self, files):
        """Update the file list with the provided files"""
        self.file_table.setRowCount(0)
        self.file_table.setRowCount(len(files))
        
        for row, file in enumerate(files):
            # Name column
            name_item = QTableWidgetItem(file.name)
            if file.is_dir:
                name_item.setData(Qt.ItemDataRole.UserRole, "dir:" + file.path)
            else:
                name_item.setData(Qt.ItemDataRole.UserRole, "file:" + file.path)
            self.file_table.setItem(row, 0, name_item)
            
            # Type column
            if file.is_dir:
                type_item = QTableWidgetItem("Folder")
            else:
                type_item = QTableWidgetItem(file.extension)
            self.file_table.setItem(row, 1, type_item)
            
            # Size column
            size_item = QTableWidgetItem(file.get_formatted_size())
            self.file_table.setItem(row, 2, size_item)
            
            # Modified date column
            from datetime import datetime
            modified_time = datetime.fromtimestamp(file.modified).strftime("%Y-%m-%d %H:%M")
            modified_item = QTableWidgetItem(modified_time)
            self.file_table.setItem(row, 3, modified_item)
            
            # Color folders differently
            if file.is_dir:
                for col in range(4):
                    item = self.file_table.item(row, col)
                    if item:
                        item.setBackground(QColor(config.COLORS['hover']))
    
    def set_current_path(self, path):
        """Set the current directory path"""
        self.current_path = path
        self.path_edit.setText(path)
        self.directory_changed.emit(path)
    
    def navigate_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:  # Avoid infinite loop at root
            self.set_current_path(parent)
            self.directory_changed.emit(parent)
    
    def handle_double_click(self, index):
        """Handle double-click on file/folder"""
        row = index.row()
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return
            
        item_data = name_item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        if item_data.startswith("dir:"):
            # Navigate to directory
            dir_path = item_data[4:]
            self.set_current_path(dir_path)
            self.directory_changed.emit(dir_path)
        else:
            # Select file
            file_path = item_data[5:]
            self.selected_file = file_path
            self.file_selected.emit(file_path)
    
    def show_context_menu(self, position):
        """Show context menu for file operations"""
        # Get the selected item
        indexes = self.file_table.selectedIndexes()
        if not indexes:
            return
            
        # Create menu
        menu = QMenu(self)
        
        open_action = QAction("Open", self)
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        copy_action = QAction("Copy", self)
        menu.addAction(copy_action)
        
        move_action = QAction("Move", self)
        menu.addAction(move_action)
        
        rename_action = QAction("Rename", self)
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        menu.addAction(delete_action)
        
        # Get selected file or directory
        row = indexes[0].row()
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return
            
        item_data = name_item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        is_dir = item_data.startswith("dir:")
        path = item_data[4:] if is_dir else item_data[5:]
        
        # Connect actions
        open_action.triggered.connect(
            lambda: self.handle_double_click(indexes[0])
        )
        
        copy_action.triggered.connect(
            lambda: self.file_operation_requested.emit("copy", path, "")
        )
        
        move_action.triggered.connect(
            lambda: self.file_operation_requested.emit("move", path, "")
        )
        
        rename_action.triggered.connect(
            lambda: self.handle_rename(path)
        )
        
        delete_action.triggered.connect(
            lambda: self.handle_delete(path)
        )
        
        # Show the menu
        menu.exec(self.file_table.viewport().mapToGlobal(position))
    
    def handle_operation(self, operation):
        """Handle file operations from buttons"""
        selected_indexes = self.file_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.information(self, "No Selection", "Please select a file or folder first.")
            return
            
        row = selected_indexes[0].row()
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return
            
        item_data = name_item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        is_dir = item_data.startswith("dir:")
        path = item_data[4:] if is_dir else item_data[5:]
        
        if operation == "delete":
            self.handle_delete(path)
        elif operation == "copy":
            self.file_operation_requested.emit("copy", path, "")
        elif operation == "move":
            self.file_operation_requested.emit("move", path, "")
    
    def handle_delete(self, path):
        """Handle delete operation"""
        name = os.path.basename(path)
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.file_operation_requested.emit("delete", path, "")
    
    def handle_rename(self, path):
        """Handle rename operation"""
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", 
            QLineEdit.EchoMode.Normal, old_name
        )
        
        if ok and new_name and new_name != old_name:
            parent_dir = os.path.dirname(path)
            new_path = os.path.join(parent_dir, new_name)
            self.file_operation_requested.emit("rename", path, new_path)
    
    def create_new_folder(self):
        """Create a new folder in the current directory"""
        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:",
            QLineEdit.EchoMode.Normal, "New Folder"
        )
        
        if ok and folder_name:
            self.file_operation_requested.emit("new_folder", self.current_path, folder_name)


class SearchWidget(QWidget):
    """Widget for searching files"""
    
    search_requested = pyqtSignal(dict)  # search criteria
    result_selected = pyqtSignal(str)  # file path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
    
    def setupUI(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search criteria
        criteria_layout = QVBoxLayout()
        
        # Search terms
        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel("Search:"))
        self.search_term = QLineEdit()
        self.search_term.setPlaceholderText("Enter search terms...")
        self.search_term.returnPressed.connect(self.execute_search)
        term_layout.addWidget(self.search_term)
        criteria_layout.addLayout(term_layout)
        
        # Search location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))
        self.location_combo = QComboBox()
        self.location_combo.addItem("Home Directory", os.path.expanduser("~"))
        self.location_combo.addItem("Documents", os.path.join(os.path.expanduser("~"), "Documents"))
        self.location_combo.addItem("Downloads", os.path.join(os.path.expanduser("~"), "Downloads"))
        self.location_combo.addItem("Pictures", os.path.join(os.path.expanduser("~"), "Pictures"))
        self.location_combo.addItem("Custom Location...", "custom")
        self.location_combo.currentIndexChanged.connect(self.handle_location_change)
        location_layout.addWidget(self.location_combo)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_location)
        self.browse_button.setVisible(False)
        location_layout.addWidget(self.browse_button)
        
        criteria_layout.addLayout(location_layout)
        
        # File types
        types_layout = QHBoxLayout()
        types_layout.addWidget(QLabel("File Types:"))
        
        self.type_document = QCheckBox("Documents")
        types_layout.addWidget(self.type_document)
        
        self.type_image = QCheckBox("Images")
        types_layout.addWidget(self.type_image)
        
        self.type_audio = QCheckBox("Audio")
        types_layout.addWidget(self.type_audio)
        
        self.type_video = QCheckBox("Video")
        types_layout.addWidget(self.type_video)
        
        self.type_code = QCheckBox("Code")
        types_layout.addWidget(self.type_code)
        
        criteria_layout.addLayout(types_layout)
        
        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Modified:"))
        
        self.date_combo = QComboBox()
        self.date_combo.addItem("Any time", "any")
        self.date_combo.addItem("Today", "today")
        self.date_combo.addItem("This week", "week")
        self.date_combo.addItem("This month", "month")
        self.date_combo.addItem("This year", "year")
        date_layout.addWidget(self.date_combo)
        
        criteria_layout.addLayout(date_layout)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.execute_search)
        criteria_layout.addWidget(self.search_button)
        
        layout.addLayout(criteria_layout)
        
        # Search results
        self.results_label = QLabel("Results:")
        layout.addWidget(self.results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Name", "Location", "Type", "Modified"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.doubleClicked.connect(self.handle_result_double_click)
        
        layout.addWidget(self.results_table)
        
        # Apply styles
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLORS['tools']};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
            
            QPushButton:hover {{
                background-color: #8E44AD;
            }}
            
            QTableWidget {{
                border: 1px solid {config.COLORS['border']};
                gridline-color: {config.COLORS['border']};
            }}
            
            QHeaderView::section {{
                background-color: {config.COLORS['section_bg']};
                color: {config.COLORS['text']};
                padding: 5px;
                border: 1px solid {config.COLORS['border']};
            }}
            
            QCheckBox {{
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            
            QCheckBox::indicator:unchecked {{
                border: 1px solid {config.COLORS['border']};
                background-color: white;
            }}
            
            QCheckBox::indicator:checked {{
                border: 1px solid {config.COLORS['tools']};
                background-color: {config.COLORS['tools']};
            }}
        """)
    
    def handle_location_change(self, index):
        """Handle location combobox change"""
        if self.location_combo.currentData() == "custom":
            self.browse_button.setVisible(True)
        else:
            self.browse_button.setVisible(False)
    
    def browse_location(self):
        """Browse for a custom search location"""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                # Add the selected directory to the combobox
                self.location_combo.setItemData(
                    self.location_combo.currentIndex(), selected_dirs[0]
                )
    
    def execute_search(self):
        """Execute the search with the current criteria"""
        # Gather search criteria
        criteria = {
            'term': self.search_term.text(),
            'location': self.location_combo.currentData(),
            'file_types': []
        }
        
        # Add selected file types
        if self.type_document.isChecked():
            criteria['file_types'].append(FileType.DOCUMENT)
        if self.type_image.isChecked():
            criteria['file_types'].append(FileType.IMAGE)
        if self.type_audio.isChecked():
            criteria['file_types'].append(FileType.AUDIO)
        if self.type_video.isChecked():
            criteria['file_types'].append(FileType.VIDEO)
        if self.type_code.isChecked():
            criteria['file_types'].append(FileType.CODE)
            
        # Add date filter
        criteria['date_filter'] = self.date_combo.currentData()
        
        # Emit search request
        self.search_requested.emit(criteria)
        
        # For now, show mock results
        self.show_mock_results()
    
    def show_mock_results(self):
        """Show mock search results for demonstration"""
        self.results_table.setRowCount(0)
        
        term = self.search_term.text().lower()
        if not term:
            return
            
        # Generate mock results
        mock_results = [
            {
                'name': 'project_report.docx',
                'path': os.path.join(os.path.expanduser('~'), 'Documents', 'project_report.docx'),
                'type': FileType.DOCUMENT,
                'modified': '2023-05-15 14:32'
            },
            {
                'name': 'meeting_notes.txt',
                'path': os.path.join(os.path.expanduser('~'), 'Documents', 'meeting_notes.txt'),
                'type': FileType.DOCUMENT,
                'modified': '2023-05-10 09:45'
            },
            {
                'name': 'logo.png',
                'path': os.path.join(os.path.expanduser('~'), 'Pictures', 'logo.png'),
                'type': FileType.IMAGE,
                'modified': '2023-04-20 11:15'
            },
            {
                'name': 'test.py',
                'path': os.path.join(os.path.expanduser('~'), 'projects', 'test.py'),
                'type': FileType.CODE,
                'modified': '2023-05-18 16:22'
            }
        ]
        
        # Filter results by term
        filtered_results = [
            result for result in mock_results 
            if term in result['name'].lower()
        ]
        
        # Display results
        self.results_table.setRowCount(len(filtered_results))
        for row, result in enumerate(filtered_results):
            # Name
            name_item = QTableWidgetItem(result['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, result['path'])
            self.results_table.setItem(row, 0, name_item)
            
            # Location
            location = os.path.dirname(result['path'])
            location_item = QTableWidgetItem(location)
            self.results_table.setItem(row, 1, location_item)
            
            # Type
            type_str = result['type'].capitalize() if isinstance(result['type'], str) else result['type']
            type_item = QTableWidgetItem(type_str)
            self.results_table.setItem(row, 2, type_item)
            
            # Modified
            modified_item = QTableWidgetItem(result['modified'])
            self.results_table.setItem(row, 3, modified_item)
        
        self.results_label.setText(f"Results: {len(filtered_results)} items found")
    
    def handle_result_double_click(self, index):
        """Handle double-click on a search result"""
        row = index.row()
        name_item = self.results_table.item(row, 0)
        if not name_item:
            return
            
        file_path = name_item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.result_selected.emit(file_path)


class TagEditorWidget(QWidget):
    """Widget for editing tags for files"""
    
    tag_added = pyqtSignal(str, str)  # file_path, tag
    tag_removed = pyqtSignal(str, str)  # file_path, tag
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.setupUI()
    
    def setupUI(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File info
        info_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet(f"font-weight: bold; color: {config.COLORS['text']};")
        info_layout.addWidget(self.file_label)
        
        self.type_label = QLabel("Type: -")
        info_layout.addWidget(self.type_label)
        
        self.size_label = QLabel("Size: -")
        info_layout.addWidget(self.size_label)
        
        layout.addLayout(info_layout)
        
        # Current tags
        self.tags_label = QLabel("Tags:")
        layout.addWidget(self.tags_label)
        
        self.tags_layout = QHBoxLayout()
        layout.addLayout(self.tags_layout)
        
        # New tag input
        tag_input_layout = QHBoxLayout()
        
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Add a new tag...")
        self.tag_input.returnPressed.connect(self.add_tag)
        tag_input_layout.addWidget(self.tag_input)
        
        self.add_tag_button = QPushButton("Add")
        self.add_tag_button.clicked.connect(self.add_tag)
        tag_input_layout.addWidget(self.add_tag_button)
        
        layout.addLayout(tag_input_layout)
        
        # Suggested tags
        self.suggestions_label = QLabel("Suggested tags:")
        layout.addWidget(self.suggestions_label)
        
        self.suggestions_layout = QHBoxLayout()
        layout.addLayout(self.suggestions_layout)
        
        # Stretch to fill
        layout.addStretch()
        
        # Apply styles
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLORS['tools']};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
            
            QPushButton:hover {{
                background-color: #8E44AD;
            }}
            
            QPushButton.tag-button {{
                background-color: {config.COLORS['files']};
                margin-right: 5px;
            }}
            
            QPushButton.tag-button:hover {{
                background-color: #27AE60;
            }}
            
            QPushButton.suggestion-button {{
                background-color: {config.COLORS['cloud']};
                margin-right: 5px;
            }}
            
            QPushButton.suggestion-button:hover {{
                background-color: #D35400;
            }}
        """)
    
    def set_file(self, file_metadata):
        """Set the current file to edit tags for"""
        self.current_file = file_metadata
        
        # Update UI with file info
        self.file_label.setText(file_metadata.name)
        self.type_label.setText(f"Type: {file_metadata.file_type}")
        self.size_label.setText(f"Size: {file_metadata.get_formatted_size()}")
        
        # Clear existing tags
        self.clear_tags()
        
        # Add current tags
        for tag in file_metadata.tags:
            self.add_tag_button_to_ui(tag)
        
        # Add suggested tags
        self.clear_suggestions()
        suggestions = ['document', 'work', 'important']  # Mock suggestions
        for suggestion in suggestions:
            if suggestion not in file_metadata.tags:
                self.add_suggestion_button_to_ui(suggestion)
    
    def clear_tags(self):
        """Clear the tags UI"""
        # Clear the tags layout
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def clear_suggestions(self):
        """Clear the suggestions UI"""
        # Clear the suggestions layout
        while self.suggestions_layout.count():
            item = self.suggestions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_tag(self):
        """Add a new tag to the current file"""
        if not self.current_file:
            return
            
        tag = self.tag_input.text().strip()
        if not tag:
            return
            
        # Check if tag already exists
        if tag in self.current_file.tags:
            return
            
        # Add tag to file
        self.current_file.add_tag(tag)
        
        # Add tag to UI
        self.add_tag_button_to_ui(tag)
        
        # Clear input
        self.tag_input.clear()
        
        # Emit signal
        self.tag_added.emit(self.current_file.path, tag)
    
    def add_tag_button_to_ui(self, tag):
        """Add a tag button to the UI"""
        button = QPushButton(tag)
        button.setProperty("class", "tag-button")
        button.setMaximumHeight(30)
        
        # Add x icon for removal
        button.clicked.connect(lambda: self.remove_tag(tag))
        
        self.tags_layout.addWidget(button)
    
    def add_suggestion_button_to_ui(self, tag):
        """Add a suggestion button to the UI"""
        button = QPushButton(tag)
        button.setProperty("class", "suggestion-button")
        button.setMaximumHeight(30)
        
        # Add + icon for adding
        button.clicked.connect(lambda: self.add_suggested_tag(tag))
        
        self.suggestions_layout.addWidget(button)
    
    def remove_tag(self, tag):
        """Remove a tag from the current file"""
        if not self.current_file:
            return
            
        # Remove tag from file
        self.current_file.remove_tag(tag)
        
        # Refresh tags UI
        self.clear_tags()
        for tag in self.current_file.tags:
            self.add_tag_button_to_ui(tag)
            
        # Add as suggestion
        self.add_suggestion_button_to_ui(tag)
        
        # Emit signal
        self.tag_removed.emit(self.current_file.path, tag)
    
    def add_suggested_tag(self, tag):
        """Add a suggested tag to the current file"""
        if not self.current_file:
            return
            
        # Add tag to file
        self.current_file.add_tag(tag)
        
        # Refresh UI
        self.clear_suggestions()
        self.clear_tags()
        
        # Add current tags
        for tag in self.current_file.tags:
            self.add_tag_button_to_ui(tag)
            
        # Add remaining suggestions
        suggestions = ['document', 'work', 'important']  # Mock suggestions
        for suggestion in suggestions:
            if suggestion not in self.current_file.tags:
                self.add_suggestion_button_to_ui(suggestion)
        
        # Emit signal
        self.tag_added.emit(self.current_file.path, tag)


class ToolsWidget(QWidget):
    """Widget containing all the tools functionality"""
    
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    operation_requested = pyqtSignal(str, str, str)  # operation, source, target
    tag_modified = pyqtSignal(str, list)  # file_path, tags_list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
    
    def setupUI(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # File explorer tab
        self.file_explorer = FileExplorerWidget()
        self.file_explorer.file_selected.connect(self.handle_file_selected)
        self.file_explorer.directory_changed.connect(self.directory_changed)
        self.file_explorer.file_operation_requested.connect(self.operation_requested)
        self.tabs.addTab(self.file_explorer, "Explorer")
        
        # Search tab
        self.search_widget = SearchWidget()
        self.search_widget.result_selected.connect(self.handle_file_selected)
        self.tabs.addTab(self.search_widget, "Search")
        
        # Tag editor tab
        self.tag_editor = TagEditorWidget()
        self.tag_editor.tag_added.connect(self.handle_tag_modified)
        self.tag_editor.tag_removed.connect(self.handle_tag_modified)
        self.tabs.addTab(self.tag_editor, "Tags")
        
        layout.addWidget(self.tabs)
        
        # Apply styles
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {config.COLORS['border']};
                background-color: {config.COLORS['section_bg']};
            }}
            
            QTabBar::tab {{
                background-color: {config.COLORS['main_bg']};
                border: 1px solid {config.COLORS['border']};
                padding: 6px 12px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {config.COLORS['tools']};
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #D7BDE2;
            }}
        """)
    
    def handle_file_selected(self, file_path):
        """Handle file selection from any tool"""
        self.file_selected.emit(file_path)
    
    def handle_tag_modified(self, file_path, tag):
        """Handle tag modifications from tag editor"""
        # This handler will be expanded in a full implementation
        # to update the file system or database with the tag changes
        
        # For now, just emit a signal
        self.tag_modified.emit(file_path, [tag])
    
    def set_current_directory(self, path):
        """Set the current directory in file explorer"""
        self.file_explorer.set_current_path(path)
    
    def update_file_list(self, files):
        """Update the file list in file explorer"""
        self.file_explorer.update_file_list(files)
    
    def set_current_file(self, file_metadata):
        """Set the current file in tag editor"""
        self.tag_editor.set_file(file_metadata)
