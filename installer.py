"""
Installer script for Drive-Manager Pro.
Creates an installer package with all dependencies and proper file structure.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import platform
import subprocess
import argparse
import datetime
import json
import re

class InstallerBuilder:
    """Creates installation packages for Drive-Manager Pro"""
    
    def __init__(self, target_platform=None, output_dir=None, version="1.0.0"):
        """Initialize the installer builder"""
        self.target_platform = target_platform or platform.system().lower()
        self.output_dir = output_dir or os.path.join(os.getcwd(), "dist")
        self.version = version
        self.temp_dir = tempfile.mkdtemp(prefix="drive_manager_installer_")
        
        # Record the creation timestamp
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def build_installer(self):
        """Build installer package for the target platform"""
        if self.target_platform == "windows":
            return self._build_windows_installer()
        elif self.target_platform == "darwin":
            return self._build_macos_installer()
        elif self.target_platform == "linux":
            return self._build_linux_installer()
        else:
            return {
                "success": False,
                "error": f"Unsupported platform: {self.target_platform}"
            }
            
    def _build_windows_installer(self):
        """Build Windows installer (exe)"""
        try:
            # Create the package directory structure
            package_dir = os.path.join(self.temp_dir, "DriveManagerPro")
            os.makedirs(package_dir, exist_ok=True)
            
            # Create subdirectories
            dirs_to_create = [
                "bin",
                "lib",
                "assets",
                "templates",
                "config",
                "docs",
                "logs"
            ]
            
            for dir_name in dirs_to_create:
                os.makedirs(os.path.join(package_dir, dir_name), exist_ok=True)
            
            # Copy source files
            self._copy_source_files(package_dir)
            
            # Create main executable batch file
            self._create_windows_batch_file(package_dir)
            
            # Create configuration file
            self._create_config_file(package_dir)
            
            # Create documentation
            self._create_documentation(package_dir)
            
            # Create inno setup script
            iss_script_path = os.path.join(self.temp_dir, "drive_manager_setup.iss")
            self._create_inno_setup_script(iss_script_path, package_dir)
            
            # Build the installer with Inno Setup (if available)
            try:
                inno_result = self._build_with_inno_setup(iss_script_path)
                if inno_result.get("success"):
                    return inno_result
            except Exception as e:
                print(f"Inno Setup build failed: {e}")
                print("Falling back to ZIP archive")
            
            # If Inno Setup fails or is not available, fall back to zip archive
            return self._create_zip_archive(package_dir, "DriveManagerPro_Windows")
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error building Windows installer: {str(e)}"
            }
    
    def _build_macos_installer(self):
        """Build macOS installer (DMG)"""
        try:
            # Create the package directory structure
            package_dir = os.path.join(self.temp_dir, "DriveManagerPro.app")
            os.makedirs(package_dir, exist_ok=True)
            
            # Create macOS app structure
            contents_dir = os.path.join(package_dir, "Contents")
            os.makedirs(contents_dir, exist_ok=True)
            
            macos_dir = os.path.join(contents_dir, "MacOS")
            os.makedirs(macos_dir, exist_ok=True)
            
            resources_dir = os.path.join(contents_dir, "Resources")
            os.makedirs(resources_dir, exist_ok=True)
            
            # Copy source files to Resources
            self._copy_source_files(resources_dir)
            
            # Create the Info.plist file
            self._create_info_plist(contents_dir)
            
            # Create the main executable script
            self._create_macos_launcher(macos_dir)
            
            # Create configuration file
            self._create_config_file(resources_dir)
            
            # Create documentation
            self._create_documentation(resources_dir)
            
            # Try to create DMG (requires hdiutil on macOS)
            if platform.system() == "Darwin":
                return self._create_dmg(package_dir)
            else:
                # Fall back to zip archive if not on macOS
                return self._create_zip_archive(package_dir, "DriveManagerPro_macOS")
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error building macOS installer: {str(e)}"
            }
    
    def _build_linux_installer(self):
        """Build Linux installer (deb, rpm, or tar.gz)"""
        try:
            # Create the package directory structure
            package_dir = os.path.join(self.temp_dir, "drivemanagerpro")
            os.makedirs(package_dir, exist_ok=True)
            
            # Create subdirectories
            dirs_to_create = [
                "bin",
                "lib",
                "assets",
                "templates",
                "config",
                "doc",
                "var/log"
            ]
            
            for dir_name in dirs_to_create:
                os.makedirs(os.path.join(package_dir, dir_name), exist_ok=True)
            
            # Copy source files
            self._copy_source_files(package_dir)
            
            # Create main executable script
            self._create_linux_launcher(package_dir)
            
            # Create configuration file
            self._create_config_file(package_dir)
            
            # Create documentation
            self._create_documentation(package_dir)
            
            # Try to create .deb package (requires dpkg-deb)
            try:
                deb_result = self._create_deb_package(package_dir)
                if deb_result.get("success"):
                    return deb_result
            except Exception as e:
                print(f"DEB package creation failed: {e}")
                print("Falling back to tar.gz archive")
            
            # Fall back to tar.gz archive
            return self._create_tarball(package_dir, "DriveManagerPro_Linux")
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error building Linux installer: {str(e)}"
            }
    
    def _copy_source_files(self, dest_dir):
        """Copy all source files to the destination directory"""
        # Source files to copy
        files_to_copy = [
            "account_manager.py",
            "ai_analysis.py",
            "ai_media_generator.py",
            "apk_analyzer.py",
            "app_generator.py",
            "cloud_storage.py",
            "config.py",
            "database.py",
            "demo_app.py",
            "file_system.py",
            "file_system_web.py",
            "main.py",
            "media_handler.py",
            "mind_map.py",
            "models.py",
            "platform_specific.py",
            "platform_utils.py",
            "tools_panel.py",
            "ui_extractor.py",
            "windows_app.py",
            "pyproject.toml",
            "requirements.txt",  # Will be created if doesn't exist
        ]
        
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            self._create_requirements_file()
        
        # Source assets to copy
        asset_files = [
            "generated-icon.png"
        ]
        
        # Create destination directories
        os.makedirs(os.path.join(dest_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(dest_dir, "assets"), exist_ok=True)
        
        # Copy the files
        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy2(file_name, os.path.join(dest_dir, "src", file_name))
        
        # Copy assets
        for asset_file in asset_files:
            if os.path.exists(asset_file):
                shutil.copy2(asset_file, os.path.join(dest_dir, "assets", asset_file))
    
    def _create_requirements_file(self):
        """Create a requirements.txt file with all dependencies"""
        with open("requirements.txt", "w") as f:
            f.write("# Drive-Manager Pro dependencies\n")
            f.write("PyQt6>=6.0.0\n")
            f.write("sqlalchemy>=1.4.0\n")
            f.write("psycopg2-binary>=2.9.0\n")
            f.write("pillow>=9.0.0\n")
            f.write("numpy>=1.20.0\n")
            f.write("matplotlib>=3.5.0\n")
            f.write("networkx>=2.6.0\n")
            f.write("opencv-python>=4.5.0\n")
            f.write("requests>=2.26.0\n")
            f.write("canvashacks>=0.0.1\n")
            f.write("openai>=1.0.0\n")
    
    def _create_windows_batch_file(self, package_dir):
        """Create a Windows batch file to launch the application"""
        batch_path = os.path.join(package_dir, "DriveManagerPro.bat")
        
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write("title Drive-Manager Pro\n")
            f.write("cd /d %~dp0\n")
            f.write("set PYTHONPATH=%~dp0;%~dp0\\src\n")
            f.write("set CONFIG_DIR=%~dp0\\config\n")
            f.write("set LOG_DIR=%~dp0\\logs\n")
            f.write("set ASSETS_DIR=%~dp0\\assets\n")
            f.write("\n")
            f.write(":: Check if Python is installed\n")
            f.write("python --version >nul 2>&1\n")
            f.write("if %ERRORLEVEL% neq 0 (\n")
            f.write("    echo Python is not installed or not in the PATH\n")
            f.write("    echo Please install Python 3.9 or later from https://www.python.org/\n")
            f.write("    pause\n")
            f.write("    exit /b 1\n")
            f.write(")\n")
            f.write("\n")
            f.write(":: Create virtual environment if it doesn't exist\n")
            f.write("if not exist \"%~dp0\\venv\" (\n")
            f.write("    echo Creating virtual environment...\n")
            f.write("    python -m venv \"%~dp0\\venv\"\n")
            f.write("    call \"%~dp0\\venv\\Scripts\\activate.bat\"\n")
            f.write("    pip install -r \"%~dp0\\src\\requirements.txt\"\n")
            f.write(") else (\n")
            f.write("    call \"%~dp0\\venv\\Scripts\\activate.bat\"\n")
            f.write(")\n")
            f.write("\n")
            f.write(":: Launch the application\n")
            f.write("echo Starting Drive-Manager Pro...\n")
            f.write("python \"%~dp0\\src\\windows_app.py\"\n")
            f.write("\n")
            f.write("if %ERRORLEVEL% neq 0 (\n")
            f.write("    echo An error occurred while running the application.\n")
            f.write("    echo Please check the logs in %~dp0\\logs\n")
            f.write("    pause\n")
            f.write(")\n")
        
        # Make it executable
        os.chmod(batch_path, 0o755)
    
    def _create_macos_launcher(self, macos_dir):
        """Create a macOS launcher script"""
        launcher_path = os.path.join(macos_dir, "DriveManagerPro")
        
        with open(launcher_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Drive-Manager Pro launcher for macOS\n\n")
            f.write("# Get the app bundle path\n")
            f.write("APP_PATH=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n")
            f.write("RESOURCES_PATH=\"$APP_PATH/Resources\"\n")
            f.write("SRC_PATH=\"$RESOURCES_PATH/src\"\n")
            f.write("VENV_PATH=\"$RESOURCES_PATH/venv\"\n")
            f.write("CONFIG_PATH=\"$RESOURCES_PATH/config\"\n")
            f.write("LOG_PATH=\"$RESOURCES_PATH/logs\"\n")
            f.write("\n")
            f.write("# Create logs directory if it doesn't exist\n")
            f.write("mkdir -p \"$LOG_PATH\"\n")
            f.write("\n")
            f.write("# Check if Python is installed\n")
            f.write("if ! command -v python3 &> /dev/null; then\n")
            f.write("    osascript -e 'display dialog \"Python 3 is required but not found. Please install Python 3.9 or later from https://www.python.org/\" buttons {\"OK\"} default button \"OK\" with title \"Drive-Manager Pro\" with icon stop'\n")
            f.write("    exit 1\n")
            f.write("fi\n")
            f.write("\n")
            f.write("# Create and activate a virtual environment if it doesn't exist\n")
            f.write("if [ ! -d \"$VENV_PATH\" ]; then\n")
            f.write("    python3 -m venv \"$VENV_PATH\"\n")
            f.write("    source \"$VENV_PATH/bin/activate\"\n")
            f.write("    pip install -r \"$SRC_PATH/requirements.txt\"\n")
            f.write("else\n")
            f.write("    source \"$VENV_PATH/bin/activate\"\n")
            f.write("fi\n")
            f.write("\n")
            f.write("# Set environment variables\n")
            f.write("export PYTHONPATH=\"$SRC_PATH:$PYTHONPATH\"\n")
            f.write("export CONFIG_DIR=\"$CONFIG_PATH\"\n")
            f.write("export LOG_DIR=\"$LOG_PATH\"\n")
            f.write("export ASSETS_DIR=\"$RESOURCES_PATH/assets\"\n")
            f.write("\n")
            f.write("# Launch the application\n")
            f.write("cd \"$SRC_PATH\"\n")
            f.write("python3 \"$SRC_PATH/main.py\" \"$@\" 2>&1 | tee -a \"$LOG_PATH/app.log\"\n")
        
        # Make it executable
        os.chmod(launcher_path, 0o755)
    
    def _create_linux_launcher(self, package_dir):
        """Create a Linux launcher script"""
        bin_dir = os.path.join(package_dir, "bin")
        launcher_path = os.path.join(bin_dir, "drivemanagerpro")
        
        with open(launcher_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Drive-Manager Pro launcher for Linux\n\n")
            f.write("# Get the installation directory\n")
            f.write("INSTALL_DIR=\"$(dirname \"$(dirname \"$(readlink -f \"$0\")\")\")\"  # parent of the bin dir\n")
            f.write("SRC_DIR=\"$INSTALL_DIR\"\n")
            f.write("VENV_PATH=\"$INSTALL_DIR/venv\"\n")
            f.write("CONFIG_DIR=\"$INSTALL_DIR/config\"\n")
            f.write("LOG_DIR=\"$INSTALL_DIR/var/log\"\n")
            f.write("ASSETS_DIR=\"$INSTALL_DIR/assets\"\n")
            f.write("\n")
            f.write("# Create necessary directories\n")
            f.write("mkdir -p \"$LOG_DIR\"\n")
            f.write("\n")
            f.write("# Check if Python is installed\n")
            f.write("if ! command -v python3 &> /dev/null; then\n")
            f.write("    echo \"Python 3 is required but not found. Please install Python 3.9 or later.\"\n")
            f.write("    exit 1\n")
            f.write("fi\n")
            f.write("\n")
            f.write("# Create and activate a virtual environment if it doesn't exist\n")
            f.write("if [ ! -d \"$VENV_PATH\" ]; then\n")
            f.write("    python3 -m venv \"$VENV_PATH\"\n")
            f.write("    source \"$VENV_PATH/bin/activate\"\n")
            f.write("    pip install -r \"$SRC_DIR/src/requirements.txt\"\n")
            f.write("else\n")
            f.write("    source \"$VENV_PATH/bin/activate\"\n")
            f.write("fi\n")
            f.write("\n")
            f.write("# Set environment variables\n")
            f.write("export PYTHONPATH=\"$SRC_DIR/src:$PYTHONPATH\"\n")
            f.write("export CONFIG_DIR=\"$CONFIG_DIR\"\n")
            f.write("export LOG_DIR=\"$LOG_DIR\"\n")
            f.write("export ASSETS_DIR=\"$ASSETS_DIR\"\n")
            f.write("\n")
            f.write("# Launch the application\n")
            f.write("cd \"$SRC_DIR\"\n")
            f.write("python3 \"$SRC_DIR/src/main.py\" \"$@\" 2>&1 | tee -a \"$LOG_DIR/app.log\"\n")
        
        # Make it executable
        os.chmod(launcher_path, 0o755)
    
    def _create_info_plist(self, contents_dir):
        """Create Info.plist for macOS app bundle"""
        plist_path = os.path.join(contents_dir, "Info.plist")
        
        with open(plist_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
            f.write('<plist version="1.0">\n')
            f.write('<dict>\n')
            f.write('    <key>CFBundleDisplayName</key>\n')
            f.write('    <string>Drive-Manager Pro</string>\n')
            f.write('    <key>CFBundleExecutable</key>\n')
            f.write('    <string>DriveManagerPro</string>\n')
            f.write('    <key>CFBundleIconFile</key>\n')
            f.write('    <string>AppIcon</string>\n')
            f.write('    <key>CFBundleIdentifier</key>\n')
            f.write('    <string>com.example.drivemanagerpro</string>\n')
            f.write('    <key>CFBundleInfoDictionaryVersion</key>\n')
            f.write('    <string>6.0</string>\n')
            f.write('    <key>CFBundleName</key>\n')
            f.write('    <string>DriveManagerPro</string>\n')
            f.write('    <key>CFBundlePackageType</key>\n')
            f.write('    <string>APPL</string>\n')
            f.write('    <key>CFBundleShortVersionString</key>\n')
            f.write(f'    <string>{self.version}</string>\n')
            f.write('    <key>CFBundleVersion</key>\n')
            f.write(f'    <string>{self.version}</string>\n')
            f.write('    <key>NSHighResolutionCapable</key>\n')
            f.write('    <true/>\n')
            f.write('    <key>NSHumanReadableCopyright</key>\n')
            f.write('    <string>Copyright © 2023. All rights reserved.</string>\n')
            f.write('    <key>NSPrincipalClass</key>\n')
            f.write('    <string>NSApplication</string>\n')
            f.write('</dict>\n')
            f.write('</plist>\n')
    
    def _create_config_file(self, package_dir):
        """Create a configuration file"""
        config_dir = os.path.join(package_dir, "config")
        if not os.path.exists(config_dir):
            config_dir = package_dir  # Fall back if the expected path doesn't exist
            
        config_path = os.path.join(config_dir, "config.json")
        
        config = {
            "application": {
                "name": "Drive-Manager Pro",
                "version": self.version,
                "release_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "organization": "Example Organization",
                "website": "https://example.com",
                "update_url": "https://example.com/updates"
            },
            "paths": {
                "logs": "${LOG_DIR}",
                "assets": "${ASSETS_DIR}",
                "temp": "${TEMP}/DriveManagerPro",
                "user_data": "${USER_DATA}/DriveManagerPro"
            },
            "database": {
                "type": "sqlite",
                "path": "${USER_DATA}/DriveManagerPro/database.db",
                "backup_dir": "${USER_DATA}/DriveManagerPro/backups"
            },
            "features": {
                "enable_analytics": False,
                "enable_auto_update": True,
                "enable_cloud_sync": False,
                "enable_ai_features": True,
                "enable_debug_mode": False
            },
            "ai": {
                "default_provider": "local",
                "providers": {
                    "local": {
                        "model_path": "${ASSETS_DIR}/models",
                        "enable_gpu": True
                    },
                    "openai": {
                        "api_key_env": "OPENAI_API_KEY"
                    }
                }
            },
            "ui": {
                "theme": "system",
                "themes": ["system", "light", "dark", "blue", "green"],
                "language": "en",
                "languages": ["en", "es", "fr", "de", "ja", "zh"],
                "font_size": "medium",
                "font_sizes": ["small", "medium", "large"]
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    
    def _create_documentation(self, package_dir):
        """Create documentation files"""
        # Determine the docs directory
        if os.path.exists(os.path.join(package_dir, "docs")):
            docs_dir = os.path.join(package_dir, "docs")
        elif os.path.exists(os.path.join(package_dir, "doc")):
            docs_dir = os.path.join(package_dir, "doc")
        else:
            # Create it in the package dir
            docs_dir = os.path.join(package_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
        
        # Create README
        readme_path = os.path.join(docs_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Drive-Manager Pro\n\n")
            f.write("Drive-Manager Pro is a cross-platform file management application leveraging advanced AI technologies for intelligent file organization, recommendation, and interaction.\n\n")
            f.write("## Key Features\n\n")
            f.write("- Neural network-based interface\n")
            f.write("- Multi-tier AI model integration (local, cloud-hosted, API-based)\n")
            f.write("- Mind map visualization\n")
            f.write("- Cross-platform compatibility (Windows, Linux, macOS, Android)\n")
            f.write("- Adaptive learning AI recommendation system\n")
            f.write("- Intelligent file duplicate detection\n")
            f.write("- APK analysis and feature extraction\n")
            f.write("- UI design extractor for application development\n\n")
            f.write("## System Requirements\n\n")
            f.write("- Windows 10/11, macOS 11+, or Ubuntu 20.04+\n")
            f.write("- Python 3.9 or higher\n")
            f.write("- 8GB RAM minimum (16GB recommended)\n")
            f.write("- 2GB free disk space\n")
            f.write("- Internet connection for cloud features\n\n")
            f.write("## Installation\n\n")
            f.write("1. Run the installer package for your platform\n")
            f.write("2. Follow the installation prompts\n")
            f.write("3. Launch Drive-Manager Pro from your applications menu or desktop shortcut\n\n")
            f.write("## Documentation\n\n")
            f.write("For full documentation, visit the docs directory or our website.\n\n")
            f.write("## License\n\n")
            f.write("Copyright © 2023 Example Organization. All rights reserved.\n")
        
        # Create LICENSE
        license_path = os.path.join(docs_dir, "LICENSE.txt")
        with open(license_path, "w") as f:
            f.write("Copyright © 2023 Example Organization. All rights reserved.\n\n")
            f.write("This software is provided for evaluation and personal use only.\n")
            f.write("Redistribution and use in source and binary forms, with or without modification,\n")
            f.write("are not permitted without express written permission from the copyright holder.\n\n")
            f.write("THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND\n")
            f.write("ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED\n")
            f.write("WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.\n")
        
        # Create CHANGELOG
        changelog_path = os.path.join(docs_dir, "CHANGELOG.md")
        with open(changelog_path, "w") as f:
            f.write("# Changelog\n\n")
            f.write("## Version 1.0.0 (2023-05-21)\n\n")
            f.write("Initial release with the following features:\n\n")
            f.write("- Cross-platform file management\n")
            f.write("- Neural network-based interface\n")
            f.write("- Multi-tier AI model integration\n")
            f.write("- Mind map visualization\n")
            f.write("- Intelligent file duplicate detection\n")
            f.write("- APK analysis and feature extraction\n")
    
    def _create_inno_setup_script(self, script_path, package_dir):
        """Create an Inno Setup script for Windows installer"""
        with open(script_path, "w") as f:
            f.write("; Drive-Manager Pro Installer Script\n")
            f.write("; Generated by InstallerBuilder\n\n")
            f.write("[Setup]\n")
            f.write("AppName=Drive-Manager Pro\n")
            f.write(f"AppVersion={self.version}\n")
            f.write("AppPublisher=Example Organization\n")
            f.write("AppPublisherURL=https://example.com\n")
            f.write("AppSupportURL=https://example.com/support\n")
            f.write("AppUpdatesURL=https://example.com/updates\n")
            f.write("DefaultDirName={autopf}\\DriveManagerPro\n")
            f.write("DefaultGroupName=Drive-Manager Pro\n")
            f.write("OutputDir=" + self.output_dir.replace("\\", "\\\\") + "\n")
            f.write(f"OutputBaseFilename=DriveManagerPro_Setup_{self.version}\n")
            f.write("Compression=lzma\n")
            f.write("SolidCompression=yes\n")
            f.write("PrivilegesRequired=lowest\n")
            f.write("PrivilegesRequiredOverridesAllowed=dialog\n")
            f.write("SetupIconFile=" + os.path.join(package_dir, "assets", "generated-icon.png").replace("\\", "\\\\") + "\n")
            f.write("\n[Languages]\n")
            f.write("Name: \"english\"; MessagesFile: \"compiler:Default.isl\"\n")
            f.write("\n[Tasks]\n")
            f.write("Name: \"desktopicon\"; Description: \"{cm:CreateDesktopIcon}\"; GroupDescription: \"{cm:AdditionalIcons}\"\n")
            f.write("\n[Files]\n")
            
            # Add all files in the package directory
            package_path = package_dir.replace("\\", "\\\\")
            f.write(f"Source: \"{package_path}\\*\"; DestDir: \"{{app}}\"; Flags: ignoreversion recursesubdirs createallsubdirs\n")
            
            f.write("\n[Icons]\n")
            f.write("Name: \"{group}\\Drive-Manager Pro\"; Filename: \"{app}\\DriveManagerPro.bat\"\n")
            f.write("Name: \"{commondesktop}\\Drive-Manager Pro\"; Filename: \"{app}\\DriveManagerPro.bat\"; Tasks: desktopicon\n")
            
            f.write("\n[Run]\n")
            f.write("Filename: \"{app}\\DriveManagerPro.bat\"; Description: \"{cm:LaunchProgram,Drive-Manager Pro}\"; Flags: nowait postinstall skipifsilent\n")
    
    def _build_with_inno_setup(self, script_path):
        """Build the installer using Inno Setup"""
        # Try to find Inno Setup compiler
        inno_compiler = None
        
        # Check default installation paths
        possible_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                inno_compiler = path
                break
        
        if not inno_compiler:
            return {
                "success": False,
                "error": "Inno Setup compiler not found"
            }
        
        try:
            result = subprocess.run([inno_compiler, script_path], 
                                 capture_output=True, text=True, check=True)
            
            # The output directory is specified in the script
            # Find the generated installer file (usually in the output_dir)
            installer_file = None
            for file in os.listdir(self.output_dir):
                if file.startswith("DriveManagerPro_Setup_") and file.endswith(".exe"):
                    installer_file = os.path.join(self.output_dir, file)
                    break
            
            if installer_file:
                return {
                    "success": True,
                    "installer_path": installer_file,
                    "installer_type": "exe",
                    "message": "Windows installer created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Installer was created but could not be located"
                }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Inno Setup compilation failed: {e.stderr}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running Inno Setup: {str(e)}"
            }
    
    def _create_zip_archive(self, package_dir, archive_name_prefix):
        """Create a ZIP archive of the package directory"""
        archive_path = os.path.join(self.output_dir, f"{archive_name_prefix}_{self.version}_{self.timestamp}.zip")
        
        try:
            shutil.make_archive(
                os.path.splitext(archive_path)[0],  # Remove .zip extension
                'zip',
                os.path.dirname(package_dir),
                os.path.basename(package_dir)
            )
            
            return {
                "success": True,
                "installer_path": archive_path,
                "installer_type": "zip",
                "message": "ZIP archive created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create ZIP archive: {str(e)}"
            }
    
    def _create_tarball(self, package_dir, archive_name_prefix):
        """Create a tar.gz archive of the package directory"""
        archive_path = os.path.join(self.output_dir, f"{archive_name_prefix}_{self.version}_{self.timestamp}.tar.gz")
        
        try:
            shutil.make_archive(
                os.path.splitext(os.path.splitext(archive_path)[0])[0],  # Remove .tar.gz extension
                'gztar',
                os.path.dirname(package_dir),
                os.path.basename(package_dir)
            )
            
            return {
                "success": True,
                "installer_path": archive_path,
                "installer_type": "tar.gz",
                "message": "Tarball created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create tarball: {str(e)}"
            }
    
    def _create_dmg(self, package_dir):
        """Create a DMG image for macOS"""
        dmg_path = os.path.join(self.output_dir, f"DriveManagerPro_macOS_{self.version}_{self.timestamp}.dmg")
        
        try:
            # Check if hdiutil is available
            subprocess.run(["hdiutil", "--version"], capture_output=True, check=True)
            
            # Create the DMG
            subprocess.run([
                "hdiutil", "create", "-volname", "Drive-Manager Pro", 
                "-srcfolder", package_dir, "-ov", "-format", "UDZO", 
                dmg_path
            ], capture_output=True, check=True)
            
            return {
                "success": True,
                "installer_path": dmg_path,
                "installer_type": "dmg",
                "message": "DMG image created successfully"
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to create DMG: {e.stderr.decode('utf-8')}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create DMG: {str(e)}"
            }
    
    def _create_deb_package(self, package_dir):
        """Create a Debian package for Linux"""
        # Create the DEBIAN directory structure
        debian_dir = os.path.join(package_dir, "DEBIAN")
        os.makedirs(debian_dir, exist_ok=True)
        
        # Create the control file
        control_path = os.path.join(debian_dir, "control")
        with open(control_path, "w") as f:
            f.write("Package: drivemanagerpro\n")
            f.write(f"Version: {self.version}\n")
            f.write("Section: utils\n")
            f.write("Priority: optional\n")
            f.write("Architecture: all\n")
            f.write("Depends: python3 (>= 3.9), python3-venv, python3-pip\n")
            f.write("Maintainer: Example Organization <info@example.com>\n")
            f.write("Description: Advanced file management with AI capabilities\n")
            f.write(" Drive-Manager Pro is a cross-platform file management application\n")
            f.write(" leveraging advanced AI technologies for intelligent file organization,\n")
            f.write(" recommendation, and interaction.\n")
        
        # Create the postinst script
        postinst_path = os.path.join(debian_dir, "postinst")
        with open(postinst_path, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("set -e\n\n")
            f.write("# Make the launcher executable\n")
            f.write("chmod +x /usr/share/drivemanagerpro/bin/drivemanagerpro\n\n")
            f.write("# Create a symbolic link in /usr/bin\n")
            f.write("ln -sf /usr/share/drivemanagerpro/bin/drivemanagerpro /usr/bin/drivemanagerpro\n\n")
            f.write("# Create the desktop file\n")
            f.write("cat > /usr/share/applications/drivemanagerpro.desktop << EOF\n")
            f.write("[Desktop Entry]\n")
            f.write("Name=Drive-Manager Pro\n")
            f.write("Comment=Advanced file management with AI capabilities\n")
            f.write("Exec=drivemanagerpro\n")
            f.write("Terminal=false\n")
            f.write("Type=Application\n")
            f.write("Categories=Utility;FileManager;\n")
            f.write("Icon=/usr/share/drivemanagerpro/assets/generated-icon.png\n")
            f.write("EOF\n\n")
            f.write("exit 0\n")
        
        # Make the postinst script executable
        os.chmod(postinst_path, 0o755)
        
        # Create the prerm script
        prerm_path = os.path.join(debian_dir, "prerm")
        with open(prerm_path, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("set -e\n\n")
            f.write("# Remove symbolic link\n")
            f.write("rm -f /usr/bin/drivemanagerpro\n\n")
            f.write("# Remove the desktop file\n")
            f.write("rm -f /usr/share/applications/drivemanagerpro.desktop\n\n")
            f.write("exit 0\n")
        
        # Make the prerm script executable
        os.chmod(prerm_path, 0o755)
        
        # Create the directories structure for Debian packaging
        usr_share_dir = os.path.join(package_dir, "usr", "share", "drivemanagerpro")
        os.makedirs(usr_share_dir, exist_ok=True)
        
        # Move files to the correct location
        for item in os.listdir(package_dir):
            if item not in ["DEBIAN", "usr"]:
                src_path = os.path.join(package_dir, item)
                dst_path = os.path.join(usr_share_dir, item)
                if os.path.exists(dst_path):
                    if os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    else:
                        os.remove(dst_path)
                shutil.move(src_path, dst_path)
        
        # Build the deb package
        deb_path = os.path.join(self.output_dir, f"drivemanagerpro_{self.version}_{self.timestamp}.deb")
        
        try:
            # Check if dpkg-deb is available
            subprocess.run(["dpkg-deb", "--version"], capture_output=True, check=True)
            
            # Build the package
            subprocess.run([
                "dpkg-deb", "--build", "--root-owner-group", 
                package_dir, deb_path
            ], capture_output=True, check=True)
            
            return {
                "success": True,
                "installer_path": deb_path,
                "installer_type": "deb",
                "message": "Debian package created successfully"
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to create Debian package: {e.stderr.decode('utf-8')}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Debian package: {str(e)}"
            }
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Failed to clean up temporary directory: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Drive-Manager Pro Installer Builder")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], default=platform.system().lower(),
                      help="Target platform for the installer")
    parser.add_argument("--output-dir", default=os.path.join(os.getcwd(), "dist"),
                      help="Output directory for the installer")
    parser.add_argument("--version", default="1.0.0",
                      help="Version number for the installer")
    
    args = parser.parse_args()
    
    if args.platform == "darwin":
        args.platform = "macos"
    
    if args.platform == "all":
        platforms = ["windows", "macos", "linux"]
    else:
        platforms = [args.platform]
    
    results = {}
    
    for platform_name in platforms:
        print(f"Building installer for {platform_name}...")
        builder = InstallerBuilder(platform_name, args.output_dir, args.version)
        result = builder.build_installer()
        builder.cleanup()
        
        results[platform_name] = result
        
        if result.get("success"):
            print(f"✓ {platform_name}: {result.get('message')}")
            print(f"  Installer path: {result.get('installer_path')}")
        else:
            print(f"✗ {platform_name}: {result.get('error')}")
    
    print("\nSummary:")
    for platform_name, result in results.items():
        if result.get("success"):
            print(f"✓ {platform_name}: {result.get('installer_type')} created at {result.get('installer_path')}")
        else:
            print(f"✗ {platform_name}: Failed - {result.get('error')}")


if __name__ == "__main__":
    main()