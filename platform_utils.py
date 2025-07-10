"""
Platform-specific utilities for Drive-Manager Pro.
Handles detection of OS and customizes behavior accordingly.
"""

import os
import sys
import platform


def get_platform():
    """Identify the current operating system."""
    system = platform.system().lower()
    
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        # Could add more specific detection for Linux distributions
        return 'linux'
    elif system == 'android':
        # Note: This is a simple check and might not always work
        # More robust Android detection would be needed in production
        return 'android' 
    else:
        return 'unknown'


def get_home_directory():
    """Get the user's home directory."""
    return os.path.expanduser('~')


def get_default_directories():
    """Get platform-specific default directories."""
    home = get_home_directory()
    platform_name = get_platform()
    
    # Default structure that works for most platforms
    dirs = {
        'documents': os.path.join(home, 'Documents'),
        'downloads': os.path.join(home, 'Downloads'),
        'pictures': os.path.join(home, 'Pictures'),
        'music': os.path.join(home, 'Music'),
        'videos': os.path.join(home, 'Videos')
    }
    
    # Platform-specific overrides
    if platform_name == 'windows':
        # Windows often has Documents, not Document
        dirs = {
            'documents': os.path.join(home, 'Documents'),
            'downloads': os.path.join(home, 'Downloads'),
            'pictures': os.path.join(home, 'Pictures'),
            'music': os.path.join(home, 'Music'),
            'videos': os.path.join(home, 'Videos')
        }
    elif platform_name == 'macos':
        # macOS uses capitalized folder names
        dirs = {
            'documents': os.path.join(home, 'Documents'),
            'downloads': os.path.join(home, 'Downloads'),
            'pictures': os.path.join(home, 'Pictures'),
            'music': os.path.join(home, 'Music'),
            'videos': os.path.join(home, 'Movies')  # Note: Movies, not Videos
        }
    elif platform_name == 'linux':
        # Linux distributions might use lowercase or XDG folders
        # Checking if XDG directories are defined
        xdg_documents = os.environ.get('XDG_DOCUMENTS_DIR')
        xdg_downloads = os.environ.get('XDG_DOWNLOAD_DIR')
        xdg_pictures = os.environ.get('XDG_PICTURES_DIR')
        xdg_music = os.environ.get('XDG_MUSIC_DIR')
        xdg_videos = os.environ.get('XDG_VIDEOS_DIR')
        
        dirs = {
            'documents': xdg_documents if xdg_documents else os.path.join(home, 'Documents'),
            'downloads': xdg_downloads if xdg_downloads else os.path.join(home, 'Downloads'),
            'pictures': xdg_pictures if xdg_pictures else os.path.join(home, 'Pictures'),
            'music': xdg_music if xdg_music else os.path.join(home, 'Music'),
            'videos': xdg_videos if xdg_videos else os.path.join(home, 'Videos')
        }
    elif platform_name == 'android':
        # For Android, these directories might need special handling
        # This is a placeholder implementation
        dirs = {
            'documents': '/sdcard/Documents',
            'downloads': '/sdcard/Download',
            'pictures': '/sdcard/Pictures',
            'music': '/sdcard/Music',
            'videos': '/sdcard/Movies'
        }
    
    # Verify directories exist and are accessible
    for key, path in dirs.items():
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                # If we can't create it, default to home
                dirs[key] = home
    
    return dirs


def get_platform_style():
    """Get platform-specific styling considerations."""
    platform_name = get_platform()
    
    if platform_name == 'windows':
        return {
            'style': 'Fluent',
            'font_family': 'Segoe UI',
            'border_radius': '4px'
        }
    elif platform_name == 'macos':
        return {
            'style': 'Aqua',
            'font_family': 'San Francisco',
            'border_radius': '6px'
        }
    elif platform_name == 'linux':
        return {
            'style': 'Breeze',  # KDE's default style
            'font_family': 'Noto Sans',
            'border_radius': '3px'
        }
    elif platform_name == 'android':
        return {
            'style': 'Material',
            'font_family': 'Roboto',
            'border_radius': '8px'
        }
    else:
        return {
            'style': 'Generic',
            'font_family': 'Arial',
            'border_radius': '4px'
        }


def is_touch_device():
    """Detect if running on a touch-enabled device."""
    platform_name = get_platform()
    if platform_name == 'android':
        return True
    
    # This is a simple heuristic and would need better detection in production
    return False


def get_screen_dimensions():
    """Get the screen dimensions for responsive design."""
    try:
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            size = screen.size()
            return size.width(), size.height()
    except:
        # Fallback to a reasonable default if we can't detect
        return 1280, 800
