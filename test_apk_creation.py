#!/usr/bin/env python3
"""
Test script to verify APK creation functionality.
This script creates sample APKs and verifies they are properly generated.
"""

import os
import sys
import json
from apk_manager import apk_manager

def test_apk_creation():
    """Test APK creation functionality"""
    print("Testing APK Creation System")
    print("=" * 50)
    
    # Test 1: Create APK from template
    print("\n1. Testing APK creation from template...")
    
    custom_params = {
        'name': 'Test App',
        'package_name': 'com.test.myapp',
        'version': '1.0.0',
        'colors': {
            'colorPrimary': '#FF5722',
            'colorAccent': '#2196F3'
        }
    }
    
    result = apk_manager.create_from_template('basic_app', custom_params)
    
    if result['success']:
        print(f"✓ APK created successfully: {result['app_name']}")
        print(f"  Package: {result['package_name']}")
        print(f"  Path: {result['apk_path']}")
        
        # Verify file exists
        if os.path.exists(result['apk_path']):
            file_size = os.path.getsize(result['apk_path'])
            print(f"  File size: {file_size} bytes")
        else:
            print("✗ APK file not found!")
    else:
        print(f"✗ Failed to create APK: {result.get('error', 'Unknown error')}")
    
    # Test 2: Create custom APK
    print("\n2. Testing custom APK creation...")
    
    custom_spec = {
        'name': 'Custom Social App',
        'package_name': 'com.custom.social',
        'type': 'social',
        'version': '2.0.0',
        'version_code': 20,
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
        },
        'strings': {
            'welcome_msg': 'Welcome to Custom Social!',
            'share_photo': 'Share Photo',
            'connect': 'Connect'
        },
        'activities': [
            {'name': '.MainActivity', 'exported': True},
            {'name': '.ProfileActivity', 'exported': False}
        ]
    }
    
    result = apk_manager.create_apk(custom_spec)
    
    if result['success']:
        print(f"✓ Custom APK created successfully: {result['app_name']}")
        print(f"  Package: {result['package_name']}")
        print(f"  Path: {result['apk_path']}")
        
        # Verify file exists
        if os.path.exists(result['apk_path']):
            file_size = os.path.getsize(result['apk_path'])
            print(f"  File size: {file_size} bytes")
        else:
            print("✗ APK file not found!")
    else:
        print(f"✗ Failed to create custom APK: {result.get('error', 'Unknown error')}")
    
    # Test 3: List stored APKs
    print("\n3. Testing APK listing...")
    
    result = apk_manager.get_stored_apks()
    
    if result['success']:
        print(f"✓ Found {result['count']} stored APKs:")
        for apk in result['apks'][:5]:  # Show first 5
            print(f"  - {apk['app_name']} v{apk['version']} ({apk['formatted_size']})")
    else:
        print(f"✗ Failed to list APKs: {result.get('error', 'Unknown error')}")
    
    # Test 4: Analyze an APK
    if result['success'] and result['apks']:
        print("\n4. Testing APK analysis...")
        
        first_apk_path = result['apks'][0]['path']
        analysis_result = apk_manager.get_apk_analysis(first_apk_path)
        
        if analysis_result['success']:
            analysis = analysis_result['analysis']
            print(f"✓ APK analysis successful:")
            print(f"  App Name: {analysis.get('app_name', 'N/A')}")
            print(f"  Package: {analysis.get('package_name', 'N/A')}")
            print(f"  Version: {analysis.get('version_name', 'N/A')}")
            print(f"  Min SDK: {analysis.get('min_sdk_version', 'N/A')}")
            print(f"  Target SDK: {analysis.get('target_sdk_version', 'N/A')}")
            print(f"  Permissions: {len(analysis.get('permissions', []))}")
        else:
            print(f"✗ Failed to analyze APK: {analysis_result.get('error', 'Unknown error')}")
    
    # Test 5: Get available templates
    print("\n5. Testing template listing...")
    
    templates_result = apk_manager.get_available_templates()
    
    if templates_result['success']:
        print(f"✓ Found {len(templates_result['templates'])} templates:")
        for template in templates_result['templates']:
            print(f"  - {template['display_name']}: {template['description']}")
    else:
        print("✗ Failed to get templates")
    
    print("\n" + "=" * 50)
    print("APK Creation Test Complete!")

if __name__ == "__main__":
    try:
        test_apk_creation()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()