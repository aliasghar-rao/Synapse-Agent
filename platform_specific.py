"""
Platform-specific optimizations for Drive-Manager Pro.
Provides custom implementations for Windows, Linux, macOS, and Android.
"""

import os
import platform
import shutil
import json
import sys
import subprocess
import tempfile
import re
from datetime import datetime

class PlatformOptimizer:
    """Handles platform-specific optimizations for Drive-Manager Pro"""
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.temp_dir = tempfile.gettempdir()
        self.cache_dir = self._get_cache_dir()
        
    def _detect_platform(self):
        """Detect current platform with detailed information"""
        system = platform.system().lower()
        
        if system == 'windows':
            version = platform.version()
            release = platform.release()
            return {
                'os': 'windows',
                'version': version,
                'release': release,
                'name': f"Windows {release}",
                'is_windows': True,
                'is_linux': False,
                'is_macos': False,
                'is_android': False
            }
        elif system == 'darwin':
            version = platform.mac_ver()[0]
            return {
                'os': 'macos',
                'version': version,
                'name': f"macOS {version}",
                'is_windows': False,
                'is_linux': False,
                'is_macos': True,
                'is_android': False
            }
        elif system == 'linux':
            # Try to detect if running on Android
            if self._check_android():
                return {
                    'os': 'android',
                    'version': self._get_android_version(),
                    'name': f"Android {self._get_android_version()}",
                    'is_windows': False,
                    'is_linux': False,
                    'is_macos': False,
                    'is_android': True
                }
            else:
                # Try to get Linux distribution details
                try:
                    if os.path.exists('/etc/os-release'):
                        with open('/etc/os-release', 'r') as f:
                            lines = f.readlines()
                            info = {}
                            for line in lines:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    info[key] = value.strip('"')
                        
                        distro = info.get('ID', 'linux')
                        version = info.get('VERSION_ID', '')
                        name = info.get('PRETTY_NAME', f'Linux {distro} {version}')
                    else:
                        distro = 'linux'
                        version = platform.release()
                        name = f"Linux {version}"
                        
                    return {
                        'os': 'linux',
                        'distro': distro,
                        'version': version,
                        'name': name,
                        'is_windows': False,
                        'is_linux': True,
                        'is_macos': False,
                        'is_android': False
                    }
                except Exception:
                    # Fallback if detection fails
                    return {
                        'os': 'linux',
                        'version': platform.release(),
                        'name': f"Linux {platform.release()}",
                        'is_windows': False,
                        'is_linux': True,
                        'is_macos': False,
                        'is_android': False
                    }
        else:
            # Unknown platform
            return {
                'os': 'unknown',
                'version': '',
                'name': "Unknown OS",
                'is_windows': False,
                'is_linux': False,
                'is_macos': False,
                'is_android': False
            }
    
    def _check_android(self):
        """Check if running on Android"""
        # Method 1: Check for standard Android system directories
        android_paths = ['/system/app/', '/data/data/', '/storage/emulated/0/Android/']
        path_check = any(os.path.exists(path) for path in android_paths)
        
        # Method 2: Check for properties command (Android-specific)
        try:
            result = subprocess.run(['getprop', 'ro.build.version.release'], 
                                  capture_output=True, text=True, timeout=1)
            prop_check = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            prop_check = False
            
        return path_check or prop_check
    
    def _get_android_version(self):
        """Get Android version if running on Android"""
        try:
            result = subprocess.run(['getprop', 'ro.build.version.release'], 
                                  capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"
    
    def _get_cache_dir(self):
        """Get the appropriate cache directory for the current platform"""
        if self.platform['is_windows']:
            if 'LOCALAPPDATA' in os.environ:
                return os.path.join(os.environ['LOCALAPPDATA'], 'DriveManagerPro', 'Cache')
            else:
                return os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'DriveManagerPro', 'Cache')
        elif self.platform['is_macos']:
            return os.path.join(os.path.expanduser('~'), 'Library', 'Caches', 'DriveManagerPro')
        elif self.platform['is_android']:
            return "/storage/emulated/0/Android/data/com.example.drivemanagerpro/cache"
        else:  # Linux and others
            cache_dir = os.environ.get('XDG_CACHE_HOME')
            if not cache_dir:
                cache_dir = os.path.join(os.path.expanduser('~'), '.cache')
            return os.path.join(cache_dir, 'drivemanagerpro')
    
    def get_platform_info(self):
        """Get platform information"""
        return self.platform
    
    def get_system_directories(self):
        """Get system directories for the current platform"""
        directories = {}
        
        # Common directories for all platforms
        directories['home'] = os.path.expanduser('~')
        
        if self.platform['is_windows']:
            # Windows directories
            for env_var, dir_name in [
                ('USERPROFILE', 'user_profile'),
                ('APPDATA', 'app_data'),
                ('LOCALAPPDATA', 'local_app_data'),
                ('PROGRAMFILES', 'program_files'),
                ('PROGRAMFILES(X86)', 'program_files_x86'),
                ('WINDIR', 'windows'),
                ('SYSTEMROOT', 'system_root'),
                ('TEMP', 'temp')
            ]:
                if env_var in os.environ:
                    directories[dir_name] = os.environ[env_var]
            
            # User directories on Windows
            for dir_name in ['Documents', 'Pictures', 'Music', 'Videos', 'Downloads']:
                path = os.path.join(directories['user_profile'], dir_name)
                if os.path.exists(path):
                    directories[dir_name.lower()] = path
                    
        elif self.platform['is_macos']:
            # macOS directories
            base_dirs = {
                'documents': os.path.join(directories['home'], 'Documents'),
                'desktop': os.path.join(directories['home'], 'Desktop'),
                'downloads': os.path.join(directories['home'], 'Downloads'),
                'pictures': os.path.join(directories['home'], 'Pictures'),
                'music': os.path.join(directories['home'], 'Music'),
                'movies': os.path.join(directories['home'], 'Movies'),
                'applications': '/Applications',
                'library': os.path.join(directories['home'], 'Library'),
                'temp': self.temp_dir
            }
            
            for key, path in base_dirs.items():
                if os.path.exists(path):
                    directories[key] = path
                    
        elif self.platform['is_android']:
            # Android directories
            base_dirs = {
                'internal_storage': '/storage/emulated/0',
                'dcim': '/storage/emulated/0/DCIM',
                'pictures': '/storage/emulated/0/Pictures',
                'downloads': '/storage/emulated/0/Download',
                'music': '/storage/emulated/0/Music',
                'movies': '/storage/emulated/0/Movies',
                'documents': '/storage/emulated/0/Documents',
                'app_data': '/data/data/com.example.drivemanagerpro',
                'temp': self.temp_dir
            }
            
            for key, path in base_dirs.items():
                if os.path.exists(path):
                    directories[key] = path
                    
        else:  # Linux and others
            # Check for XDG directories
            xdg_vars = {
                'XDG_DESKTOP_DIR': 'desktop',
                'XDG_DOCUMENTS_DIR': 'documents',
                'XDG_DOWNLOAD_DIR': 'downloads',
                'XDG_MUSIC_DIR': 'music',
                'XDG_PICTURES_DIR': 'pictures',
                'XDG_PUBLICSHARE_DIR': 'public',
                'XDG_TEMPLATES_DIR': 'templates',
                'XDG_VIDEOS_DIR': 'videos',
                'XDG_CONFIG_HOME': 'config',
                'XDG_CACHE_HOME': 'cache',
                'XDG_DATA_HOME': 'data'
            }
            
            # Check environment variables first
            for env_var, dir_name in xdg_vars.items():
                if env_var in os.environ:
                    directories[dir_name] = os.environ[env_var]
            
            # Check common Linux directories
            for dir_name in ['Documents', 'Pictures', 'Music', 'Videos', 'Downloads']:
                path = os.path.join(directories['home'], dir_name)
                if os.path.exists(path) and dir_name.lower() not in directories:
                    directories[dir_name.lower()] = path
                    
            # Add other Linux-specific paths
            if os.path.exists('/usr/bin'):
                directories['bin'] = '/usr/bin'
            if os.path.exists('/usr/lib'):
                directories['lib'] = '/usr/lib'
            
            directories['temp'] = self.temp_dir
        
        return directories
    
    def create_optimized_file_operation(self, operation, source_path, destination_path=None):
        """Create an optimized file operation appropriate for the platform"""
        operations = {
            'copy': self._optimized_copy,
            'move': self._optimized_move,
            'delete': self._optimized_delete,
            'backup': self._optimized_backup
        }
        
        if operation not in operations:
            raise ValueError(f"Unsupported operation: {operation}")
            
        return operations[operation](source_path, destination_path)
    
    def _optimized_copy(self, source_path, destination_path):
        """Create an optimized copy operation based on platform"""
        operation = {
            'type': 'copy',
            'source': source_path,
            'destination': destination_path,
            'platform': self.platform['os'],
        }
        
        if self.platform['is_windows']:
            # For Windows, use FastCopy for large files if available
            if os.path.getsize(source_path) > 100 * 1024 * 1024:  # > 100MB
                operation['method'] = 'fastcopy'
                operation['command'] = f'fastcopy /cmd=diff /auto_close /force_close "/srcfile={source_path}" "/to={destination_path}"'
            else:
                operation['method'] = 'shutil'
                
        elif self.platform['is_macos']:
            # For macOS, use ditto for resource forks
            operation['method'] = 'ditto'
            operation['command'] = f'ditto "{source_path}" "{destination_path}"'
            
        elif self.platform['is_android']:
            # For Android, use standard copy but monitor battery
            operation['method'] = 'android'
            operation['monitor_battery'] = True
            
        else:  # Linux and others
            # For Linux, use rsync if available
            try:
                subprocess.run(['rsync', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                operation['method'] = 'rsync'
                operation['command'] = f'rsync -a --info=progress2 "{source_path}" "{destination_path}"'
            except (subprocess.SubprocessError, FileNotFoundError):
                operation['method'] = 'shutil'
                
        return operation
    
    def _optimized_move(self, source_path, destination_path):
        """Create an optimized move operation based on platform"""
        operation = {
            'type': 'move',
            'source': source_path,
            'destination': destination_path,
            'platform': self.platform['os'],
        }
        
        if self.platform['is_windows']:
            # For Windows, use FastCopy for large files if available
            if os.path.getsize(source_path) > 100 * 1024 * 1024:  # > 100MB
                operation['method'] = 'fastcopy'
                operation['command'] = f'fastcopy /cmd=move /auto_close /force_close "/srcfile={source_path}" "/to={destination_path}"'
            else:
                operation['method'] = 'shutil'
                
        elif self.platform['is_macos']:
            # For macOS, preserving resource forks
            operation['method'] = 'ditto+remove'
            operation['commands'] = [
                f'ditto "{source_path}" "{destination_path}"',
                f'rm -rf "{source_path}"'
            ]
            
        elif self.platform['is_android']:
            # For Android, check if on same filesystem first
            operation['method'] = 'android'
            operation['monitor_battery'] = True
            operation['check_storage'] = True
            
        else:  # Linux and others
            # For Linux, different approach for different filesystems
            source_stat = os.stat(source_path)
            dest_stat = os.stat(os.path.dirname(destination_path))
            
            if source_stat.st_dev == dest_stat.st_dev:
                # Same filesystem, can use rename
                operation['method'] = 'rename'
            else:
                # Different filesystem, copy and delete
                try:
                    subprocess.run(['rsync', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    operation['method'] = 'rsync+remove'
                    operation['commands'] = [
                        f'rsync -a --remove-source-files --info=progress2 "{source_path}" "{destination_path}"',
                        f'find "{os.path.dirname(source_path)}" -type d -empty -delete'
                    ]
                except (subprocess.SubprocessError, FileNotFoundError):
                    operation['method'] = 'shutil'
                
        return operation
    
    def _optimized_delete(self, source_path, destination_path=None):
        """Create an optimized delete operation based on platform"""
        operation = {
            'type': 'delete',
            'source': source_path,
            'platform': self.platform['os'],
        }
        
        if self.platform['is_windows']:
            # For Windows, use recycle bin if possible
            operation['method'] = 'recycle_bin'
            
            # Verify if it's a system file or not
            if os.path.isfile(source_path) and self._is_system_file_windows(source_path):
                operation['secure'] = True
                operation['warning'] = 'System file deletion requires elevation'
                
        elif self.platform['is_macos']:
            # For macOS, use Trash
            operation['method'] = 'trash'
            operation['command'] = f'osascript -e \'tell application "Finder" to delete POSIX file "{source_path}"\''
            
        elif self.platform['is_android']:
            # For Android, standard delete (no recycle bin)
            operation['method'] = 'remove'
            
        else:  # Linux and others
            # For Linux, try to use trash-cli if available
            try:
                subprocess.run(['trash', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                operation['method'] = 'trash-cli'
                operation['command'] = f'trash "{source_path}"'
            except (subprocess.SubprocessError, FileNotFoundError):
                operation['method'] = 'remove'
                
        return operation
    
    def _optimized_backup(self, source_path, destination_path):
        """Create an optimized backup operation based on platform"""
        operation = {
            'type': 'backup',
            'source': source_path,
            'destination': destination_path,
            'platform': self.platform['os'],
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        
        if self.platform['is_windows']:
            # For Windows, use robocopy for directories
            if os.path.isdir(source_path):
                operation['method'] = 'robocopy'
                operation['command'] = f'robocopy "{source_path}" "{destination_path}" /MIR /W:1 /R:1 /Z /FFT /MT:4'
            else:
                operation['method'] = 'shutil'
                
        elif self.platform['is_macos']:
            # For macOS, use ditto for resource forks
            operation['method'] = 'ditto'
            operation['command'] = f'ditto -X "{source_path}" "{destination_path}"'
            
        elif self.platform['is_android']:
            # For Android, use standard copy with timestamp
            operation['method'] = 'android_backup'
            operation['monitor_battery'] = True
            
        else:  # Linux and others
            # For Linux, use rsync with backup options
            try:
                subprocess.run(['rsync', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                operation['method'] = 'rsync'
                operation['command'] = f'rsync -a --info=progress2 --backup "{source_path}" "{destination_path}"'
            except (subprocess.SubprocessError, FileNotFoundError):
                operation['method'] = 'shutil'
                
        return operation
    
    def _is_system_file_windows(self, file_path):
        """Check if file is a system file on Windows"""
        try:
            import win32api
            import win32con
            attributes = win32api.GetFileAttributes(file_path)
            return bool(attributes & win32con.FILE_ATTRIBUTE_SYSTEM)
        except (ImportError, Exception):
            # Fallback to a simple check
            system_dirs = [
                os.environ.get('WINDIR', ''),
                os.path.join(os.environ.get('WINDIR', ''), 'system32'),
                os.path.join(os.environ.get('SYSTEMROOT', ''), 'system32')
            ]
            return any(dir in file_path for dir in system_dirs if dir)
            
    def optimize_apk_operations(self):
        """Get optimized APK operations for current platform"""
        apk_operations = {
            'install_command': None,
            'extract_command': None,
            'analyze_command': None,
            'package_manager': None,
        }
        
        if self.platform['is_windows']:
            # On Windows, we use platform-specific tools
            apk_operations['install_command'] = "adb install -r \"{apk_path}\""
            apk_operations['extract_command'] = "\"C:\\Program Files\\7-Zip\\7z.exe\" x \"{apk_path}\" -o\"{output_dir}\""
            apk_operations['analyze_command'] = "aapt dump badging \"{apk_path}\""
            apk_operations['package_manager'] = "windows"
            
        elif self.platform['is_macos']:
            # On macOS, similar to Linux but with platform-specific paths
            apk_operations['install_command'] = "adb install -r \"{apk_path}\""
            apk_operations['extract_command'] = "unzip -q \"{apk_path}\" -d \"{output_dir}\""
            apk_operations['analyze_command'] = "~/Library/Android/sdk/build-tools/*/aapt dump badging \"{apk_path}\""
            apk_operations['package_manager'] = "macos"
            
        elif self.platform['is_android']:
            # On Android, we can directly install APKs
            apk_operations['install_command'] = "pm install -r \"{apk_path}\""
            apk_operations['extract_command'] = "unzip -q \"{apk_path}\" -d \"{output_dir}\""
            apk_operations['analyze_command'] = "aapt dump badging \"{apk_path}\""
            apk_operations['package_manager'] = "android"
            
        else:  # Linux and others
            # On Linux, using standard tools
            apk_operations['install_command'] = "adb install -r \"{apk_path}\""
            apk_operations['extract_command'] = "unzip -q \"{apk_path}\" -d \"{output_dir}\""
            apk_operations['analyze_command'] = "aapt dump badging \"{apk_path}\""
            apk_operations['package_manager'] = "linux"
            
        return apk_operations
    
    def execute_platform_operation(self, operation):
        """Execute a platform-specific operation"""
        if operation['type'] == 'copy':
            return self._execute_copy_operation(operation)
        elif operation['type'] == 'move':
            return self._execute_move_operation(operation)
        elif operation['type'] == 'delete':
            return self._execute_delete_operation(operation)
        elif operation['type'] == 'backup':
            return self._execute_backup_operation(operation)
        else:
            raise ValueError(f"Unsupported operation type: {operation['type']}")
    
    def _execute_copy_operation(self, operation):
        """Execute a copy operation"""
        try:
            source_path = operation['source']
            destination_path = operation['destination']
            
            if operation['method'] == 'shutil':
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
                return {'success': True, 'message': f"Copied {source_path} to {destination_path}"}
                
            elif operation['method'] in ['fastcopy', 'ditto', 'rsync']:
                result = subprocess.run(operation['command'], shell=True, 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return {'success': True, 'message': f"Copied {source_path} to {destination_path}"}
                else:
                    return {'success': False, 'message': f"Error: {result.stderr}"}
                    
            elif operation['method'] == 'android':
                # Android-specific copy operation
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
                return {'success': True, 'message': f"Copied {source_path} to {destination_path}"}
                
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
    
    def _execute_move_operation(self, operation):
        """Execute a move operation"""
        try:
            source_path = operation['source']
            destination_path = operation['destination']
            
            if operation['method'] == 'shutil':
                shutil.move(source_path, destination_path)
                return {'success': True, 'message': f"Moved {source_path} to {destination_path}"}
                
            elif operation['method'] == 'rename':
                os.rename(source_path, destination_path)
                return {'success': True, 'message': f"Moved {source_path} to {destination_path}"}
                
            elif operation['method'] in ['fastcopy', 'rsync+remove']:
                if isinstance(operation.get('commands', []), list):
                    for command in operation['commands']:
                        result = subprocess.run(command, shell=True, 
                                             capture_output=True, text=True)
                        if result.returncode != 0:
                            return {'success': False, 'message': f"Error: {result.stderr}"}
                else:
                    result = subprocess.run(operation['command'], shell=True, 
                                         capture_output=True, text=True)
                    if result.returncode != 0:
                        return {'success': False, 'message': f"Error: {result.stderr}"}
                
                return {'success': True, 'message': f"Moved {source_path} to {destination_path}"}
                
            elif operation['method'] == 'ditto+remove':
                # macOS-specific move using ditto then remove
                for command in operation['commands']:
                    result = subprocess.run(command, shell=True, 
                                         capture_output=True, text=True)
                    if result.returncode != 0:
                        return {'success': False, 'message': f"Error: {result.stderr}"}
                
                return {'success': True, 'message': f"Moved {source_path} to {destination_path}"}
                
            elif operation['method'] == 'android':
                # Android-specific move operation
                shutil.move(source_path, destination_path)
                return {'success': True, 'message': f"Moved {source_path} to {destination_path}"}
                
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
    
    def _execute_delete_operation(self, operation):
        """Execute a delete operation"""
        try:
            source_path = operation['source']
            
            if operation['method'] == 'remove':
                if os.path.isdir(source_path):
                    shutil.rmtree(source_path)
                else:
                    os.remove(source_path)
                return {'success': True, 'message': f"Deleted {source_path}"}
                
            elif operation['method'] == 'recycle_bin':
                # Windows-specific recycle bin operation
                try:
                    import winshell
                    winshell.delete_file(source_path, no_confirm=True, allow_undo=True)
                    return {'success': True, 'message': f"Moved {source_path} to Recycle Bin"}
                except ImportError:
                    # Fallback if winshell is not available
                    if os.path.isdir(source_path):
                        shutil.rmtree(source_path)
                    else:
                        os.remove(source_path)
                    return {'success': True, 'message': f"Deleted {source_path}"}
                    
            elif operation['method'] == 'trash':
                # macOS-specific trash operation
                result = subprocess.run(operation['command'], shell=True, 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return {'success': True, 'message': f"Moved {source_path} to Trash"}
                else:
                    return {'success': False, 'message': f"Error: {result.stderr}"}
                    
            elif operation['method'] == 'trash-cli':
                # Linux-specific trash operation
                result = subprocess.run(operation['command'], shell=True, 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return {'success': True, 'message': f"Moved {source_path} to Trash"}
                else:
                    return {'success': False, 'message': f"Error: {result.stderr}"}
                
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
    
    def _execute_backup_operation(self, operation):
        """Execute a backup operation"""
        try:
            source_path = operation['source']
            destination_path = operation['destination']
            
            if operation['method'] == 'shutil':
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
                return {'success': True, 'message': f"Backed up {source_path} to {destination_path}"}
                
            elif operation['method'] in ['robocopy', 'ditto', 'rsync']:
                result = subprocess.run(operation['command'], shell=True, 
                                     capture_output=True, text=True)
                if result.returncode == 0 or (operation['method'] == 'robocopy' and result.returncode <= 3):
                    return {'success': True, 'message': f"Backed up {source_path} to {destination_path}"}
                else:
                    return {'success': False, 'message': f"Error: {result.stderr}"}
                    
            elif operation['method'] == 'android_backup':
                # Android-specific backup operation
                timestamped_dest = f"{destination_path}_{operation['timestamp']}"
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, timestamped_dest)
                else:
                    shutil.copy2(source_path, timestamped_dest)
                return {'success': True, 'message': f"Backed up {source_path} to {timestamped_dest}"}
                
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
    
    def extract_apk_info(self, apk_path):
        """Extract information from an APK file using platform-specific tools"""
        apk_info = {
            'package_name': None,
            'version_name': None,
            'version_code': None,
            'sdk_min': None,
            'sdk_target': None,
            'permissions': [],
            'activities': [],
            'services': [],
            'receivers': [],
            'providers': []
        }
        
        try:
            # Get operations for current platform
            apk_operations = self.optimize_apk_operations()
            analyze_command = apk_operations['analyze_command'].format(apk_path=apk_path)
            
            # Run the command
            result = subprocess.run(analyze_command, shell=True, 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Extract basic info
                package_match = re.search(r"package: name='([^']+)'", output)
                if package_match:
                    apk_info['package_name'] = package_match.group(1)
                
                version_name_match = re.search(r"versionName='([^']+)'", output)
                if version_name_match:
                    apk_info['version_name'] = version_name_match.group(1)
                
                version_code_match = re.search(r"versionCode='(\d+)'", output)
                if version_code_match:
                    apk_info['version_code'] = version_code_match.group(1)
                
                # SDK versions
                sdk_min_match = re.search(r"sdkVersion:'(\d+)'", output)
                if sdk_min_match:
                    apk_info['sdk_min'] = sdk_min_match.group(1)
                    
                sdk_target_match = re.search(r"targetSdkVersion:'(\d+)'", output)
                if sdk_target_match:
                    apk_info['sdk_target'] = sdk_target_match.group(1)
                
                # Extract permissions
                permission_matches = re.finditer(r"uses-permission: name='([^']+)'", output)
                for match in permission_matches:
                    apk_info['permissions'].append(match.group(1))
                
                return apk_info
            else:
                # If the analysis command fails, try extracting the APK and reading AndroidManifest.xml
                return self._extract_apk_manifest(apk_path)
                
        except Exception as e:
            print(f"Error analyzing APK: {e}")
            return apk_info
    
    def _extract_apk_manifest(self, apk_path):
        """Extract APK manifest by unpacking the APK file"""
        apk_info = {
            'package_name': None,
            'version_name': None,
            'version_code': None,
            'sdk_min': None,
            'sdk_target': None,
            'permissions': [],
            'activities': [],
            'services': [],
            'receivers': [],
            'providers': []
        }
        
        try:
            # Create a temporary directory for extraction
            temp_dir = os.path.join(self.temp_dir, f"apk_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Get extract command for current platform
            apk_operations = self.optimize_apk_operations()
            extract_command = apk_operations['extract_command'].format(
                apk_path=apk_path, output_dir=temp_dir
            )
            
            # Run the extraction command
            result = subprocess.run(extract_command, shell=True, 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                # Look for AndroidManifest.xml
                manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
                if os.path.exists(manifest_path):
                    # In a real implementation, we would parse the binary XML format
                    # For this demo, we'll return basic information
                    apk_info['package_name'] = os.path.basename(apk_path).split('.apk')[0]
                    apk_info['version_name'] = "1.0"
                    apk_info['version_code'] = "1"
            
            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return apk_info
            
        except Exception as e:
            print(f"Error extracting APK manifest: {e}")
            return apk_info
    
    def install_apk(self, apk_path):
        """Install an APK file using platform-specific tools"""
        try:
            # Get operations for current platform
            apk_operations = self.optimize_apk_operations()
            install_command = apk_operations['install_command'].format(apk_path=apk_path)
            
            # Run the command
            result = subprocess.run(install_command, shell=True, 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True, 
                    'message': f"Successfully installed {os.path.basename(apk_path)}"
                }
            else:
                return {
                    'success': False, 
                    'message': f"Failed to install APK: {result.stderr}"
                }
                
        except Exception as e:
            return {'success': False, 'message': f"Error installing APK: {str(e)}"}


# Create an instance
platform_optimizer = PlatformOptimizer()