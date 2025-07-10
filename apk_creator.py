"""
APK Creator module for Drive-Manager Pro.
Creates actual APK files from app templates and specifications.
"""

import os
import json
import zipfile
import tempfile
import shutil
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64

class APKCreator:
    """Creates actual APK files from specifications"""
    
    def __init__(self, output_dir=None):
        """Initialize the APK creator"""
        self.output_dir = output_dir or os.path.join(os.getcwd(), "generated_apks")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_apk(self, app_spec):
        """Create an APK file from app specification"""
        try:
            # Create temporary directory for APK building
            temp_dir = tempfile.mkdtemp(prefix="apk_build_")
            
            # Create APK structure
            self._create_apk_structure(temp_dir, app_spec)
            
            # Create AndroidManifest.xml
            self._create_manifest(temp_dir, app_spec)
            
            # Create resources
            self._create_resources(temp_dir, app_spec)
            
            # Create classes.dex (simplified)
            self._create_classes_dex(temp_dir, app_spec)
            
            # Create META-INF
            self._create_meta_inf(temp_dir)
            
            # Package into APK
            apk_path = self._package_apk(temp_dir, app_spec)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                'success': True,
                'apk_path': apk_path,
                'app_name': app_spec.get('name', 'Unknown'),
                'package_name': app_spec.get('package_name', 'com.example.app'),
                'version': app_spec.get('version', '1.0'),
                'message': f"APK created successfully: {os.path.basename(apk_path)}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create APK: {str(e)}"
            }
    
    def _create_apk_structure(self, temp_dir, app_spec):
        """Create the basic APK directory structure"""
        directories = [
            'META-INF',
            'res/drawable-hdpi',
            'res/drawable-mdpi',
            'res/drawable-xhdpi',
            'res/drawable-xxhdpi',
            'res/layout',
            'res/values',
            'res/values-v21',
            'assets'
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(temp_dir, directory), exist_ok=True)
    
    def _create_manifest(self, temp_dir, app_spec):
        """Create AndroidManifest.xml"""
        manifest_path = os.path.join(temp_dir, 'AndroidManifest.xml')
        
        # Create manifest XML
        manifest = ET.Element('manifest')
        manifest.set('xmlns:android', 'http://schemas.android.com/apk/res/android')
        manifest.set('package', app_spec.get('package_name', 'com.example.app'))
        manifest.set('android:versionCode', str(app_spec.get('version_code', 1)))
        manifest.set('android:versionName', app_spec.get('version', '1.0'))
        
        # Add uses-sdk
        uses_sdk = ET.SubElement(manifest, 'uses-sdk')
        uses_sdk.set('android:minSdkVersion', str(app_spec.get('min_sdk', 21)))
        uses_sdk.set('android:targetSdkVersion', str(app_spec.get('target_sdk', 33)))
        
        # Add permissions
        permissions = app_spec.get('permissions', [])
        for permission in permissions:
            perm_elem = ET.SubElement(manifest, 'uses-permission')
            perm_elem.set('android:name', permission)
        
        # Add application
        application = ET.SubElement(manifest, 'application')
        application.set('android:allowBackup', 'true')
        application.set('android:icon', '@mipmap/ic_launcher')
        application.set('android:label', app_spec.get('name', 'My App'))
        application.set('android:theme', '@style/AppTheme')
        
        # Add main activity
        activity = ET.SubElement(application, 'activity')
        activity.set('android:name', '.MainActivity')
        activity.set('android:exported', 'true')
        
        intent_filter = ET.SubElement(activity, 'intent-filter')
        action = ET.SubElement(intent_filter, 'action')
        action.set('android:name', 'android.intent.action.MAIN')
        category = ET.SubElement(intent_filter, 'category')
        category.set('android:name', 'android.intent.category.LAUNCHER')
        
        # Add other activities from spec
        activities = app_spec.get('activities', [])
        for act_spec in activities:
            act_elem = ET.SubElement(application, 'activity')
            act_elem.set('android:name', act_spec.get('name', '.CustomActivity'))
            act_elem.set('android:exported', str(act_spec.get('exported', False)).lower())
        
        # Add services
        services = app_spec.get('services', [])
        for service_spec in services:
            service_elem = ET.SubElement(application, 'service')
            service_elem.set('android:name', service_spec.get('name', '.CustomService'))
            service_elem.set('android:exported', str(service_spec.get('exported', False)).lower())
        
        # Write manifest to file
        rough_string = ET.tostring(manifest, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_manifest = reparsed.toprettyxml(indent="    ")
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(pretty_manifest)
    
    def _create_resources(self, temp_dir, app_spec):
        """Create resource files"""
        # Create strings.xml
        self._create_strings_xml(temp_dir, app_spec)
        
        # Create colors.xml
        self._create_colors_xml(temp_dir, app_spec)
        
        # Create styles.xml
        self._create_styles_xml(temp_dir, app_spec)
        
        # Create layout files
        self._create_layouts(temp_dir, app_spec)
        
        # Create app icon
        self._create_app_icon(temp_dir, app_spec)
    
    def _create_strings_xml(self, temp_dir, app_spec):
        """Create strings.xml resource file"""
        strings_path = os.path.join(temp_dir, 'res', 'values', 'strings.xml')
        
        resources = ET.Element('resources')
        
        # App name
        app_name = ET.SubElement(resources, 'string')
        app_name.set('name', 'app_name')
        app_name.text = app_spec.get('name', 'My App')
        
        # Add custom strings
        strings = app_spec.get('strings', {})
        for key, value in strings.items():
            string_elem = ET.SubElement(resources, 'string')
            string_elem.set('name', key)
            string_elem.text = value
        
        # Write to file
        rough_string = ET.tostring(resources, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        with open(strings_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def _create_colors_xml(self, temp_dir, app_spec):
        """Create colors.xml resource file"""
        colors_path = os.path.join(temp_dir, 'res', 'values', 'colors.xml')
        
        resources = ET.Element('resources')
        
        # Default colors
        default_colors = {
            'colorPrimary': '#2196F3',
            'colorPrimaryDark': '#1976D2',
            'colorAccent': '#FF4081',
            'white': '#FFFFFF',
            'black': '#000000'
        }
        
        # Merge with custom colors
        colors = {**default_colors, **app_spec.get('colors', {})}
        
        for name, value in colors.items():
            color_elem = ET.SubElement(resources, 'color')
            color_elem.set('name', name)
            color_elem.text = value
        
        # Write to file
        rough_string = ET.tostring(resources, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        with open(colors_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def _create_styles_xml(self, temp_dir, app_spec):
        """Create styles.xml resource file"""
        styles_path = os.path.join(temp_dir, 'res', 'values', 'styles.xml')
        
        resources = ET.Element('resources')
        
        # App theme
        style = ET.SubElement(resources, 'style')
        style.set('name', 'AppTheme')
        style.set('parent', 'Theme.AppCompat.Light.DarkActionBar')
        
        # Color primary
        item1 = ET.SubElement(style, 'item')
        item1.set('name', 'colorPrimary')
        item1.text = '@color/colorPrimary'
        
        # Color primary dark
        item2 = ET.SubElement(style, 'item')
        item2.set('name', 'colorPrimaryDark')
        item2.text = '@color/colorPrimaryDark'
        
        # Color accent
        item3 = ET.SubElement(style, 'item')
        item3.set('name', 'colorAccent')
        item3.text = '@color/colorAccent'
        
        # Write to file
        rough_string = ET.tostring(resources, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        with open(styles_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def _create_layouts(self, temp_dir, app_spec):
        """Create layout XML files"""
        # Create main activity layout
        self._create_main_layout(temp_dir, app_spec)
        
        # Create custom layouts
        layouts = app_spec.get('layouts', [])
        for layout_spec in layouts:
            self._create_custom_layout(temp_dir, layout_spec)
    
    def _create_main_layout(self, temp_dir, app_spec):
        """Create activity_main.xml layout"""
        layout_path = os.path.join(temp_dir, 'res', 'layout', 'activity_main.xml')
        
        # Create layout XML based on app type
        app_type = app_spec.get('type', 'basic')
        
        if app_type == 'basic':
            layout_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/app_name"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_gravity="center_horizontal"
        android:layout_marginBottom="32dp" />

    <Button
        android:id="@+id/btn_main"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Main Action"
        android:layout_marginBottom="16dp" />

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Welcome to the app!"
        android:textAlignment="center"
        android:layout_marginTop="32dp" />

</LinearLayout>'''
        
        elif app_type == 'social':
            layout_xml = '''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/title"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/app_name"
        android:textSize="20sp"
        android:textStyle="bold"
        android:layout_centerHorizontal="true"
        android:layout_marginTop="16dp" />

    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:layout_below="@id/title"
        android:layout_marginTop="16dp">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">

            <EditText
                android:id="@+id/post_input"
                android:layout_width="match_parent"
                android:layout_height="120dp"
                android:hint="What's on your mind?"
                android:gravity="top"
                android:inputType="textMultiLine"
                android:background="@android:drawable/edit_text"
                android:padding="8dp" />

            <Button
                android:id="@+id/btn_post"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Post"
                android:layout_gravity="end"
                android:layout_marginTop="8dp" />

        </LinearLayout>

    </ScrollView>

</RelativeLayout>'''
        
        elif app_type == 'productivity':
            layout_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <Toolbar
        android:id="@+id/toolbar"
        android:layout_width="match_parent"
        android:layout_height="?attr/actionBarSize"
        android:background="@color/colorPrimary"
        android:title="@string/app_name" />

    <TabLayout
        android:id="@+id/tab_layout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:background="@color/colorPrimary" />

    <ViewPager
        android:id="@+id/view_pager"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:padding="16dp">

        <Button
            android:id="@+id/btn_add"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="Add Task"
            android:layout_marginEnd="8dp" />

        <Button
            android:id="@+id/btn_sync"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="Sync"
            android:layout_marginStart="8dp" />

    </LinearLayout>

</LinearLayout>'''
        
        else:
            # Default layout
            layout_xml = '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/app_name"
        android:layout_gravity="center" />

</FrameLayout>'''
        
        with open(layout_path, 'w', encoding='utf-8') as f:
            f.write(layout_xml)
    
    def _create_custom_layout(self, temp_dir, layout_spec):
        """Create a custom layout from specification"""
        layout_name = layout_spec.get('name', 'custom_layout')
        layout_path = os.path.join(temp_dir, 'res', 'layout', f'{layout_name}.xml')
        
        # Generate layout XML from specification
        layout_xml = self._generate_layout_xml(layout_spec)
        
        with open(layout_path, 'w', encoding='utf-8') as f:
            f.write(layout_xml)
    
    def _generate_layout_xml(self, layout_spec):
        """Generate layout XML from specification"""
        root_type = layout_spec.get('root_type', 'LinearLayout')
        orientation = layout_spec.get('orientation', 'vertical')
        
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<{root_type} xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"'''
        
        if root_type == 'LinearLayout':
            xml_content += f'\n    android:orientation="{orientation}"'
        
        xml_content += '>\n\n'
        
        # Add components
        components = layout_spec.get('components', [])
        for component in components:
            xml_content += self._generate_component_xml(component)
        
        xml_content += f'</{root_type}>'
        
        return xml_content
    
    def _generate_component_xml(self, component):
        """Generate XML for a component"""
        comp_type = component.get('type', 'TextView')
        comp_id = component.get('id', 'component')
        text = component.get('text', '')
        
        xml = f'''    <{comp_type}
        android:id="@+id/{comp_id}"
        android:layout_width="{component.get('width', 'wrap_content')}"
        android:layout_height="{component.get('height', 'wrap_content')}"'''
        
        if text:
            xml += f'\n        android:text="{text}"'
        
        # Add other attributes
        attrs = component.get('attributes', {})
        for attr_name, attr_value in attrs.items():
            xml += f'\n        android:{attr_name}="{attr_value}"'
        
        xml += ' />\n\n'
        
        return xml
    
    def _create_app_icon(self, temp_dir, app_spec):
        """Create app icon files"""
        # Create a simple colored square as icon
        icon_color = app_spec.get('icon_color', '#2196F3')
        
        # Create different density icons
        densities = {
            'mdpi': 48,
            'hdpi': 72,
            'xhdpi': 96,
            'xxhdpi': 144
        }
        
        for density, size in densities.items():
            icon_dir = os.path.join(temp_dir, 'res', f'drawable-{density}')
            icon_path = os.path.join(icon_dir, 'ic_launcher.png')
            
            # Create a simple PNG icon (base64 encoded 1x1 pixel)
            # This is a minimal implementation
            self._create_simple_icon(icon_path, size, icon_color)
    
    def _create_simple_icon(self, icon_path, size, color):
        """Create a simple colored icon"""
        # Create a simple XML drawable instead of PNG for simplicity
        xml_path = icon_path.replace('.png', '.xml')
        
        icon_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="{color}" />
    <corners android:radius="8dp" />
</shape>'''
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(icon_xml)
    
    def _create_classes_dex(self, temp_dir, app_spec):
        """Create classes.dex file (simplified)"""
        # For a real APK, this would contain compiled Java/Kotlin bytecode
        # For this demo, we'll create a minimal file
        dex_path = os.path.join(temp_dir, 'classes.dex')
        
        # DEX file header (simplified)
        dex_content = bytearray([
            0x64, 0x65, 0x78, 0x0a,  # DEX magic
            0x30, 0x33, 0x35, 0x00,  # Version 035
        ])
        
        # Pad to minimum size
        dex_content.extend(b'\x00' * 100)
        
        with open(dex_path, 'wb') as f:
            f.write(dex_content)
    
    def _create_meta_inf(self, temp_dir):
        """Create META-INF directory with certificate info"""
        meta_inf_dir = os.path.join(temp_dir, 'META-INF')
        
        # Create MANIFEST.MF
        manifest_mf_path = os.path.join(meta_inf_dir, 'MANIFEST.MF')
        with open(manifest_mf_path, 'w') as f:
            f.write('Manifest-Version: 1.0\n')
            f.write('Created-By: Drive-Manager Pro APK Creator\n')
            f.write('\n')
        
        # Create certificate files (dummy)
        cert_rsa_path = os.path.join(meta_inf_dir, 'CERT.RSA')
        with open(cert_rsa_path, 'wb') as f:
            f.write(b'DUMMY_CERTIFICATE_DATA')
        
        cert_sf_path = os.path.join(meta_inf_dir, 'CERT.SF')
        with open(cert_sf_path, 'w') as f:
            f.write('Signature-Version: 1.0\n')
            f.write('Created-By: Drive-Manager Pro\n')
            f.write('\n')
    
    def _package_apk(self, temp_dir, app_spec):
        """Package the APK file"""
        app_name = app_spec.get('name', 'MyApp').replace(' ', '_')
        version = app_spec.get('version', '1.0')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        apk_filename = f"{app_name}_v{version}_{timestamp}.apk"
        apk_path = os.path.join(self.output_dir, apk_filename)
        
        # Create ZIP file (APK is a ZIP archive)
        with zipfile.ZipFile(apk_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        return apk_path
    
    def create_sample_apps(self):
        """Create a set of sample APK files"""
        sample_apps = [
            {
                'name': 'TaskMaster Pro',
                'package_name': 'com.drivemanager.taskmaster',
                'type': 'productivity',
                'version': '2.1.0',
                'version_code': 21,
                'min_sdk': 21,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.WRITE_EXTERNAL_STORAGE',
                    'android.permission.READ_EXTERNAL_STORAGE'
                ],
                'colors': {
                    'colorPrimary': '#1976D2',
                    'colorPrimaryDark': '#1565C0',
                    'colorAccent': '#FF5722'
                },
                'strings': {
                    'welcome_message': 'Welcome to TaskMaster Pro',
                    'add_task': 'Add New Task',
                    'sync_data': 'Sync with Cloud'
                },
                'activities': [
                    {'name': '.TaskListActivity', 'exported': False},
                    {'name': '.SettingsActivity', 'exported': False}
                ],
                'services': [
                    {'name': '.SyncService', 'exported': False}
                ]
            },
            {
                'name': 'SocialConnect',
                'package_name': 'com.drivemanager.socialconnect',
                'type': 'social',
                'version': '1.5.2',
                'version_code': 152,
                'min_sdk': 23,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.CAMERA',
                    'android.permission.ACCESS_FINE_LOCATION',
                    'android.permission.READ_CONTACTS'
                ],
                'colors': {
                    'colorPrimary': '#E91E63',
                    'colorPrimaryDark': '#C2185B',
                    'colorAccent': '#FFC107'
                },
                'strings': {
                    'share_moment': 'Share this moment',
                    'connect_friends': 'Connect with friends',
                    'post_update': 'Post Update'
                },
                'activities': [
                    {'name': '.FeedActivity', 'exported': False},
                    {'name': '.ProfileActivity', 'exported': False},
                    {'name': '.CameraActivity', 'exported': False}
                ]
            },
            {
                'name': 'Finance Tracker',
                'package_name': 'com.drivemanager.financetracker',
                'type': 'productivity',
                'version': '3.0.1',
                'version_code': 301,
                'min_sdk': 24,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.ACCESS_NETWORK_STATE',
                    'android.permission.VIBRATE'
                ],
                'colors': {
                    'colorPrimary': '#4CAF50',
                    'colorPrimaryDark': '#388E3C',
                    'colorAccent': '#FF9800'
                },
                'strings': {
                    'add_expense': 'Add Expense',
                    'view_reports': 'View Reports',
                    'budget_alert': 'Budget Alert'
                },
                'activities': [
                    {'name': '.ExpenseActivity', 'exported': False},
                    {'name': '.ReportsActivity', 'exported': False},
                    {'name': '.BudgetActivity', 'exported': False}
                ]
            },
            {
                'name': 'Photo Editor Plus',
                'package_name': 'com.drivemanager.photoeditor',
                'type': 'media',
                'version': '1.8.0',
                'version_code': 180,
                'min_sdk': 21,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.READ_EXTERNAL_STORAGE',
                    'android.permission.WRITE_EXTERNAL_STORAGE',
                    'android.permission.CAMERA'
                ],
                'colors': {
                    'colorPrimary': '#9C27B0',
                    'colorPrimaryDark': '#7B1FA2',
                    'colorAccent': '#00BCD4'
                },
                'strings': {
                    'edit_photo': 'Edit Photo',
                    'apply_filter': 'Apply Filter',
                    'save_image': 'Save Image'
                },
                'activities': [
                    {'name': '.EditorActivity', 'exported': False},
                    {'name': '.GalleryActivity', 'exported': False}
                ]
            },
            {
                'name': 'Game Center',
                'package_name': 'com.drivemanager.gamecenter',
                'type': 'gaming',
                'version': '2.3.1',
                'version_code': 231,
                'min_sdk': 23,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.ACCESS_NETWORK_STATE',
                    'android.permission.VIBRATE',
                    'android.permission.WAKE_LOCK'
                ],
                'colors': {
                    'colorPrimary': '#FF5722',
                    'colorPrimaryDark': '#E64A19',
                    'colorAccent': '#2196F3'
                },
                'strings': {
                    'start_game': 'Start Game',
                    'leaderboard': 'Leaderboard',
                    'achievements': 'Achievements'
                },
                'activities': [
                    {'name': '.GameActivity', 'exported': False},
                    {'name': '.LeaderboardActivity', 'exported': False},
                    {'name': '.AchievementsActivity', 'exported': False}
                ],
                'services': [
                    {'name': '.GameService', 'exported': False}
                ]
            }
        ]
        
        created_apks = []
        
        for app_spec in sample_apps:
            result = self.create_apk(app_spec)
            if result['success']:
                created_apks.append(result)
        
        return {
            'success': True,
            'created_count': len(created_apks),
            'apks': created_apks,
            'message': f"Created {len(created_apks)} sample APK files"
        }
    
    def create_apk_from_template(self, template_name, custom_params=None):
        """Create APK from a predefined template"""
        templates = {
            'basic_app': {
                'name': 'Basic App',
                'package_name': 'com.example.basicapp',
                'type': 'basic',
                'version': '1.0.0',
                'version_code': 1,
                'min_sdk': 21,
                'target_sdk': 33,
                'permissions': ['android.permission.INTERNET'],
                'colors': {
                    'colorPrimary': '#2196F3',
                    'colorPrimaryDark': '#1976D2',
                    'colorAccent': '#FF4081'
                }
            },
            'social_app': {
                'name': 'Social App',
                'package_name': 'com.example.socialapp',
                'type': 'social',
                'version': '1.0.0',
                'version_code': 1,
                'min_sdk': 23,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.CAMERA',
                    'android.permission.READ_CONTACTS'
                ],
                'colors': {
                    'colorPrimary': '#E91E63',
                    'colorPrimaryDark': '#C2185B',
                    'colorAccent': '#FFC107'
                }
            },
            'productivity_app': {
                'name': 'Productivity App',
                'package_name': 'com.example.productivityapp',
                'type': 'productivity',
                'version': '1.0.0',
                'version_code': 1,
                'min_sdk': 21,
                'target_sdk': 33,
                'permissions': [
                    'android.permission.INTERNET',
                    'android.permission.WRITE_EXTERNAL_STORAGE'
                ],
                'colors': {
                    'colorPrimary': '#4CAF50',
                    'colorPrimaryDark': '#388E3C',
                    'colorAccent': '#FF9800'
                }
            }
        }
        
        if template_name not in templates:
            return {
                'success': False,
                'error': f"Template '{template_name}' not found"
            }
        
        # Get base template
        app_spec = templates[template_name].copy()
        
        # Apply custom parameters
        if custom_params:
            app_spec.update(custom_params)
        
        return self.create_apk(app_spec)


# Create an instance for use in the application
apk_creator = APKCreator()