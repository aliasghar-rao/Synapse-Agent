"""
UI Extractor module for Drive-Manager Pro.
Extracts UI designs from existing applications and applies them to new projects.
"""

import os
import json
import shutil
import zipfile
import tempfile
import subprocess
import platform
import re
from datetime import datetime
import xml.etree.ElementTree as ET

# Optional imports - will be used if available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class UIComponentType:
    """Enumeration of UI component types"""
    BUTTON = "button"
    TEXT_FIELD = "text_field"
    LABEL = "label"
    IMAGE = "image"
    LAYOUT = "layout"
    NAVIGATION = "navigation"
    MENU = "menu"
    LIST = "list"
    GRID = "grid"
    DIALOG = "dialog"
    TAB = "tab"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    SLIDER = "slider"
    PROGRESS = "progress"
    CARD = "card"
    UNKNOWN = "unknown"


class UIStyle:
    """Class for UI style information"""
    
    def __init__(self):
        self.colors = {
            'primary': "#1976D2",
            'secondary': "#424242",
            'accent': "#FF4081",
            'background': "#FFFFFF",
            'surface': "#FFFFFF",
            'error': "#F44336",
            'text_primary': "#212121",
            'text_secondary': "#757575"
        }
        
        self.typography = {
            'font_family': "Roboto, Arial, sans-serif",
            'h1': {'size': '24px', 'weight': 'bold'},
            'h2': {'size': '20px', 'weight': 'bold'},
            'h3': {'size': '18px', 'weight': 'bold'},
            'body1': {'size': '16px', 'weight': 'normal'},
            'body2': {'size': '14px', 'weight': 'normal'},
            'button': {'size': '14px', 'weight': 'medium', 'transform': 'uppercase'},
            'caption': {'size': '12px', 'weight': 'normal'}
        }
        
        self.dimensions = {
            'padding': '16px',
            'margin': '8px',
            'border_radius': '4px',
            'icon_size': '24px',
            'button_height': '36px',
            'input_height': '40px'
        }
        
        self.animations = {
            'transition_duration': '0.3s',
            'transition_timing': 'ease'
        }


class UIComponent:
    """Class representing a UI component from an application"""
    
    def __init__(self, component_type, properties=None):
        self.component_type = component_type
        self.properties = properties or {}
        self.children = []
        self.id = self.properties.get('id', '')
        self.style = {}
    
    def add_child(self, component):
        """Add a child component"""
        self.children.append(component)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'type': self.component_type,
            'id': self.id,
            'properties': self.properties,
            'style': self.style,
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create component from dictionary"""
        component = cls(data['type'], data['properties'])
        component.id = data['id']
        component.style = data['style']
        
        for child_data in data.get('children', []):
            child = UIComponent.from_dict(child_data)
            component.add_child(child)
        
        return component


class UITemplate:
    """Class representing a complete UI template"""
    
    def __init__(self, name, description=''):
        self.name = name
        self.description = description
        self.style = UIStyle()
        self.screens = {}  # Map of screen name to root component
        self.navigation = {}  # Navigation structure between screens
        self.assets = {}  # Dict of asset paths
        self.metadata = {
            'created': datetime.now().isoformat(),
            'source': '',
            'platform': '',
            'tags': []
        }
    
    def add_screen(self, screen_name, root_component):
        """Add a screen to the template"""
        self.screens[screen_name] = root_component
    
    def set_navigation(self, navigation_structure):
        """Set the navigation structure between screens"""
        self.navigation = navigation_structure
    
    def add_asset(self, asset_name, asset_path):
        """Add an asset to the template"""
        self.assets[asset_name] = asset_path
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'style': {
                'colors': self.style.colors,
                'typography': self.style.typography,
                'dimensions': self.style.dimensions,
                'animations': self.style.animations
            },
            'screens': {
                name: component.to_dict() for name, component in self.screens.items()
            },
            'navigation': self.navigation,
            'assets': self.assets,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create template from dictionary"""
        template = cls(data['name'], data['description'])
        
        # Set style
        template.style.colors = data['style']['colors']
        template.style.typography = data['style']['typography']
        template.style.dimensions = data['style']['dimensions']
        template.style.animations = data['style']['animations']
        
        # Set screens
        for name, screen_data in data['screens'].items():
            template.screens[name] = UIComponent.from_dict(screen_data)
        
        # Set navigation
        template.navigation = data['navigation']
        
        # Set assets
        template.assets = data['assets']
        
        # Set metadata
        template.metadata = data['metadata']
        
        return template


class UIExtractor:
    """Class for extracting UI from applications"""
    
    def __init__(self, cache_dir=None):
        """Initialize the UI extractor with optional cache directory"""
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), 'drivemanager_ui_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Platform detection
        self.platform = platform.system().lower()
    
    def extract_from_android_apk(self, apk_path):
        """Extract UI design from an Android APK"""
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file does not exist'}
        
        try:
            # Create a temporary directory for extraction
            extraction_dir = tempfile.mkdtemp(prefix='ui_extraction_')
            
            # Extract the APK
            with zipfile.ZipFile(apk_path, 'r') as z:
                z.extractall(extraction_dir)
            
            # Extract APK information for metadata
            apk_name = os.path.basename(apk_path)
            package_name = self._extract_package_name(extraction_dir)
            
            # Create UI template with basic info
            template = UITemplate(
                name=f"UI from {apk_name}",
                description=f"UI extracted from {package_name if package_name else apk_name}"
            )
            
            # Set metadata
            template.metadata['source'] = apk_path
            template.metadata['platform'] = 'android'
            template.metadata['extracted_date'] = datetime.now().isoformat()
            if package_name:
                template.metadata['package_name'] = package_name
            
            # Extract color scheme
            colors = self._extract_android_colors(extraction_dir)
            if colors:
                template.style.colors.update(colors)
            
            # Extract dimensions
            dimensions = self._extract_android_dimensions(extraction_dir)
            if dimensions:
                template.style.dimensions.update(dimensions)
            
            # Extract layouts
            screens = self._extract_android_layouts(extraction_dir)
            for screen_name, component in screens.items():
                template.add_screen(screen_name, component)
            
            # Extract assets
            assets_dir = os.path.join(self.cache_dir, f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(assets_dir, exist_ok=True)
            
            # Copy drawable resources
            assets = {}
            drawable_dirs = [d for d in os.listdir(extraction_dir) if os.path.isdir(os.path.join(extraction_dir, d)) and 'drawable' in d]
            
            for drawable_dir in drawable_dirs:
                drawable_path = os.path.join(extraction_dir, drawable_dir)
                for file in os.listdir(drawable_path):
                    if file.endswith(('.png', '.jpg', '.gif')):
                        src_path = os.path.join(drawable_path, file)
                        dst_path = os.path.join(assets_dir, file)
                        shutil.copy2(src_path, dst_path)
                        assets[file] = dst_path
            
            template.assets = assets
            
            # Create a template export
            result_path = self._export_template(template)
            
            # Clean up extraction directory
            shutil.rmtree(extraction_dir, ignore_errors=True)
            
            return {
                'success': True,
                'template': template,
                'template_path': result_path,
                'assets_path': assets_dir,
                'message': f"UI design extracted from {apk_name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_from_screenshots(self, screenshot_paths, application_name):
        """Extract UI design from application screenshots"""
        if not screenshot_paths:
            return {'success': False, 'error': 'No screenshots provided'}
        
        for path in screenshot_paths:
            if not os.path.exists(path):
                return {'success': False, 'error': f'Screenshot does not exist: {path}'}
        
        if not CV2_AVAILABLE:
            return {'success': False, 'error': 'OpenCV is required for screenshot analysis'}
        
        try:
            # Create UI template with basic info
            template = UITemplate(
                name=f"UI from {application_name}",
                description=f"UI extracted from {application_name} screenshots"
            )
            
            # Set metadata
            template.metadata['source'] = 'screenshots'
            template.metadata['platform'] = 'unknown'
            template.metadata['extracted_date'] = datetime.now().isoformat()
            template.metadata['screenshot_count'] = len(screenshot_paths)
            
            # Extract color scheme using computer vision
            extracted_colors = self._extract_colors_from_screenshots(screenshot_paths)
            template.style.colors.update(extracted_colors)
            
            # Extract UI components using computer vision
            screens = {}
            
            for i, screenshot_path in enumerate(screenshot_paths):
                screen_name = f"Screen_{i+1}"
                component = self._extract_components_from_screenshot(screenshot_path)
                screens[screen_name] = component
            
            for screen_name, component in screens.items():
                template.add_screen(screen_name, component)
            
            # Copy screenshot assets
            assets_dir = os.path.join(self.cache_dir, f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(assets_dir, exist_ok=True)
            
            assets = {}
            for i, screenshot_path in enumerate(screenshot_paths):
                dst_path = os.path.join(assets_dir, f"screenshot_{i+1}{os.path.splitext(screenshot_path)[1]}")
                shutil.copy2(screenshot_path, dst_path)
                assets[f"screenshot_{i+1}"] = dst_path
            
            template.assets = assets
            
            # Create a template export
            result_path = self._export_template(template)
            
            return {
                'success': True,
                'template': template,
                'template_path': result_path,
                'assets_path': assets_dir,
                'message': f"UI design extracted from {application_name} screenshots"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_from_website(self, url):
        """Extract UI design from a website"""
        try:
            # Extract website content using browser automation
            # This would normally require a browser automation library like Selenium
            # For this demo, we'll create a simplified version
            
            # Create a temporary directory for screenshots
            screenshot_dir = tempfile.mkdtemp(prefix='website_screenshots_')
            
            # In a real implementation, we would:
            # 1. Use Selenium to open the website
            # 2. Take screenshots of different pages
            # 3. Extract CSS styles
            
            # For now, create a mock template
            template = UITemplate(
                name=f"UI from {url}",
                description=f"UI extracted from website {url}"
            )
            
            # Set metadata
            template.metadata['source'] = url
            template.metadata['platform'] = 'web'
            template.metadata['extracted_date'] = datetime.now().isoformat()
            
            # Create a basic structure with common web components
            home_screen = UIComponent(UIComponentType.LAYOUT, {'id': 'home_screen'})
            
            # Header
            header = UIComponent(UIComponentType.LAYOUT, {'id': 'header'})
            header.style = {'height': '60px', 'background': '#333333'}
            
            logo = UIComponent(UIComponentType.IMAGE, {'id': 'logo'})
            logo.style = {'width': '120px', 'height': '40px'}
            header.add_child(logo)
            
            menu = UIComponent(UIComponentType.NAVIGATION, {'id': 'main_menu'})
            for item in ['Home', 'Products', 'Services', 'About', 'Contact']:
                menu_item = UIComponent(UIComponentType.BUTTON, {'id': f'menu_{item.lower()}', 'text': item})
                menu.add_child(menu_item)
            header.add_child(menu)
            
            home_screen.add_child(header)
            
            # Hero section
            hero = UIComponent(UIComponentType.LAYOUT, {'id': 'hero'})
            hero.style = {'height': '400px', 'background': '#f5f5f5'}
            
            hero_title = UIComponent(UIComponentType.LABEL, {'id': 'hero_title', 'text': 'Welcome to Our Website'})
            hero_title.style = {'font-size': '32px', 'color': '#333333'}
            hero.add_child(hero_title)
            
            hero_subtitle = UIComponent(UIComponentType.LABEL, {'id': 'hero_subtitle', 'text': 'Discover our amazing products and services'})
            hero_subtitle.style = {'font-size': '18px', 'color': '#666666'}
            hero.add_child(hero_subtitle)
            
            cta_button = UIComponent(UIComponentType.BUTTON, {'id': 'cta_button', 'text': 'Get Started'})
            cta_button.style = {'background': '#1976D2', 'color': '#FFFFFF', 'padding': '12px 24px'}
            hero.add_child(cta_button)
            
            home_screen.add_child(hero)
            
            # Features section
            features = UIComponent(UIComponentType.LAYOUT, {'id': 'features'})
            features.style = {'padding': '40px 0'}
            
            for i in range(3):
                feature = UIComponent(UIComponentType.CARD, {'id': f'feature_{i+1}'})
                feature.style = {'width': '30%', 'margin': '0 1.5%'}
                
                feature_title = UIComponent(UIComponentType.LABEL, {'id': f'feature_{i+1}_title', 'text': f'Feature {i+1}'})
                feature_title.style = {'font-size': '24px', 'color': '#333333'}
                feature.add_child(feature_title)
                
                feature_desc = UIComponent(UIComponentType.LABEL, {'id': f'feature_{i+1}_desc', 'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'})
                feature_desc.style = {'font-size': '16px', 'color': '#666666'}
                feature.add_child(feature_desc)
                
                features.add_child(feature)
            
            home_screen.add_child(features)
            
            # Footer
            footer = UIComponent(UIComponentType.LAYOUT, {'id': 'footer'})
            footer.style = {'height': '60px', 'background': '#333333', 'color': '#FFFFFF'}
            
            copyright = UIComponent(UIComponentType.LABEL, {'id': 'copyright', 'text': '© 2025 Company Name. All rights reserved.'})
            footer.add_child(copyright)
            
            home_screen.add_child(footer)
            
            # Add the screen to the template
            template.add_screen('home', home_screen)
            
            # Create a contact page as a second screen
            contact_screen = UIComponent(UIComponentType.LAYOUT, {'id': 'contact_screen'})
            
            # Reuse the header and footer
            contact_screen.add_child(header)
            
            contact_form = UIComponent(UIComponentType.LAYOUT, {'id': 'contact_form'})
            contact_form.style = {'padding': '40px', 'background': '#FFFFFF'}
            
            form_title = UIComponent(UIComponentType.LABEL, {'id': 'form_title', 'text': 'Contact Us'})
            form_title.style = {'font-size': '28px', 'color': '#333333'}
            contact_form.add_child(form_title)
            
            name_field = UIComponent(UIComponentType.TEXT_FIELD, {'id': 'name_field', 'placeholder': 'Your Name'})
            name_field.style = {'width': '100%', 'margin': '10px 0'}
            contact_form.add_child(name_field)
            
            email_field = UIComponent(UIComponentType.TEXT_FIELD, {'id': 'email_field', 'placeholder': 'Your Email'})
            email_field.style = {'width': '100%', 'margin': '10px 0'}
            contact_form.add_child(email_field)
            
            message_field = UIComponent(UIComponentType.TEXT_FIELD, {'id': 'message_field', 'placeholder': 'Your Message', 'multiline': True})
            message_field.style = {'width': '100%', 'height': '150px', 'margin': '10px 0'}
            contact_form.add_child(message_field)
            
            submit_button = UIComponent(UIComponentType.BUTTON, {'id': 'submit_button', 'text': 'Send Message'})
            submit_button.style = {'background': '#1976D2', 'color': '#FFFFFF', 'padding': '12px 24px'}
            contact_form.add_child(submit_button)
            
            contact_screen.add_child(contact_form)
            contact_screen.add_child(footer)
            
            template.add_screen('contact', contact_screen)
            
            # Set up navigation
            template.set_navigation({
                'home': ['contact'],
                'contact': ['home']
            })
            
            # Set sample color scheme based on url
            if 'google' in url:
                template.style.colors = {
                    'primary': "#4285F4",
                    'secondary': "#34A853",
                    'accent': "#FBBC05",
                    'background': "#FFFFFF",
                    'surface': "#F8F9FA",
                    'error': "#EA4335",
                    'text_primary': "#202124",
                    'text_secondary': "#5F6368"
                }
            elif 'twitter' in url or 'x.com' in url:
                template.style.colors = {
                    'primary': "#1DA1F2",
                    'secondary': "#14171A",
                    'accent': "#1DA1F2",
                    'background': "#FFFFFF",
                    'surface': "#F5F8FA",
                    'error': "#E0245E",
                    'text_primary': "#14171A",
                    'text_secondary': "#657786"
                }
            elif 'facebook' in url:
                template.style.colors = {
                    'primary': "#1877F2",
                    'secondary': "#42B72A",
                    'accent': "#1877F2",
                    'background': "#FFFFFF",
                    'surface': "#F0F2F5",
                    'error': "#FA383E",
                    'text_primary': "#050505",
                    'text_secondary': "#65676B"
                }
            
            # Create a template export
            result_path = self._export_template(template)
            
            return {
                'success': True,
                'template': template,
                'template_path': result_path,
                'message': f"UI design extracted from website {url}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_from_windows_app(self, app_path):
        """Extract UI design from a Windows application"""
        if not os.path.exists(app_path):
            return {'success': False, 'error': 'Application executable does not exist'}
        
        try:
            # This would normally require Windows-specific APIs
            # For this demo, we'll create a simplified version
            
            app_name = os.path.basename(app_path)
            
            # Create UI template with basic info
            template = UITemplate(
                name=f"UI from {app_name}",
                description=f"UI extracted from Windows application {app_name}"
            )
            
            # Set metadata
            template.metadata['source'] = app_path
            template.metadata['platform'] = 'windows'
            template.metadata['extracted_date'] = datetime.now().isoformat()
            
            # Create a template export
            result_path = self._export_template(template)
            
            return {
                'success': True,
                'template': template,
                'template_path': result_path,
                'message': f"UI design extracted from Windows application {app_name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_to_project(self, template_path, project_path, project_type):
        """Apply UI template to a project"""
        if not os.path.exists(template_path):
            return {'success': False, 'error': 'Template file does not exist'}
            
        if not os.path.exists(project_path):
            return {'success': False, 'error': 'Project directory does not exist'}
        
        try:
            # Load the template
            template = None
            with open(template_path, 'r') as f:
                template_data = json.load(f)
                template = UITemplate.from_dict(template_data)
            
            if not template:
                return {'success': False, 'error': 'Failed to load template'}
            
            # Apply the template based on project type
            if project_type == 'android':
                result = self._apply_to_android_project(template, project_path)
            elif project_type == 'flutter':
                result = self._apply_to_flutter_project(template, project_path)
            elif project_type == 'react':
                result = self._apply_to_react_project(template, project_path)
            elif project_type == 'web':
                result = self._apply_to_web_project(template, project_path)
            elif project_type == 'wpf':
                result = self._apply_to_wpf_project(template, project_path)
            else:
                return {'success': False, 'error': f'Unsupported project type: {project_type}'}
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_package_name(self, extraction_dir):
        """Extract package name from APK manifest"""
        manifest_path = os.path.join(extraction_dir, 'AndroidManifest.xml')
        if not os.path.exists(manifest_path):
            return None
            
        try:
            # Try to parse XML (may fail for binary XML)
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            ns = {'android': 'http://schemas.android.com/apk/res/android'}
            package = root.get('package')
            
            return package
        except Exception:
            # If parsing fails, try to find it in other files
            for root, dirs, files in os.walk(extraction_dir):
                for file in files:
                    if file.endswith('.xml'):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                match = re.search(r'package="([^"]+)"', content)
                                if match:
                                    return match.group(1)
                        except Exception:
                            pass
            
            return None
    
    def _extract_android_colors(self, extraction_dir):
        """Extract color scheme from Android resources"""
        colors = {}
        
        # Look for colors.xml in different resource directories
        for root, dirs, files in os.walk(extraction_dir):
            for file in files:
                if file == 'colors.xml':
                    try:
                        tree = ET.parse(os.path.join(root, file))
                        root_element = tree.getroot()
                        
                        for color_element in root_element.findall('.//color'):
                            name = color_element.get('name')
                            value = color_element.text
                            
                            if name and value:
                                # Map common Android color names to our color scheme
                                if 'primary' in name:
                                    colors['primary'] = value
                                elif 'secondary' in name or 'accent' in name:
                                    colors['secondary'] = value
                                elif 'background' in name:
                                    colors['background'] = value
                                elif 'surface' in name:
                                    colors['surface'] = value
                                elif 'error' in name:
                                    colors['error'] = value
                                elif 'text' in name and 'primary' in name:
                                    colors['text_primary'] = value
                                elif 'text' in name and 'secondary' in name:
                                    colors['text_secondary'] = value
                    except Exception:
                        pass
        
        return colors
    
    def _extract_android_dimensions(self, extraction_dir):
        """Extract dimensions from Android resources"""
        dimensions = {}
        
        # Look for dimens.xml in different resource directories
        for root, dirs, files in os.walk(extraction_dir):
            for file in files:
                if file == 'dimens.xml':
                    try:
                        tree = ET.parse(os.path.join(root, file))
                        root_element = tree.getroot()
                        
                        for dimen_element in root_element.findall('.//dimen'):
                            name = dimen_element.get('name')
                            value = dimen_element.text
                            
                            if name and value:
                                # Map common Android dimension names to our scheme
                                if 'padding' in name:
                                    dimensions['padding'] = value
                                elif 'margin' in name:
                                    dimensions['margin'] = value
                                elif 'radius' in name or 'corner' in name:
                                    dimensions['border_radius'] = value
                                elif 'icon' in name and 'size' in name:
                                    dimensions['icon_size'] = value
                                elif 'button' in name and 'height' in name:
                                    dimensions['button_height'] = value
                                elif 'input' in name and 'height' in name:
                                    dimensions['input_height'] = value
                    except Exception:
                        pass
        
        return dimensions
    
    def _extract_android_layouts(self, extraction_dir):
        """Extract layouts from Android resources"""
        screens = {}
        
        # Look for layout XMLs
        layout_dir = os.path.join(extraction_dir, 'res', 'layout')
        if not os.path.exists(layout_dir):
            return screens
            
        for file in os.listdir(layout_dir):
            if file.endswith('.xml'):
                try:
                    layout_path = os.path.join(layout_dir, file)
                    screen_name = os.path.splitext(file)[0]
                    
                    # Parse the layout XML
                    tree = ET.parse(layout_path)
                    root_element = tree.getroot()
                    
                    # Convert to our component structure
                    root_component = self._convert_android_view_to_component(root_element)
                    screens[screen_name] = root_component
                except Exception:
                    pass
        
        return screens
    
    def _convert_android_view_to_component(self, element):
        """Convert Android View XML to UIComponent"""
        # Determine component type based on element tag
        tag = element.tag.split('.')[-1]  # Get the last part of the tag
        
        component_type = UIComponentType.UNKNOWN
        
        if tag in ['LinearLayout', 'RelativeLayout', 'FrameLayout', 'ConstraintLayout']:
            component_type = UIComponentType.LAYOUT
        elif tag == 'Button':
            component_type = UIComponentType.BUTTON
        elif tag == 'TextView':
            component_type = UIComponentType.LABEL
        elif tag == 'EditText':
            component_type = UIComponentType.TEXT_FIELD
        elif tag == 'ImageView':
            component_type = UIComponentType.IMAGE
        elif tag == 'RecyclerView' or tag == 'ListView':
            component_type = UIComponentType.LIST
        elif tag == 'GridView':
            component_type = UIComponentType.GRID
        elif tag == 'CheckBox':
            component_type = UIComponentType.CHECKBOX
        elif tag == 'RadioButton':
            component_type = UIComponentType.RADIO
        elif tag == 'Spinner':
            component_type = UIComponentType.DROPDOWN
        elif tag == 'SeekBar':
            component_type = UIComponentType.SLIDER
        elif tag == 'ProgressBar':
            component_type = UIComponentType.PROGRESS
        elif tag == 'TabLayout':
            component_type = UIComponentType.TAB
        elif tag == 'CardView':
            component_type = UIComponentType.CARD
        
        # Extract properties
        ns = {'android': 'http://schemas.android.com/apk/res/android'}
        properties = {}
        
        for key, value in element.attrib.items():
            # Extract attribute name without namespace
            if '}' in key:
                attr_name = key.split('}')[-1]
            else:
                attr_name = key
                
            properties[attr_name] = value
        
        # Create the component
        component = UIComponent(component_type, properties)
        
        # Extract style
        style = {}
        
        # Dimensions and positioning
        padding = element.get(f"{{{ns['android']}}}padding")
        if padding:
            style['padding'] = padding
            
        layout_width = element.get(f"{{{ns['android']}}}layout_width")
        if layout_width:
            style['width'] = layout_width
            
        layout_height = element.get(f"{{{ns['android']}}}layout_height")
        if layout_height:
            style['height'] = layout_height
            
        # Text styling
        text_size = element.get(f"{{{ns['android']}}}textSize")
        if text_size:
            style['font-size'] = text_size
            
        text_color = element.get(f"{{{ns['android']}}}textColor")
        if text_color:
            style['color'] = text_color
            
        text_style = element.get(f"{{{ns['android']}}}textStyle")
        if text_style:
            style['font-style'] = text_style
        
        # Background
        background = element.get(f"{{{ns['android']}}}background")
        if background:
            style['background'] = background
        
        component.style = style
        
        # Process children
        for child_element in element:
            child_component = self._convert_android_view_to_component(child_element)
            component.add_child(child_component)
        
        return component
    
    def _extract_colors_from_screenshots(self, screenshot_paths):
        """Extract color scheme from screenshots using computer vision"""
        if not CV2_AVAILABLE:
            return {}
            
        try:
            # Initialize color scheme
            colors = {
                'primary': None,
                'secondary': None,
                'background': None,
                'text_primary': None
            }
            
            # Process each screenshot
            dominant_colors = []
            background_colors = []
            text_colors = []
            
            for screenshot_path in screenshot_paths:
                img = cv2.imread(screenshot_path)
                if img is None:
                    continue
                    
                # Convert to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Reshape and cluster colors
                pixels = img_rgb.reshape(-1, 3)
                
                # Use K-means clustering to find dominant colors
                num_clusters = 5
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                _, labels, centers = cv2.kmeans(np.float32(pixels), num_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                
                # Count occurrences of each cluster
                counts = np.bincount(labels.flatten())
                
                # Sort clusters by count
                sorted_indices = np.argsort(counts)[::-1]
                sorted_centers = centers[sorted_indices]
                
                # Convert to hex colors
                for center in sorted_centers:
                    r, g, b = [int(c) for c in center]
                    hex_color = f"#{r:02X}{g:02X}{b:02X}"
                    dominant_colors.append(hex_color)
                
                # Assume the most common color is the background
                background_colors.append(dominant_colors[0])
                
                # Extract text colors using edge detection and color analysis
                # This is a simplified approach
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                
                # Create a mask of edge pixels
                mask = edges > 0
                
                # Extract colors along edges
                edge_colors = img_rgb[mask]
                
                if len(edge_colors) > 0:
                    # Cluster edge colors
                    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                    _, labels, centers = cv2.kmeans(np.float32(edge_colors), 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                    
                    # Count occurrences of each cluster
                    counts = np.bincount(labels.flatten())
                    
                    # Sort clusters by count
                    sorted_indices = np.argsort(counts)[::-1]
                    sorted_centers = centers[sorted_indices]
                    
                    # Convert to hex colors
                    for center in sorted_centers:
                        r, g, b = [int(c) for c in center]
                        
                        # Check if the color is dark (likely text)
                        if r + g + b < 384:  # 3 * 128
                            hex_color = f"#{r:02X}{g:02X}{b:02X}"
                            text_colors.append(hex_color)
            
            # Aggregate results
            if dominant_colors:
                # Primary color is often the second most common color
                if len(dominant_colors) > 1:
                    colors['primary'] = dominant_colors[1]
                
                # Secondary color is often the third most common color
                if len(dominant_colors) > 2:
                    colors['secondary'] = dominant_colors[2]
            
            if background_colors:
                colors['background'] = background_colors[0]
                colors['surface'] = background_colors[0]
            
            if text_colors:
                colors['text_primary'] = text_colors[0]
                if len(text_colors) > 1:
                    colors['text_secondary'] = text_colors[1]
            
            # Fill in any missing colors with defaults
            default_colors = {
                'primary': "#1976D2",
                'secondary': "#424242",
                'accent': "#FF4081",
                'background': "#FFFFFF",
                'surface': "#FFFFFF",
                'error': "#F44336",
                'text_primary': "#212121",
                'text_secondary': "#757575"
            }
            
            for key, value in default_colors.items():
                if key not in colors or colors[key] is None:
                    colors[key] = value
            
            return colors
            
        except Exception as e:
            print(f"Error extracting colors: {e}")
            return {}
    
    def _extract_components_from_screenshot(self, screenshot_path):
        """Extract UI components from a screenshot using computer vision"""
        if not CV2_AVAILABLE:
            root = UIComponent(UIComponentType.LAYOUT, {'id': 'root'})
            return root
            
        try:
            # Load the image
            img = cv2.imread(screenshot_path)
            if img is None:
                root = UIComponent(UIComponentType.LAYOUT, {'id': 'root'})
                return root
                
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Create a root component
            root = UIComponent(UIComponentType.LAYOUT, {'id': 'root'})
            root.style = {
                'width': f"{img.shape[1]}px",
                'height': f"{img.shape[0]}px"
            }
            
            # Detect rectangles (potential UI components)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                # Skip very small contours
                if cv2.contourArea(contour) < 100:
                    continue
                    
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Create a component based on shape and size
                component_type = UIComponentType.UNKNOWN
                
                # Determine component type based on size and shape
                aspect_ratio = w / h if h > 0 else 0
                
                if aspect_ratio > 3 and h < 100:
                    # Wide rectangle could be a header
                    component_type = UIComponentType.LAYOUT
                    properties = {'id': f'header_{i}', 'role': 'header'}
                elif aspect_ratio < 0.5 and w < 100:
                    # Tall rectangle could be a sidebar
                    component_type = UIComponentType.NAVIGATION
                    properties = {'id': f'sidebar_{i}', 'role': 'navigation'}
                elif 0.8 < aspect_ratio < 1.2 and h < 100 and w < 100:
                    # Square could be a button or icon
                    component_type = UIComponentType.BUTTON
                    properties = {'id': f'button_{i}'}
                elif 2 < aspect_ratio < 8 and h < 60:
                    # Could be a text field
                    component_type = UIComponentType.TEXT_FIELD
                    properties = {'id': f'field_{i}'}
                else:
                    # Default to a generic container
                    component_type = UIComponentType.LAYOUT
                    properties = {'id': f'container_{i}'}
                
                component = UIComponent(component_type, properties)
                component.style = {
                    'position': 'absolute',
                    'left': f"{x}px",
                    'top': f"{y}px",
                    'width': f"{w}px",
                    'height': f"{h}px"
                }
                
                # Extract average color of the component region
                roi = img[y:y+h, x:x+w]
                average_color = cv2.mean(roi)[:3]
                average_color_hex = f"#{int(average_color[2]):02X}{int(average_color[1]):02X}{int(average_color[0]):02X}"
                component.style['background'] = average_color_hex
                
                root.add_child(component)
            
            return root
            
        except Exception as e:
            print(f"Error extracting components: {e}")
            root = UIComponent(UIComponentType.LAYOUT, {'id': 'root'})
            return root
    
    def _export_template(self, template):
        """Export UI template to a file"""
        template_dir = os.path.join(self.cache_dir, 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        # Sanitize template name for filename
        sanitized_name = ''.join(c for c in template.name if c.isalnum() or c == ' ').strip().replace(' ', '_')
        template_path = os.path.join(template_dir, f"{sanitized_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Export the template to JSON
        with open(template_path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
        
        return template_path
    
    def _apply_to_android_project(self, template, project_path):
        """Apply UI template to an Android project"""
        try:
            # Create the colors.xml file
            colors_dir = os.path.join(project_path, 'app', 'src', 'main', 'res', 'values')
            os.makedirs(colors_dir, exist_ok=True)
            
            colors_path = os.path.join(colors_dir, 'colors.xml')
            with open(colors_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write('<resources>\n')
                
                for name, value in template.style.colors.items():
                    f.write(f'    <color name="{name}">{value}</color>\n')
                
                f.write('</resources>\n')
            
            # Create the dimens.xml file
            dimens_path = os.path.join(colors_dir, 'dimens.xml')
            with open(dimens_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write('<resources>\n')
                
                for name, value in template.style.dimensions.items():
                    # Convert to dp if not already
                    if not value.endswith('dp') and not value.endswith('sp'):
                        if 'font' in name or 'text' in name:
                            value = value.replace('px', 'sp')
                        else:
                            value = value.replace('px', 'dp')
                    
                    f.write(f'    <dimen name="{name}">{value}</dimen>\n')
                
                f.write('</resources>\n')
            
            # Create the styles.xml file
            styles_path = os.path.join(colors_dir, 'styles.xml')
            with open(styles_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write('<resources>\n')
                
                f.write('    <style name="AppTheme" parent="Theme.AppCompat.Light.DarkActionBar">\n')
                f.write('        <item name="colorPrimary">@color/primary</item>\n')
                f.write('        <item name="colorPrimaryDark">@color/primary</item>\n')
                f.write('        <item name="colorAccent">@color/accent</item>\n')
                f.write('        <item name="android:windowBackground">@color/background</item>\n')
                f.write('        <item name="android:textColorPrimary">@color/text_primary</item>\n')
                f.write('        <item name="android:textColorSecondary">@color/text_secondary</item>\n')
                f.write('    </style>\n')
                
                f.write('</resources>\n')
            
            # Create layout files for each screen
            layout_dir = os.path.join(project_path, 'app', 'src', 'main', 'res', 'layout')
            os.makedirs(layout_dir, exist_ok=True)
            
            for screen_name, root_component in template.screens.items():
                layout_path = os.path.join(layout_dir, f"{screen_name}.xml")
                with open(layout_path, 'w') as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    self._write_android_component(f, root_component)
            
            # Copy assets
            drawable_dir = os.path.join(project_path, 'app', 'src', 'main', 'res', 'drawable')
            os.makedirs(drawable_dir, exist_ok=True)
            
            for asset_name, asset_path in template.assets.items():
                if os.path.exists(asset_path):
                    dst_path = os.path.join(drawable_dir, os.path.basename(asset_path))
                    shutil.copy2(asset_path, dst_path)
            
            return {
                'success': True,
                'message': 'UI template applied to Android project',
                'files_created': [
                    colors_path,
                    dimens_path,
                    styles_path
                ] + [os.path.join(layout_dir, f"{name}.xml") for name in template.screens.keys()]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _write_android_component(self, file, component, indent=0):
        """Write a component as Android XML"""
        indentation = ' ' * 4 * indent
        
        # Map component types to Android view types
        type_to_view = {
            UIComponentType.LAYOUT: 'LinearLayout',
            UIComponentType.BUTTON: 'Button',
            UIComponentType.TEXT_FIELD: 'EditText',
            UIComponentType.LABEL: 'TextView',
            UIComponentType.IMAGE: 'ImageView',
            UIComponentType.LIST: 'ListView',
            UIComponentType.GRID: 'GridView',
            UIComponentType.NAVIGATION: 'LinearLayout',
            UIComponentType.MENU: 'LinearLayout',
            UIComponentType.DIALOG: 'LinearLayout',
            UIComponentType.TAB: 'TabLayout',
            UIComponentType.CHECKBOX: 'CheckBox',
            UIComponentType.RADIO: 'RadioButton',
            UIComponentType.DROPDOWN: 'Spinner',
            UIComponentType.SLIDER: 'SeekBar',
            UIComponentType.PROGRESS: 'ProgressBar',
            UIComponentType.CARD: 'CardView'
        }
        
        view_type = type_to_view.get(component.component_type, 'LinearLayout')
        
        # Start the tag
        file.write(f'{indentation}<{view_type}\n')
        
        # Write XML namespace for the root element
        if indent == 0:
            file.write(f'{indentation}    xmlns:android="http://schemas.android.com/apk/res/android"\n')
            file.write(f'{indentation}    xmlns:app="http://schemas.android.com/apk/res-auto"\n')
            file.write(f'{indentation}    android:layout_width="match_parent"\n')
            file.write(f'{indentation}    android:layout_height="match_parent"\n')
            
            # If it's a layout, set orientation
            if component.component_type == UIComponentType.LAYOUT:
                file.write(f'{indentation}    android:orientation="vertical"\n')
        else:
            # Write layout params
            width = component.style.get('width', 'wrap_content')
            height = component.style.get('height', 'wrap_content')
            
            # Convert pixel values to dp
            width = width.replace('px', 'dp')
            height = height.replace('px', 'dp')
            
            # Handle special values
            if width == '100%':
                width = 'match_parent'
            if height == '100%':
                height = 'match_parent'
            
            file.write(f'{indentation}    android:layout_width="{width}"\n')
            file.write(f'{indentation}    android:layout_height="{height}"\n')
            
            # Write ID if available
            if component.id:
                file.write(f'{indentation}    android:id="@+id/{component.id}"\n')
            
            # Write text for text components
            if component.component_type in [UIComponentType.BUTTON, UIComponentType.LABEL]:
                text = component.properties.get('text', '')
                if text:
                    file.write(f'{indentation}    android:text="{text}"\n')
            
            # Write hint for text fields
            if component.component_type == UIComponentType.TEXT_FIELD:
                hint = component.properties.get('placeholder', '')
                if hint:
                    file.write(f'{indentation}    android:hint="{hint}"\n')
                
                if component.properties.get('multiline', False):
                    file.write(f'{indentation}    android:inputType="textMultiLine"\n')
                    file.write(f'{indentation}    android:gravity="top|start"\n')
            
            # Write background color if available
            bg_color = component.style.get('background')
            if bg_color:
                file.write(f'{indentation}    android:background="{bg_color}"\n')
            
            # Write text color if available
            text_color = component.style.get('color')
            if text_color and component.component_type in [UIComponentType.BUTTON, UIComponentType.LABEL, UIComponentType.TEXT_FIELD]:
                file.write(f'{indentation}    android:textColor="{text_color}"\n')
            
            # Write padding if available
            padding = component.style.get('padding')
            if padding:
                file.write(f'{indentation}    android:padding="{padding.replace("px", "dp")}"\n')
            
            # Write margin if available
            margin = component.style.get('margin')
            if margin:
                file.write(f'{indentation}    android:layout_margin="{margin.replace("px", "dp")}"\n')
            
            # Handle position for absolute positioning
            if 'position' in component.style and component.style['position'] == 'absolute':
                left = component.style.get('left', '0px').replace('px', 'dp')
                top = component.style.get('top', '0px').replace('px', 'dp')
                file.write(f'{indentation}    android:layout_marginLeft="{left}"\n')
                file.write(f'{indentation}    android:layout_marginTop="{top}"\n')
            
            # Write font size if available
            font_size = component.style.get('font-size')
            if font_size and component.component_type in [UIComponentType.BUTTON, UIComponentType.LABEL, UIComponentType.TEXT_FIELD]:
                file.write(f'{indentation}    android:textSize="{font_size.replace("px", "sp")}"\n')
        
        # Close the opening tag
        if not component.children:
            file.write(f'{indentation}/>\n')
        else:
            file.write(f'{indentation}>\n')
            
            # Write children
            for child in component.children:
                self._write_android_component(file, child, indent + 1)
            
            # Close the tag
            file.write(f'{indentation}</{view_type}>\n')
    
    def _apply_to_flutter_project(self, template, project_path):
        """Apply UI template to a Flutter project"""
        try:
            # Create a theme file
            lib_dir = os.path.join(project_path, 'lib')
            os.makedirs(lib_dir, exist_ok=True)
            
            theme_path = os.path.join(lib_dir, 'theme.dart')
            with open(theme_path, 'w') as f:
                f.write('import \'package:flutter/material.dart\';\n\n')
                
                # Create a color constants class
                f.write('class AppColors {\n')
                for name, value in template.style.colors.items():
                    # Convert from hex to Color
                    color_value = value.replace('#', '0xFF')
                    f.write(f'  static const Color {name} = Color({color_value});\n')
                f.write('}\n\n')
                
                # Create a theme data method
                f.write('ThemeData buildTheme() {\n')
                f.write('  return ThemeData(\n')
                f.write('    primaryColor: AppColors.primary,\n')
                f.write('    accentColor: AppColors.accent,\n')
                f.write('    scaffoldBackgroundColor: AppColors.background,\n')
                f.write('    textTheme: TextTheme(\n')
                f.write('      headline1: TextStyle(color: AppColors.text_primary, fontSize: 24, fontWeight: FontWeight.bold),\n')
                f.write('      headline2: TextStyle(color: AppColors.text_primary, fontSize: 20, fontWeight: FontWeight.bold),\n')
                f.write('      bodyText1: TextStyle(color: AppColors.text_primary, fontSize: 16),\n')
                f.write('      bodyText2: TextStyle(color: AppColors.text_secondary, fontSize: 14),\n')
                f.write('    ),\n')
                f.write('    buttonTheme: ButtonThemeData(\n')
                f.write('      buttonColor: AppColors.primary,\n')
                f.write('      textTheme: ButtonTextTheme.primary,\n')
                f.write('      shape: RoundedRectangleBorder(\n')
                f.write(f'        borderRadius: BorderRadius.circular({template.style.dimensions.get("border_radius", "4px").replace("px", "")}),\n')
                f.write('      ),\n')
                f.write('    ),\n')
                f.write('    inputDecorationTheme: InputDecorationTheme(\n')
                f.write('      border: OutlineInputBorder(\n')
                f.write(f'        borderRadius: BorderRadius.circular({template.style.dimensions.get("border_radius", "4px").replace("px", "")}),\n')
                f.write('      ),\n')
                f.write('    ),\n')
                f.write('  );\n')
                f.write('}\n')
            
            # Create screen files for each template screen
            screens_dir = os.path.join(lib_dir, 'screens')
            os.makedirs(screens_dir, exist_ok=True)
            
            for screen_name, root_component in template.screens.items():
                screen_path = os.path.join(screens_dir, f"{screen_name}_screen.dart")
                with open(screen_path, 'w') as f:
                    f.write('import \'package:flutter/material.dart\';\n')
                    f.write('import \'../theme.dart\';\n\n')
                    
                    class_name = ''.join(word.title() for word in screen_name.split('_')) + 'Screen'
                    f.write(f'class {class_name} extends StatelessWidget {{\n')
                    f.write('  @override\n')
                    f.write('  Widget build(BuildContext context) {\n')
                    f.write('    return Scaffold(\n')
                    f.write('      appBar: AppBar(\n')
                    f.write(f'        title: Text(\'{screen_name.replace("_", " ").title()}\'),\n')
                    f.write('      ),\n')
                    f.write('      body: ')
                    
                    # Write the component tree
                    self._write_flutter_component(f, root_component, 3)
                    
                    f.write('\n    );\n')
                    f.write('  }\n')
                    f.write('}\n')
            
            # Copy assets
            assets_dir = os.path.join(project_path, 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            
            for asset_name, asset_path in template.assets.items():
                if os.path.exists(asset_path):
                    dst_path = os.path.join(assets_dir, os.path.basename(asset_path))
                    shutil.copy2(asset_path, dst_path)
            
            # Update pubspec.yaml to include assets
            pubspec_path = os.path.join(project_path, 'pubspec.yaml')
            if os.path.exists(pubspec_path):
                with open(pubspec_path, 'r') as f:
                    content = f.read()
                
                # Check if assets section exists
                if 'assets:' in content:
                    # Add assets to existing section
                    lines = content.split('\n')
                    assets_index = -1
                    
                    for i, line in enumerate(lines):
                        if line.strip() == 'assets:':
                            assets_index = i
                            break
                    
                    if assets_index >= 0:
                        indentation = ' ' * (len(lines[assets_index]) - len(lines[assets_index].lstrip()))
                        lines.insert(assets_index + 1, f'{indentation}  - assets/')
                        
                        with open(pubspec_path, 'w') as f:
                            f.write('\n'.join(lines))
                else:
                    # Add assets section
                    with open(pubspec_path, 'a') as f:
                        f.write('\n\nassets:\n  - assets/\n')
            
            return {
                'success': True,
                'message': 'UI template applied to Flutter project',
                'files_created': [
                    theme_path
                ] + [os.path.join(screens_dir, f"{name}_screen.dart") for name in template.screens.keys()]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _write_flutter_component(self, file, component, indent=0):
        """Write a component as Flutter widget"""
        indentation = ' ' * 2 * indent
        
        # Map component types to Flutter widgets
        type_to_widget = {
            UIComponentType.LAYOUT: 'Container',
            UIComponentType.BUTTON: 'ElevatedButton',
            UIComponentType.TEXT_FIELD: 'TextField',
            UIComponentType.LABEL: 'Text',
            UIComponentType.IMAGE: 'Image',
            UIComponentType.LIST: 'ListView',
            UIComponentType.GRID: 'GridView',
            UIComponentType.NAVIGATION: 'Row',
            UIComponentType.MENU: 'Row',
            UIComponentType.DIALOG: 'Dialog',
            UIComponentType.TAB: 'TabBar',
            UIComponentType.CHECKBOX: 'Checkbox',
            UIComponentType.RADIO: 'Radio',
            UIComponentType.DROPDOWN: 'DropdownButton',
            UIComponentType.SLIDER: 'Slider',
            UIComponentType.PROGRESS: 'CircularProgressIndicator',
            UIComponentType.CARD: 'Card'
        }
        
        widget_type = type_to_widget.get(component.component_type, 'Container')
        
        # Handle specific widget types
        if component.component_type == UIComponentType.LABEL:
            text = component.properties.get('text', '')
            file.write(f'{indentation}Text(\n')
            file.write(f'{indentation}  \'{text}\',\n')
            
            style_properties = []
            
            # Add text style properties
            color = component.style.get('color')
            if color:
                style_properties.append(f'color: Color({color.replace("#", "0xFF")})')
            
            font_size = component.style.get('font-size')
            if font_size:
                size_value = font_size.replace('px', '')
                try:
                    size_value = float(size_value)
                    style_properties.append(f'fontSize: {size_value}')
                except ValueError:
                    pass
            
            font_weight = component.style.get('font-weight')
            if font_weight:
                if font_weight in ['bold', 'bolder']:
                    style_properties.append('fontWeight: FontWeight.bold')
                elif font_weight == 'normal':
                    style_properties.append('fontWeight: FontWeight.normal')
            
            if style_properties:
                file.write(f'{indentation}  style: TextStyle(\n')
                for i, prop in enumerate(style_properties):
                    file.write(f'{indentation}    {prop}')
                    if i < len(style_properties) - 1:
                        file.write(',')
                    file.write('\n')
                file.write(f'{indentation}  ),\n')
            
            file.write(f'{indentation})')
            
        elif component.component_type == UIComponentType.BUTTON:
            text = component.properties.get('text', '')
            file.write(f'{indentation}ElevatedButton(\n')
            file.write(f'{indentation}  onPressed: () {{}},\n')
            file.write(f'{indentation}  child: Text(\'{text}\'),\n')
            file.write(f'{indentation})')
            
        elif component.component_type == UIComponentType.TEXT_FIELD:
            placeholder = component.properties.get('placeholder', '')
            file.write(f'{indentation}TextField(\n')
            file.write(f'{indentation}  decoration: InputDecoration(\n')
            file.write(f'{indentation}    hintText: \'{placeholder}\',\n')
            file.write(f'{indentation}  ),\n')
            
            # Handle multiline
            if component.properties.get('multiline', False):
                file.write(f'{indentation}  maxLines: null,\n')
            
            file.write(f'{indentation})')
            
        elif component.component_type == UIComponentType.LAYOUT:
            file.write(f'{indentation}Container(\n')
            
            # Add container properties
            properties = []
            
            # Width and height
            width = component.style.get('width')
            if width and width != '100%' and width != 'match_parent':
                width_value = width.replace('px', '')
                try:
                    width_value = float(width_value)
                    properties.append(f'width: {width_value}')
                except ValueError:
                    pass
            
            height = component.style.get('height')
            if height and height != '100%' and height != 'match_parent':
                height_value = height.replace('px', '')
                try:
                    height_value = float(height_value)
                    properties.append(f'height: {height_value}')
                except ValueError:
                    pass
            
            # Background color
            bg_color = component.style.get('background')
            if bg_color:
                properties.append(f'color: Color({bg_color.replace("#", "0xFF")})')
            
            # Padding
            padding = component.style.get('padding')
            if padding:
                padding_value = padding.replace('px', '')
                try:
                    padding_value = float(padding_value)
                    properties.append(f'padding: EdgeInsets.all({padding_value})')
                except ValueError:
                    pass
            
            # Margin
            margin = component.style.get('margin')
            if margin:
                margin_value = margin.replace('px', '')
                try:
                    margin_value = float(margin_value)
                    properties.append(f'margin: EdgeInsets.all({margin_value})')
                except ValueError:
                    pass
            
            # Write properties
            for i, prop in enumerate(properties):
                file.write(f'{indentation}  {prop}')
                if i < len(properties) - 1 or component.children:
                    file.write(',')
                file.write('\n')
            
            # Add child or children
            if len(component.children) == 1:
                file.write(f'{indentation}  child: ')
                self._write_flutter_component(file, component.children[0], indent + 1)
                file.write('\n')
            elif len(component.children) > 1:
                file.write(f'{indentation}  child: Column(\n')
                file.write(f'{indentation}    children: [\n')
                
                for child in component.children:
                    self._write_flutter_component(file, child, indent + 3)
                    file.write(',\n')
                
                file.write(f'{indentation}    ],\n')
                file.write(f'{indentation}  ),\n')
            
            file.write(f'{indentation})')
            
        else:
            # Generic fallback for unsupported components
            file.write(f'{indentation}Container(')
            
            if component.children:
                file.write('\n')
                file.write(f'{indentation}  child: Column(\n')
                file.write(f'{indentation}    children: [\n')
                
                for child in component.children:
                    self._write_flutter_component(file, child, indent + 3)
                    file.write(',\n')
                
                file.write(f'{indentation}    ],\n')
                file.write(f'{indentation}  ),\n')
                file.write(f'{indentation})')
            else:
                file.write(')')
    
    def _apply_to_react_project(self, template, project_path):
        """Apply UI template to a React project"""
        try:
            # Create a theme file
            src_dir = os.path.join(project_path, 'src')
            os.makedirs(src_dir, exist_ok=True)
            
            theme_path = os.path.join(src_dir, 'theme.js')
            with open(theme_path, 'w') as f:
                f.write('// Theme generated from UI template\n\n')
                
                # Create a color constants object
                f.write('export const colors = {\n')
                for name, value in template.style.colors.items():
                    f.write(f'  {name}: \'{value}\',\n')
                f.write('};\n\n')
                
                # Create typography
                f.write('export const typography = {\n')
                for name, value in template.style.typography.items():
                    if isinstance(value, dict):
                        f.write(f'  {name}: {{\n')
                        for prop, val in value.items():
                            f.write(f'    {prop}: \'{val}\',\n')
                        f.write('  },\n')
                    else:
                        f.write(f'  {name}: \'{value}\',\n')
                f.write('};\n\n')
                
                # Create dimensions
                f.write('export const spacing = {\n')
                for name, value in template.style.dimensions.items():
                    f.write(f'  {name}: \'{value}\',\n')
                f.write('};\n\n')
                
                # Create theme object
                f.write('const theme = {\n')
                f.write('  colors,\n')
                f.write('  typography,\n')
                f.write('  spacing,\n')
                f.write('};\n\n')
                
                f.write('export default theme;\n')
            
            # Create component files
            components_dir = os.path.join(src_dir, 'components')
            os.makedirs(components_dir, exist_ok=True)
            
            # Create screen components
            for screen_name, root_component in template.screens.items():
                component_name = ''.join(word.title() for word in screen_name.split('_'))
                component_path = os.path.join(components_dir, f"{component_name}.js")
                
                with open(component_path, 'w') as f:
                    f.write('import React from \'react\';\n')
                    f.write('import { colors, typography, spacing } from \'../theme\';\n\n')
                    
                    f.write(f'const {component_name} = () => {{\n')
                    f.write('  return (\n')
                    
                    # Write the component tree
                    self._write_react_component(f, root_component, 2)
                    
                    f.write('\n  );\n')
                    f.write('};\n\n')
                    
                    f.write(f'export default {component_name};\n')
            
            # Create App.js file
            app_path = os.path.join(src_dir, 'App.js')
            with open(app_path, 'w') as f:
                f.write('import React from \'react\';\n')
                
                # Import the screen components
                for screen_name in template.screens.keys():
                    component_name = ''.join(word.title() for word in screen_name.split('_'))
                    f.write(f'import {component_name} from \'./components/{component_name}\';\n')
                
                f.write('\nimport { colors } from \'./theme\';\n\n')
                
                f.write('function App() {\n')
                f.write('  return (\n')
                f.write('    <div className="App" style={{ backgroundColor: colors.background }}>\n')
                
                # Add first screen
                if template.screens:
                    first_screen = next(iter(template.screens.keys()))
                    component_name = ''.join(word.title() for word in first_screen.split('_'))
                    f.write(f'      <{component_name} />\n')
                
                f.write('    </div>\n')
                f.write('  );\n')
                f.write('}\n\n')
                
                f.write('export default App;\n')
            
            # Copy assets
            assets_dir = os.path.join(project_path, 'public', 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            
            for asset_name, asset_path in template.assets.items():
                if os.path.exists(asset_path):
                    dst_path = os.path.join(assets_dir, os.path.basename(asset_path))
                    shutil.copy2(asset_path, dst_path)
            
            return {
                'success': True,
                'message': 'UI template applied to React project',
                'files_created': [
                    theme_path,
                    app_path
                ] + [os.path.join(components_dir, f"{''.join(word.title() for word in name.split('_'))}.js") for name in template.screens.keys()]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _write_react_component(self, file, component, indent=0):
        """Write a component as React JSX"""
        indentation = ' ' * 2 * indent
        
        # Map component types to React components
        type_to_component = {
            UIComponentType.LAYOUT: 'div',
            UIComponentType.BUTTON: 'button',
            UIComponentType.TEXT_FIELD: 'input',
            UIComponentType.LABEL: 'p',
            UIComponentType.IMAGE: 'img',
            UIComponentType.LIST: 'ul',
            UIComponentType.GRID: 'div',
            UIComponentType.NAVIGATION: 'nav',
            UIComponentType.MENU: 'nav',
            UIComponentType.DIALOG: 'div',
            UIComponentType.TAB: 'div',
            UIComponentType.CHECKBOX: 'input',
            UIComponentType.RADIO: 'input',
            UIComponentType.DROPDOWN: 'select',
            UIComponentType.SLIDER: 'input',
            UIComponentType.PROGRESS: 'progress',
            UIComponentType.CARD: 'div'
        }
        
        jsx_type = type_to_component.get(component.component_type, 'div')
        
        # Build style object
        style_props = []
        
        for key, value in component.style.items():
            # Convert CSS property names to camelCase
            if '-' in key:
                parts = key.split('-')
                prop_name = parts[0] + ''.join(part.title() for part in parts[1:])
            else:
                prop_name = key
                
            style_props.append(f'{prop_name}: \'{value}\'')
        
        # Start opening tag
        file.write(f'{indentation}<{jsx_type}')
        
        # Add id if available
        if component.id:
            file.write(f' id="{component.id}"')
        
        # Add specific attributes based on component type
        if component.component_type == UIComponentType.TEXT_FIELD:
            placeholder = component.properties.get('placeholder', '')
            if placeholder:
                file.write(f' placeholder="{placeholder}"')
                
            if component.properties.get('multiline', False):
                jsx_type = 'textarea'
                
        elif component.component_type == UIComponentType.BUTTON:
            file.write(' onClick={() => {}}')
            
        elif component.component_type == UIComponentType.CHECKBOX:
            file.write(' type="checkbox"')
            
        elif component.component_type == UIComponentType.RADIO:
            file.write(' type="radio"')
            
        elif component.component_type == UIComponentType.SLIDER:
            file.write(' type="range"')
            
        elif component.component_type == UIComponentType.IMAGE:
            src = component.properties.get('src', '/assets/placeholder.png')
            alt = component.properties.get('alt', 'Image')
            file.write(f' src="{src}" alt="{alt}"')
        
        # Add the style attribute if there are style properties
        if style_props:
            file.write(' style={{\n')
            for i, prop in enumerate(style_props):
                file.write(f'{indentation}  {prop}')
                if i < len(style_props) - 1:
                    file.write(',')
                file.write('\n')
            file.write(f'{indentation}}}')
        
        # Handle empty/self-closing components
        empty_elements = ['img', 'input', 'br', 'hr', 'meta', 'link']
        
        if not component.children and jsx_type in empty_elements:
            file.write(' />')
        else:
            file.write('>')
            
            # Add text content for text components
            if component.component_type in [UIComponentType.BUTTON, UIComponentType.LABEL]:
                text = component.properties.get('text', '')
                if text:
                    file.write(text)
            
            # Add children
            if component.children:
                file.write('\n')
                for child in component.children:
                    self._write_react_component(file, child, indent + 1)
                    file.write('\n')
                file.write(indentation)
            
            file.write(f'</{jsx_type}>')
    
    def _apply_to_web_project(self, template, project_path):
        """Apply UI template to a plain web project"""
        try:
            # Create CSS file
            css_dir = os.path.join(project_path, 'css')
            os.makedirs(css_dir, exist_ok=True)
            
            css_path = os.path.join(css_dir, 'styles.css')
            with open(css_path, 'w') as f:
                f.write('/* Styles generated from UI template */\n\n')
                
                # Root variables
                f.write(':root {\n')
                for name, value in template.style.colors.items():
                    f.write(f'  --color-{name}: {value};\n')
                
                # Add font sizes
                for name, value in template.style.typography.items():
                    if isinstance(value, dict) and 'size' in value:
                        f.write(f'  --font-size-{name}: {value["size"]};\n')
                
                # Add spacing
                for name, value in template.style.dimensions.items():
                    f.write(f'  --{name}: {value};\n')
                
                f.write('}\n\n')
                
                # Base styles
                f.write('body {\n')
                f.write('  font-family: var(--font-family, sans-serif);\n')
                f.write('  color: var(--color-text_primary);\n')
                f.write('  background-color: var(--color-background);\n')
                f.write('  margin: 0;\n')
                f.write('  padding: 0;\n')
                f.write('}\n\n')
                
                # Heading styles
                f.write('h1, h2, h3, h4, h5, h6 {\n')
                f.write('  color: var(--color-text_primary);\n')
                f.write('  margin-top: var(--margin);\n')
                f.write('  margin-bottom: var(--margin);\n')
                f.write('}\n\n')
                
                # Button styles
                f.write('button, .button {\n')
                f.write('  background-color: var(--color-primary);\n')
                f.write('  color: white;\n')
                f.write('  border: none;\n')
                f.write('  padding: calc(var(--padding) / 2) var(--padding);\n')
                f.write('  border-radius: var(--border_radius);\n')
                f.write('  cursor: pointer;\n')
                f.write('  font-size: var(--font-size-button, 14px);\n')
                f.write('}\n\n')
                
                # Input styles
                f.write('input, textarea {\n')
                f.write('  padding: calc(var(--padding) / 2);\n')
                f.write('  border: 1px solid var(--color-text_secondary);\n')
                f.write('  border-radius: var(--border_radius);\n')
                f.write('  font-size: var(--font-size-body1, 16px);\n')
                f.write('  width: 100%;\n')
                f.write('  box-sizing: border-box;\n')
                f.write('}\n\n')
                
                # Card styles
                f.write('.card {\n')
                f.write('  background-color: var(--color-surface);\n')
                f.write('  border-radius: var(--border_radius);\n')
                f.write('  padding: var(--padding);\n')
                f.write('  margin: var(--margin);\n')
                f.write('  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);\n')
                f.write('}\n\n')
                
                # Container styles
                f.write('.container {\n')
                f.write('  width: 100%;\n')
                f.write('  max-width: 1200px;\n')
                f.write('  margin: 0 auto;\n')
                f.write('  padding: var(--padding);\n')
                f.write('}\n\n')
                
                # Add component-specific styles
                for screen_name, root_component in template.screens.items():
                    self._generate_css_for_component(f, root_component, screen_name)
            
            # Create HTML files for each screen
            for screen_name, root_component in template.screens.items():
                html_path = os.path.join(project_path, f"{screen_name}.html")
                
                with open(html_path, 'w') as f:
                    f.write('<!DOCTYPE html>\n')
                    f.write('<html lang="en">\n')
                    f.write('<head>\n')
                    f.write('  <meta charset="UTF-8">\n')
                    f.write('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
                    f.write(f'  <title>{screen_name.replace("_", " ").title()}</title>\n')
                    f.write('  <link rel="stylesheet" href="css/styles.css">\n')
                    f.write('</head>\n')
                    f.write('<body>\n')
                    
                    # Write the component tree
                    self._write_html_component(f, root_component, 1, screen_name)
                    
                    # Add navigation links
                    if template.navigation and screen_name in template.navigation:
                        f.write('  <div class="navigation">\n')
                        for target_screen in template.navigation[screen_name]:
                            f.write(f'    <a href="{target_screen}.html">{target_screen.replace("_", " ").title()}</a>\n')
                        f.write('  </div>\n')
                    
                    f.write('</body>\n')
                    f.write('</html>\n')
            
            # Copy assets
            assets_dir = os.path.join(project_path, 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            
            for asset_name, asset_path in template.assets.items():
                if os.path.exists(asset_path):
                    dst_path = os.path.join(assets_dir, os.path.basename(asset_path))
                    shutil.copy2(asset_path, dst_path)
            
            return {
                'success': True,
                'message': 'UI template applied to web project',
                'files_created': [
                    css_path
                ] + [os.path.join(project_path, f"{name}.html") for name in template.screens.keys()]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_css_for_component(self, file, component, screen_prefix, path=''):
        """Generate CSS for a component and its children"""
        # Generate an identifier
        identifier = component.id if component.id else f"{component.component_type}_{hash(path) % 1000}"
        full_id = f"{screen_prefix}_{identifier}"
        
        # Only generate CSS if there are style properties
        if component.style:
            file.write(f'#{full_id}, .{full_id} {{\n')
            
            for key, value in component.style.items():
                # Use the CSS property name directly
                file.write(f'  {key}: {value};\n')
            
            file.write('}\n\n')
        
        # Generate CSS for children
        for i, child in enumerate(component.children):
            child_path = f"{path}_{i}" if path else str(i)
            self._generate_css_for_component(file, child, screen_prefix, child_path)
    
    def _write_html_component(self, file, component, indent=0, screen_prefix=''):
        """Write a component as HTML"""
        indentation = ' ' * 2 * indent
        
        # Map component types to HTML elements
        type_to_element = {
            UIComponentType.LAYOUT: 'div',
            UIComponentType.BUTTON: 'button',
            UIComponentType.TEXT_FIELD: 'input',
            UIComponentType.LABEL: 'p',
            UIComponentType.IMAGE: 'img',
            UIComponentType.LIST: 'ul',
            UIComponentType.GRID: 'div',
            UIComponentType.NAVIGATION: 'nav',
            UIComponentType.MENU: 'nav',
            UIComponentType.DIALOG: 'div',
            UIComponentType.TAB: 'div',
            UIComponentType.CHECKBOX: 'input',
            UIComponentType.RADIO: 'input',
            UIComponentType.DROPDOWN: 'select',
            UIComponentType.SLIDER: 'input',
            UIComponentType.PROGRESS: 'progress',
            UIComponentType.CARD: 'div'
        }
        
        html_element = type_to_element.get(component.component_type, 'div')
        
        # Generate an identifier
        identifier = component.id if component.id else f"{component.component_type}_{hash(str(component)) % 1000}"
        full_id = f"{screen_prefix}_{identifier}"
        
        # Start opening tag
        file.write(f'{indentation}<{html_element}')
        
        # Add id and class
        file.write(f' id="{full_id}" class="{full_id}')
        
        # Add component type as a class
        file.write(f' {component.component_type}"')
        
        # Add specific attributes based on component type
        if component.component_type == UIComponentType.TEXT_FIELD:
            placeholder = component.properties.get('placeholder', '')
            if placeholder:
                file.write(f' placeholder="{placeholder}"')
                
            if component.properties.get('multiline', False):
                html_element = 'textarea'
                
        elif component.component_type == UIComponentType.CHECKBOX:
            file.write(' type="checkbox"')
            
        elif component.component_type == UIComponentType.RADIO:
            file.write(' type="radio"')
            
        elif component.component_type == UIComponentType.SLIDER:
            file.write(' type="range"')
            
        elif component.component_type == UIComponentType.IMAGE:
            src = component.properties.get('src', 'assets/placeholder.png')
            alt = component.properties.get('alt', 'Image')
            file.write(f' src="{src}" alt="{alt}"')
        
        # Handle empty/self-closing elements
        empty_elements = ['img', 'input', 'br', 'hr', 'meta', 'link']
        
        if not component.children and html_element in empty_elements:
            file.write('>')
        else:
            file.write('>')
            
            # Add text content for text components
            if component.component_type in [UIComponentType.BUTTON, UIComponentType.LABEL]:
                text = component.properties.get('text', '')
                if text:
                    file.write(text)
            
            # Add children
            if component.children:
                file.write('\n')
                for child in component.children:
                    self._write_html_component(file, child, indent + 1, screen_prefix)
                file.write(indentation)
            
            file.write(f'</{html_element}>')
        
        file.write('\n')
    
    def _apply_to_wpf_project(self, template, project_path):
        """Apply UI template to a WPF (Windows Presentation Foundation) project"""
        try:
            # Create the resource dictionary XAML file
            resources_dir = os.path.join(project_path, 'Resources')
            os.makedirs(resources_dir, exist_ok=True)
            
            theme_path = os.path.join(resources_dir, 'AppTheme.xaml')
            with open(theme_path, 'w') as f:
                f.write('<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n')
                f.write('                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">\n\n')
                
                # Color resources
                for name, value in template.style.colors.items():
                    # Convert hex color to WPF format if needed
                    if value.startswith('#'):
                        if len(value) == 7:  # #RRGGBB
                            value = value.replace('#', '#FF')  # Add alpha channel
                    
                    f.write(f'    <SolidColorBrush x:Key="{name}Color" Color="{value}" />\n')
                
                f.write('\n')
                
                # Double resources for dimensions
                for name, value in template.style.dimensions.items():
                    # Convert px values to numbers
                    if 'px' in value:
                        value = value.replace('px', '')
                    
                    try:
                        value_float = float(value)
                        f.write(f'    <sys:Double x:Key="{name}">{{value_float}}</sys:Double>\n')
                    except ValueError:
                        pass
                
                f.write('\n')
                
                # Button style
                f.write('    <Style x:Key="DefaultButtonStyle" TargetType="Button">\n')
                f.write('        <Setter Property="Background" Value="{StaticResource primaryColor}" />\n')
                f.write('        <Setter Property="Foreground" Value="White" />\n')
                f.write('        <Setter Property="Padding" Value="12,6" />\n')
                f.write(f'        <Setter Property="FontSize" Value="{template.style.typography.get("button", {}).get("size", "14px").replace("px", "")}" />\n')
                f.write('        <Setter Property="BorderThickness" Value="0" />\n')
                f.write('        <Setter Property="Template">\n')
                f.write('            <Setter.Value>\n')
                f.write('                <ControlTemplate TargetType="Button">\n')
                f.write('                    <Border Background="{TemplateBinding Background}"\n')
                f.write(f'                            CornerRadius="{template.style.dimensions.get("border_radius", "4px").replace("px", "")}"\n')
                f.write('                            Padding="{TemplateBinding Padding}">\n')
                f.write('                        <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" />\n')
                f.write('                    </Border>\n')
                f.write('                </ControlTemplate>\n')
                f.write('            </Setter.Value>\n')
                f.write('        </Setter>\n')
                f.write('    </Style>\n\n')
                
                # TextBox style
                f.write('    <Style x:Key="DefaultTextBoxStyle" TargetType="TextBox">\n')
                f.write('        <Setter Property="Background" Value="{StaticResource backgroundColor}" />\n')
                f.write('        <Setter Property="Foreground" Value="{StaticResource text_primaryColor}" />\n')
                f.write('        <Setter Property="Padding" Value="8,6" />\n')
                f.write(f'        <Setter Property="FontSize" Value="{template.style.typography.get("body1", {}).get("size", "16px").replace("px", "")}" />\n')
                f.write('        <Setter Property="BorderThickness" Value="1" />\n')
                f.write('        <Setter Property="BorderBrush" Value="{StaticResource secondaryColor}" />\n')
                f.write('        <Setter Property="Template">\n')
                f.write('            <Setter.Value>\n')
                f.write('                <ControlTemplate TargetType="TextBox">\n')
                f.write('                    <Border Background="{TemplateBinding Background}"\n')
                f.write('                            BorderBrush="{TemplateBinding BorderBrush}"\n')
                f.write('                            BorderThickness="{TemplateBinding BorderThickness}"\n')
                f.write(f'                            CornerRadius="{template.style.dimensions.get("border_radius", "4px").replace("px", "")}">\n')
                f.write('                        <ScrollViewer x:Name="PART_ContentHost" Margin="{TemplateBinding Padding}" />\n')
                f.write('                    </Border>\n')
                f.write('                </ControlTemplate>\n')
                f.write('            </Setter.Value>\n')
                f.write('        </Setter>\n')
                f.write('    </Style>\n')
                
                f.write('</ResourceDictionary>\n')
            
            # Create XAML files for each screen
            views_dir = os.path.join(project_path, 'Views')
            os.makedirs(views_dir, exist_ok=True)
            
            for screen_name, root_component in template.screens.items():
                xaml_path = os.path.join(views_dir, f"{screen_name.title()}Page.xaml")
                
                with open(xaml_path, 'w') as f:
                    f.write('<Page x:Class="YourNamespace.Views.{0}Page"\n'.format(screen_name.title()))
                    f.write('      xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n')
                    f.write('      xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"\n')
                    f.write('      xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"\n')
                    f.write('      xmlns:d="http://schemas.microsoft.com/expression/blend/2008"\n')
                    f.write('      mc:Ignorable="d"\n')
                    f.write('      Title="{0}">\n'.format(screen_name.replace('_', ' ').title()))
                    
                    # Write the component tree
                    f.write('    <Grid>\n')
                    self._write_wpf_component(f, root_component, 2)
                    f.write('    </Grid>\n')
                    
                    f.write('</Page>\n')
                
                # Create code-behind file
                cs_path = os.path.join(views_dir, f"{screen_name.title()}Page.xaml.cs")
                
                with open(cs_path, 'w') as f:
                    f.write('using System.Windows.Controls;\n\n')
                    f.write('namespace YourNamespace.Views\n')
                    f.write('{\n')
                    f.write('    /// <summary>\n')
                    f.write(f'    /// Interaction logic for {screen_name.title()}Page.xaml\n')
                    f.write('    /// </summary>\n')
                    f.write(f'    public partial class {screen_name.title()}Page : Page\n')
                    f.write('    {\n')
                    f.write(f'        public {screen_name.title()}Page()\n')
                    f.write('        {\n')
                    f.write('            InitializeComponent();\n')
                    f.write('        }\n')
                    f.write('    }\n')
                    f.write('}\n')
            
            # Update App.xaml
            app_path = os.path.join(project_path, 'App.xaml')
            if os.path.exists(app_path):
                # Read existing content
                with open(app_path, 'r') as f:
                    content = f.read()
                
                # Check if ResourceDictionary is already there
                if '<ResourceDictionary>' in content:
                    # Add to existing ResourceDictionary
                    lines = content.split('\n')
                    resource_dict_index = -1
                    
                    for i, line in enumerate(lines):
                        if '<ResourceDictionary>' in line:
                            resource_dict_index = i
                            break
                    
                    if resource_dict_index >= 0:
                        lines.insert(resource_dict_index + 1, 
                                    '                <ResourceDictionary Source="Resources/AppTheme.xaml"/>')
                        
                        with open(app_path, 'w') as f:
                            f.write('\n'.join(lines))
                else:
                    # Add new ResourceDictionary
                    lines = content.split('\n')
                    app_index = -1
                    
                    for i, line in enumerate(lines):
                        if '<Application.Resources>' in line:
                            app_index = i
                            break
                    
                    if app_index >= 0:
                        resource_dict = [
                            '        <ResourceDictionary>',
                            '            <ResourceDictionary.MergedDictionaries>',
                            '                <ResourceDictionary Source="Resources/AppTheme.xaml"/>',
                            '            </ResourceDictionary.MergedDictionaries>',
                            '        </ResourceDictionary>'
                        ]
                        
                        lines[app_index+1:app_index+1] = resource_dict
                        
                        with open(app_path, 'w') as f:
                            f.write('\n'.join(lines))
            else:
                # Create new App.xaml
                with open(app_path, 'w') as f:
                    f.write('<Application x:Class="YourNamespace.App"\n')
                    f.write('             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n')
                    f.write('             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"\n')
                    f.write('             StartupUri="MainWindow.xaml">\n')
                    f.write('    <Application.Resources>\n')
                    f.write('        <ResourceDictionary>\n')
                    f.write('            <ResourceDictionary.MergedDictionaries>\n')
                    f.write('                <ResourceDictionary Source="Resources/AppTheme.xaml"/>\n')
                    f.write('            </ResourceDictionary.MergedDictionaries>\n')
                    f.write('        </ResourceDictionary>\n')
                    f.write('    </Application.Resources>\n')
                    f.write('</Application>\n')
            
            # Copy assets
            images_dir = os.path.join(project_path, 'Images')
            os.makedirs(images_dir, exist_ok=True)
            
            for asset_name, asset_path in template.assets.items():
                if os.path.exists(asset_path):
                    dst_path = os.path.join(images_dir, os.path.basename(asset_path))
                    shutil.copy2(asset_path, dst_path)
            
            return {
                'success': True,
                'message': 'UI template applied to WPF project',
                'files_created': [
                    theme_path,
                    app_path
                ] + [os.path.join(views_dir, f"{name.title()}Page.xaml") for name in template.screens.keys()]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _write_wpf_component(self, file, component, indent=0):
        """Write a component as WPF XAML"""
        indentation = ' ' * 4 * indent
        
        # Map component types to WPF controls
        type_to_control = {
            UIComponentType.LAYOUT: 'Grid',
            UIComponentType.BUTTON: 'Button',
            UIComponentType.TEXT_FIELD: 'TextBox',
            UIComponentType.LABEL: 'TextBlock',
            UIComponentType.IMAGE: 'Image',
            UIComponentType.LIST: 'ListView',
            UIComponentType.GRID: 'Grid',
            UIComponentType.NAVIGATION: 'StackPanel',
            UIComponentType.MENU: 'Menu',
            UIComponentType.DIALOG: 'Border',
            UIComponentType.TAB: 'TabControl',
            UIComponentType.CHECKBOX: 'CheckBox',
            UIComponentType.RADIO: 'RadioButton',
            UIComponentType.DROPDOWN: 'ComboBox',
            UIComponentType.SLIDER: 'Slider',
            UIComponentType.PROGRESS: 'ProgressBar',
            UIComponentType.CARD: 'Border'
        }
        
        control_type = type_to_control.get(component.component_type, 'Border')
        
        # Start opening tag
        file.write(f'{indentation}<{control_type}')
        
        # Add name if ID is available
        if component.id:
            file.write(f' x:Name="{component.id}"')
        
        # Add style if available
        if component.component_type == UIComponentType.BUTTON:
            file.write(' Style="{StaticResource DefaultButtonStyle}"')
        elif component.component_type == UIComponentType.TEXT_FIELD:
            file.write(' Style="{StaticResource DefaultTextBoxStyle}"')
        
        # Add specific attributes based on component type
        if component.component_type == UIComponentType.BUTTON:
            text = component.properties.get('text', '')
            file.write(f' Content="{text}"')
            
        elif component.component_type == UIComponentType.LABEL:
            text = component.properties.get('text', '')
            file.write(f' Text="{text}"')
            
            # Text styling
            font_size = component.style.get('font-size')
            if font_size:
                font_size_value = font_size.replace('px', '')
                try:
                    font_size_value = float(font_size_value)
                    file.write(f' FontSize="{font_size_value}"')
                except ValueError:
                    pass
            
            color = component.style.get('color')
            if color:
                file.write(f' Foreground="{color}"')
            
        elif component.component_type == UIComponentType.TEXT_FIELD:
            placeholder = component.properties.get('placeholder', '')
            if placeholder:
                file.write(f' Text="{placeholder}"')
            
            if component.properties.get('multiline', False):
                file.write(' TextWrapping="Wrap" AcceptsReturn="True"')
            
        elif component.component_type == UIComponentType.IMAGE:
            src = component.properties.get('src', '/Images/placeholder.png')
            file.write(f' Source="{src}"')
            
        elif component.component_type == UIComponentType.CARD:
            file.write(' Background="{StaticResource surfaceColor}"')
            file.write(f' CornerRadius="{template.style.dimensions.get("border_radius", "4").replace("px", "")}"')
            file.write(' Padding="12"')
        
        # Add width and height if available
        width = component.style.get('width')
        if width and width != '100%':
            width_value = width.replace('px', '')
            try:
                width_value = float(width_value)
                file.write(f' Width="{width_value}"')
            except ValueError:
                pass
        
        height = component.style.get('height')
        if height and height != '100%':
            height_value = height.replace('px', '')
            try:
                height_value = float(height_value)
                file.write(f' Height="{height_value}"')
            except ValueError:
                pass
        
        # Add background if available
        bg_color = component.style.get('background')
        if bg_color and control_type not in ['Button', 'TextBox']:  # These use styles
            file.write(f' Background="{bg_color}"')
        
        # Add margin and padding if available
        margin = component.style.get('margin')
        if margin:
            margin_value = margin.replace('px', '')
            try:
                margin_value = float(margin_value)
                file.write(f' Margin="{margin_value}"')
            except ValueError:
                pass
        
        padding = component.style.get('padding')
        if padding and control_type not in ['Button', 'TextBox']:  # These use styles
            padding_value = padding.replace('px', '')
            try:
                padding_value = float(padding_value)
                file.write(f' Padding="{padding_value}"')
            except ValueError:
                pass
        
        # Add position if available
        if 'position' in component.style and component.style['position'] == 'absolute':
            left = component.style.get('left', '0px').replace('px', '')
            top = component.style.get('top', '0px').replace('px', '')
            file.write(' HorizontalAlignment="Left" VerticalAlignment="Top"')
            file.write(f' Margin="{left},{top},0,0"')
        
        # Close opening tag
        if not component.children:
            file.write(' />\n')
        else:
            file.write('>\n')
            
            # Write children
            for child in component.children:
                self._write_wpf_component(file, child, indent + 1)
            
            # Close tag
            file.write(f'{indentation}</{control_type}>\n')


# Create an instance for use in the application
ui_extractor = UIExtractor()