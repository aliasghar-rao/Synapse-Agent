"""
Configuration settings for Drive-Manager Pro.
Contains color schemes, layout settings, and other configuration parameters.
"""

# Color Scheme
COLORS = {
    # Primary colors
    'primary': '#0078D7',  # Blue for apps, buttons, AI
    
    # Secondary colors
    'files': '#2ECC71',     # Green for files
    'tools': '#9B59B6',     # Purple for tools
    'cloud': '#E67E22',     # Orange for cloud
    
    # Backgrounds
    'mind_map_bg': '#2A2D3E',  # Dark mind map background
    'section_bg': '#FFFFFF',    # White for panels
    'main_bg': '#F5F6FA',       # Light main background
    
    # Additional UI colors
    'text': '#333333',
    'light_text': '#666666',
    'border': '#DDDDDD',
    'highlight': '#3498DB',
    'hover': '#E0E7FF',
    'selected': '#D0E8FF',
    'warning': '#F39C12',
    'error': '#E74C3C',
    'success': '#27AE60'
}

# Layout settings
LAYOUT = {
    'mind_map_height_ratio': 0.25,  # 25% of the screen height
    'panel_count': 3,               # Three vertical panels in the top section
}

# Mind map settings
MIND_MAP = {
    'node_size': {
        'file': 15,
        'app': 20,
        'tag': 10
    },
    'edge_width': 1.5,
    'animation_duration': 300,  # ms
    'default_zoom': 1.0
}

# Application identification
APP_NAME = "Drive-Manager Pro"
APP_VERSION = "0.1.0"

# Default paths for common directories across platforms
DEFAULT_DIRS = {
    'documents': None,  # Will be set dynamically based on platform
    'downloads': None,
    'pictures': None,
    'music': None,
    'videos': None
}
