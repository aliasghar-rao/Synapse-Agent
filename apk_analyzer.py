"""
APK Analyzer module for Drive-Manager Pro.
Provides in-depth APK analysis, extraction, and management functionality.
"""

import os
import re
import time
import tempfile
import zipfile
import shutil
import json
import hashlib
import subprocess
from datetime import datetime
import xml.etree.ElementTree as ET

# Optional imports - will be used if available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import androguard.core.bytecodes.apk as apk
    import androguard.core.bytecodes.dvm as dvm
    ANDROGUARD_AVAILABLE = True
except ImportError:
    ANDROGUARD_AVAILABLE = False


class APKAnalyzer:
    """Class for analyzing APK files"""
    
    def __init__(self, cache_dir=None):
        """Initialize the APK analyzer with optional cache directory"""
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), 'drivemanager_apk_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Check for external tools
        self.aapt_available = self._check_aapt_available()
        self.adb_available = self._check_adb_available()
        
    def _check_aapt_available(self):
        """Check if Android Asset Packaging Tool (aapt) is available"""
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.run(['aapt', 'version'], stdout=devnull, stderr=devnull)
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            # Try to find aapt in common locations
            potential_paths = [
                os.path.expanduser("~/Library/Android/sdk/build-tools/"),  # macOS
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'build-tools'),  # Windows
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'build-tools')  # Generic
            ]
            
            for base_path in potential_paths:
                if os.path.exists(base_path):
                    # Look for the latest version
                    versions = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
                    versions.sort(reverse=True)
                    
                    for version in versions:
                        aapt_path = os.path.join(base_path, version, 'aapt')
                        if os.path.exists(aapt_path) or os.path.exists(aapt_path + '.exe'):
                            return True
                            
            return False
            
    def _check_adb_available(self):
        """Check if Android Debug Bridge (adb) is available"""
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.run(['adb', 'version'], stdout=devnull, stderr=devnull)
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def analyze_apk(self, apk_path):
        """Analyze an APK file and extract detailed information"""
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file does not exist'}
            
        # Calculate APK hash for caching
        apk_hash = self._calculate_file_hash(apk_path)
        cache_file = os.path.join(self.cache_dir, f"{apk_hash}_analysis.json")
        
        # Check if we have a cached analysis
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_analysis = json.load(f)
                    
                # Verify the cached analysis is for the same file
                if cached_analysis.get('apk_path') == apk_path:
                    cached_analysis['from_cache'] = True
                    return cached_analysis
            except Exception:
                # If there's an error reading the cache, proceed with fresh analysis
                pass
        
        # Start a new analysis
        analysis_result = {
            'success': True,
            'apk_path': apk_path,
            'apk_size': os.path.getsize(apk_path),
            'apk_name': os.path.basename(apk_path),
            'analysis_time': datetime.now().isoformat(),
            'apk_hash': apk_hash,
            'from_cache': False
        }
        
        # Try different analysis methods based on available tools
        if ANDROGUARD_AVAILABLE:
            androguard_result = self._analyze_with_androguard(apk_path)
            if androguard_result.get('success', False):
                analysis_result.update(androguard_result)
                analysis_result['analysis_method'] = 'androguard'
            else:
                # Fall back to other methods
                analysis_result['androguard_error'] = androguard_result.get('error')
                
        if not analysis_result.get('package_name') and self.aapt_available:
            aapt_result = self._analyze_with_aapt(apk_path)
            if aapt_result.get('success', False):
                analysis_result.update(aapt_result)
                analysis_result['analysis_method'] = analysis_result.get('analysis_method', '') + '+aapt'
            else:
                analysis_result['aapt_error'] = aapt_result.get('error')
                
        # If all else fails, extract and analyze manually
        if not analysis_result.get('package_name'):
            manual_result = self._analyze_manual_extraction(apk_path)
            if manual_result.get('success', False):
                analysis_result.update(manual_result)
                analysis_result['analysis_method'] = 'manual_extraction'
            else:
                analysis_result['manual_extraction_error'] = manual_result.get('error')
                analysis_result['success'] = False
                analysis_result['error'] = "Failed to analyze APK with any available method"
        
        # Extract icon and additional resources
        if analysis_result.get('success', False):
            icon_result = self._extract_app_icon(apk_path, analysis_result.get('package_name', ''))
            if icon_result.get('success', False):
                analysis_result['icon_path'] = icon_result.get('icon_path')
            
            # Add platform compatibility info
            analysis_result['platform_compatibility'] = self._check_platform_compatibility(analysis_result)
            
            # Add security analysis
            analysis_result['security_analysis'] = self._analyze_security(apk_path, analysis_result)
            
            # Cache the analysis results
            try:
                with open(cache_file, 'w') as f:
                    json.dump(analysis_result, f)
            except Exception as e:
                analysis_result['cache_error'] = str(e)
        
        return analysis_result
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of file"""
        if not os.path.exists(file_path):
            return None
            
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return None
    
    def _analyze_with_androguard(self, apk_path):
        """Analyze APK using Androguard library"""
        result = {'success': False}
        
        try:
            a = apk.APK(apk_path)
            
            # Basic app info
            result['package_name'] = a.get_package()
            result['app_name'] = a.get_app_name()
            result['version_name'] = a.get_androidversion_name()
            result['version_code'] = a.get_androidversion_code()
            result['min_sdk'] = a.get_min_sdk_version()
            result['target_sdk'] = a.get_target_sdk_version()
            result['max_sdk'] = a.get_max_sdk_version()
            
            # App signing
            cert = a.get_certificates()
            if cert:
                result['signing'] = {
                    'issuer': str(cert[0].issuer),
                    'subject': str(cert[0].subject),
                    'serial_number': str(cert[0].serial_number),
                    'fingerprint_md5': cert[0].fingerprint_md5.hex(),
                    'fingerprint_sha1': cert[0].fingerprint_sha1.hex(),
                    'fingerprint_sha256': cert[0].fingerprint_sha256.hex(),
                    'signature_algorithm': cert[0].signature_algorithm
                }
            
            # Components
            result['activities'] = a.get_activities()
            result['services'] = a.get_services()
            result['receivers'] = a.get_receivers()
            result['providers'] = a.get_providers()
            
            # Main activity
            result['main_activity'] = a.get_main_activity()
            
            # Permissions
            result['permissions'] = a.get_permissions()
            result['declared_permissions'] = a.get_declared_permissions()
            
            # Features
            result['features'] = a.get_features()
            
            # Libraries
            result['libraries'] = a.get_libraries()
            
            # File analysis
            result['files'] = []
            for file_path in a.get_files():
                # Limit to interesting files
                if file_path.endswith('.xml') or file_path.endswith('.dex') or '/res/' in file_path:
                    file_info = {
                        'path': file_path,
                        'size': len(a.get_file(file_path)) if a.get_file(file_path) else 0
                    }
                    result['files'].append(file_info)
            
            result['dex_files'] = a.get_dex_names()
            
            # Success!
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def _analyze_with_aapt(self, apk_path):
        """Analyze APK using aapt command line tool"""
        result = {'success': False}
        
        try:
            # Run aapt dump badging
            cmd = ['aapt', 'dump', 'badging', apk_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                result['error'] = process.stderr
                return result
                
            output = process.stdout
            
            # Extract basic info with regex
            package_match = re.search(r"package: name='([^']+)'", output)
            if package_match:
                result['package_name'] = package_match.group(1)
            
            version_name_match = re.search(r"versionName='([^']+)'", output)
            if version_name_match:
                result['version_name'] = version_name_match.group(1)
            
            version_code_match = re.search(r"versionCode='(\d+)'", output)
            if version_code_match:
                result['version_code'] = version_code_match.group(1)
            
            app_name_match = re.search(r"application-label:'([^']+)'", output)
            if app_name_match:
                result['app_name'] = app_name_match.group(1)
            
            # SDK versions
            sdk_min_match = re.search(r"sdkVersion:'(\d+)'", output)
            if sdk_min_match:
                result['min_sdk'] = sdk_min_match.group(1)
                
            sdk_target_match = re.search(r"targetSdkVersion:'(\d+)'", output)
            if sdk_target_match:
                result['target_sdk'] = sdk_target_match.group(1)
            
            # Extract permissions
            permissions = []
            permission_matches = re.finditer(r"uses-permission: name='([^']+)'", output)
            for match in permission_matches:
                permissions.append(match.group(1))
            result['permissions'] = permissions
            
            # Features
            features = []
            feature_matches = re.finditer(r"uses-feature: name='([^']+)'", output)
            for match in feature_matches:
                features.append(match.group(1))
            result['features'] = features
            
            # Activities and other components via dumpsys
            result['activities'] = []
            activity_matches = re.finditer(r"launchable-activity: name='([^']+)'", output)
            for match in activity_matches:
                result['activities'].append(match.group(1))
            
            # Check for main activity
            main_activity_match = re.search(r"launchable-activity: name='([^']+)'", output)
            if main_activity_match:
                result['main_activity'] = main_activity_match.group(1)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def _analyze_manual_extraction(self, apk_path):
        """Analyze APK by extracting and parsing its contents manually"""
        result = {'success': False}
        extraction_dir = None
        
        try:
            # Create a temporary directory for extraction
            extraction_dir = tempfile.mkdtemp(prefix='apk_analysis_')
            
            # Extract the APK using zipfile
            with zipfile.ZipFile(apk_path, 'r') as z:
                z.extractall(extraction_dir)
            
            # Look for AndroidManifest.xml
            manifest_path = os.path.join(extraction_dir, 'AndroidManifest.xml')
            if not os.path.exists(manifest_path):
                result['error'] = "AndroidManifest.xml not found in APK"
                return result
            
            # Binary XML can't be directly parsed, looking for package name in other files
            # Check for classes.dex (basic validation)
            if os.path.exists(os.path.join(extraction_dir, 'classes.dex')):
                result['has_dex'] = True
            
            # Look for resource files to extract app name
            res_dir = os.path.join(extraction_dir, 'res')
            if os.path.exists(res_dir):
                # Check for app name in strings.xml files
                for root, dirs, files in os.walk(res_dir):
                    for file in files:
                        if file == 'strings.xml':
                            try:
                                tree = ET.parse(os.path.join(root, file))
                                for string in tree.findall(".//string[@name='app_name']"):
                                    result['app_name'] = string.text
                                    break
                            except Exception:
                                pass
            
            # Look for assets
            assets_dir = os.path.join(extraction_dir, 'assets')
            if os.path.exists(assets_dir):
                result['has_assets'] = True
                result['asset_count'] = len(os.listdir(assets_dir))
            
            # Count resource types
            if os.path.exists(res_dir):
                resource_types = {}
                for res_type in os.listdir(res_dir):
                    if os.path.isdir(os.path.join(res_dir, res_type)):
                        resource_types[res_type] = len(os.listdir(os.path.join(res_dir, res_type)))
                result['resource_types'] = resource_types
            
            # Look for potentially sensitive files
            sensitive_patterns = [
                'password', 'key', 'secret', 'credential', 'token', 'apikey',
                'firebase', 'google-services.json', '.keystore', '.jks'
            ]
            
            sensitive_files = []
            for root, dirs, files in os.walk(extraction_dir):
                for file in files:
                    lower_file = file.lower()
                    if any(pattern in lower_file for pattern in sensitive_patterns):
                        sensitive_files.append(os.path.relpath(os.path.join(root, file), extraction_dir))
            
            if sensitive_files:
                result['sensitive_files'] = sensitive_files
            
            # If package name is still unknown, make an educated guess from structure
            if not result.get('package_name'):
                # Look at folder structure in classes.dex
                smali_dir = os.path.join(extraction_dir, 'smali')
                if os.path.exists(smali_dir):
                    # Navigate the directory structure to find likely package
                    current_dir = smali_dir
                    parts = []
                    
                    # Depth-first search for main activity class
                    for _ in range(5):  # Max depth of 5
                        dirs = [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]
                        if not dirs:
                            break
                            
                        # Prefer common package prefixes
                        priority_prefixes = ['com', 'org', 'net', 'io', 'app']
                        for prefix in priority_prefixes:
                            if prefix in dirs:
                                parts.append(prefix)
                                current_dir = os.path.join(current_dir, prefix)
                                break
                        else:
                            # If no priority prefix, just take the first directory
                            parts.append(dirs[0])
                            current_dir = os.path.join(current_dir, dirs[0])
                    
                    if parts:
                        result['package_name'] = '.'.join(parts)
                        result['package_name_source'] = 'guessed_from_structure'
            
            # Extract file count and size statistics
            file_stats = {}
            total_files = 0
            
            for root, dirs, files in os.walk(extraction_dir):
                dir_name = os.path.basename(root)
                if dir_name not in file_stats:
                    file_stats[dir_name] = {'count': 0, 'size': 0}
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    file_stats[dir_name]['count'] += 1
                    file_stats[dir_name]['size'] += file_size
                    total_files += 1
            
            result['file_stats'] = file_stats
            result['total_files'] = total_files
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        finally:
            # Clean up extraction directory
            if extraction_dir and os.path.exists(extraction_dir):
                shutil.rmtree(extraction_dir, ignore_errors=True)
            
        return result
    
    def _extract_app_icon(self, apk_path, package_name):
        """Extract the app icon from the APK"""
        result = {'success': False}
        extraction_dir = None
        
        try:
            # Create a temporary directory for extraction
            extraction_dir = tempfile.mkdtemp(prefix='apk_icon_')
            
            # Extract the APK using zipfile
            with zipfile.ZipFile(apk_path, 'r') as z:
                z.extractall(extraction_dir)
            
            # Look for icon files in common locations
            icon_path = None
            
            # Check for ic_launcher.png in different drawable folders
            for dpi in ['xxxhdpi', 'xxhdpi', 'xhdpi', 'hdpi', 'mdpi']:
                icon_path = os.path.join(extraction_dir, 'res', f'drawable-{dpi}', 'ic_launcher.png')
                if os.path.exists(icon_path):
                    break
                    
                # Also check without -dpi suffix
                icon_path = os.path.join(extraction_dir, 'res', 'drawable', 'ic_launcher.png')
                if os.path.exists(icon_path):
                    break
            
            # If no icon found, try to find any PNG in drawable folders
            if not icon_path or not os.path.exists(icon_path):
                for root, dirs, files in os.walk(os.path.join(extraction_dir, 'res')):
                    if 'drawable' in root.lower():
                        for file in files:
                            if file.endswith('.png'):
                                icon_path = os.path.join(root, file)
                                break
                        if icon_path:
                            break
            
            # If icon found, copy to cache directory
            if icon_path and os.path.exists(icon_path):
                # Create a sanitized filename based on package name
                sanitized_name = ''.join(c for c in package_name if c.isalnum() or c == '.')
                cached_icon_path = os.path.join(self.cache_dir, f"{sanitized_name}_icon.png")
                
                # Resize the icon if PIL is available
                if PIL_AVAILABLE:
                    img = Image.open(icon_path)
                    img = img.resize((128, 128), Image.LANCZOS)
                    img.save(cached_icon_path)
                else:
                    # Otherwise just copy the file
                    shutil.copy2(icon_path, cached_icon_path)
                
                result['icon_path'] = cached_icon_path
                result['success'] = True
            else:
                result['error'] = "Could not find app icon"
                
        except Exception as e:
            result['error'] = str(e)
            
        finally:
            # Clean up extraction directory
            if extraction_dir and os.path.exists(extraction_dir):
                shutil.rmtree(extraction_dir, ignore_errors=True)
            
        return result
    
    def _check_platform_compatibility(self, apk_info):
        """Check platform compatibility of the APK"""
        compatibility = {
            'android': True,
            'windows': False,
            'macos': False,
            'linux': False,
            'compatible_android_versions': []
        }
        
        # Check Android compatibility based on min/target SDK
        min_sdk = apk_info.get('min_sdk')
        target_sdk = apk_info.get('target_sdk')
        
        sdk_to_version = {
            '1': '1.0',
            '2': '1.1',
            '3': '1.5',
            '4': '1.6',
            '5': '2.0',
            '6': '2.0.1',
            '7': '2.1',
            '8': '2.2',
            '9': '2.3',
            '10': '2.3.3',
            '11': '3.0',
            '12': '3.1',
            '13': '3.2',
            '14': '4.0',
            '15': '4.0.3',
            '16': '4.1',
            '17': '4.2',
            '18': '4.3',
            '19': '4.4',
            '21': '5.0',
            '22': '5.1',
            '23': '6.0',
            '24': '7.0',
            '25': '7.1',
            '26': '8.0',
            '27': '8.1',
            '28': '9.0',
            '29': '10.0',
            '30': '11.0',
            '31': '12.0',
            '32': '12.1',
            '33': '13.0',
            '34': '14.0',
            '35': '15.0'
        }
        
        if min_sdk:
            min_version = sdk_to_version.get(str(min_sdk), f"SDK {min_sdk}")
            compatibility['min_android_version'] = min_version
            
            # Generate list of compatible Android versions
            for sdk, version in sdk_to_version.items():
                if int(sdk) >= int(min_sdk):
                    compatibility['compatible_android_versions'].append({
                        'sdk': sdk,
                        'version': version
                    })
        
        if target_sdk:
            target_version = sdk_to_version.get(str(target_sdk), f"SDK {target_sdk}")
            compatibility['target_android_version'] = target_version
        
        # Check for emulator support
        compatibility['emulator_support'] = {
            'bluestacks': True,
            'nox': True,
            'ldplayer': True,
            'memu': True,
            'genymotion': True
        }
        
        # Check for Windows compatibility with WSA (Windows Subsystem for Android)
        if min_sdk:
            # WSA supports Android 11 (API 30) and higher
            compatibility['windows_wsa'] = int(min_sdk) <= 30
        
        # Check for ChromeOS compatibility
        if min_sdk:
            # ChromeOS supports Android 9.0+ apps well
            compatibility['chromeos'] = int(min_sdk) <= 28
        
        return compatibility
    
    def _analyze_security(self, apk_path, apk_info):
        """Perform security analysis on the APK"""
        security = {
            'permissions': {
                'dangerous': [],
                'normal': [],
                'signature': [],
                'unknown': []
            },
            'risky_components': [],
            'certificate_info': {},
            'potential_vulnerabilities': []
        }
        
        # Categorize permissions by protection level
        dangerous_permissions = [
            'android.permission.ACCESS_FINE_LOCATION',
            'android.permission.ACCESS_COARSE_LOCATION',
            'android.permission.READ_CONTACTS',
            'android.permission.WRITE_CONTACTS',
            'android.permission.READ_CALL_LOG',
            'android.permission.WRITE_CALL_LOG',
            'android.permission.READ_CALENDAR',
            'android.permission.WRITE_CALENDAR',
            'android.permission.READ_EXTERNAL_STORAGE',
            'android.permission.WRITE_EXTERNAL_STORAGE',
            'android.permission.CAMERA',
            'android.permission.RECORD_AUDIO',
            'android.permission.READ_SMS',
            'android.permission.SEND_SMS',
            'android.permission.RECEIVE_SMS',
            'android.permission.CALL_PHONE',
            'android.permission.READ_PHONE_STATE',
            'android.permission.READ_PHONE_NUMBERS',
            'android.permission.BODY_SENSORS',
            'android.permission.ACTIVITY_RECOGNITION'
        ]
        
        permissions = apk_info.get('permissions', [])
        
        for permission in permissions:
            if permission in dangerous_permissions:
                security['permissions']['dangerous'].append(permission)
            elif permission.startswith('android.permission.'):
                security['permissions']['normal'].append(permission)
            elif 'signature' in permission.lower():
                security['permissions']['signature'].append(permission)
            else:
                security['permissions']['unknown'].append(permission)
        
        # Check for certificate info
        if 'signing' in apk_info:
            security['certificate_info'] = apk_info['signing']
        
        # Check for potentially risky components
        components = []
        components.extend(apk_info.get('activities', []))
        components.extend(apk_info.get('services', []))
        components.extend(apk_info.get('receivers', []))
        components.extend(apk_info.get('providers', []))
        
        risky_patterns = [
            'debug', 'test', 'backup', 'admin', 'root', 'shell',
            'install', 'certificate', 'password', 'key'
        ]
        
        for component in components:
            for pattern in risky_patterns:
                if pattern.lower() in component.lower():
                    security['risky_components'].append({
                        'name': component,
                        'risk_factor': pattern
                    })
                    break
        
        # Check for potential vulnerabilities
        vulnerabilities = []
        
        # Check for debuggable flag
        if ANDROGUARD_AVAILABLE:
            try:
                a = apk.APK(apk_path)
                if a.is_debuggable():
                    vulnerabilities.append({
                        'name': 'Debuggable Application',
                        'severity': 'High',
                        'description': 'The application is debuggable, which allows attackers to connect a debugger and potentially extract sensitive information.'
                    })
                
                # Check if backup is allowed
                if a.is_backup():
                    vulnerabilities.append({
                        'name': 'Backup Enabled',
                        'severity': 'Medium',
                        'description': 'The application allows backup, which could potentially lead to data leakage.'
                    })
            except Exception:
                pass
        
        # Check target SDK for known security concerns
        target_sdk = apk_info.get('target_sdk')
        if target_sdk and int(target_sdk) < 23:
            vulnerabilities.append({
                'name': 'Outdated Target SDK',
                'severity': 'Medium',
                'description': f'The application targets Android API level {target_sdk}, which is below the recommended minimum of 23 (Android 6.0). This may expose the app to security vulnerabilities that were fixed in newer versions.'
            })
        
        security['potential_vulnerabilities'] = vulnerabilities
        
        # Calculate overall security score (0-100)
        score = 100
        
        # Deduct for dangerous permissions
        score -= len(security['permissions']['dangerous']) * 5
        
        # Deduct for risky components
        score -= len(security['risky_components']) * 3
        
        # Deduct for vulnerabilities
        for vuln in vulnerabilities:
            if vuln['severity'] == 'High':
                score -= 15
            elif vuln['severity'] == 'Medium':
                score -= 10
            else:
                score -= 5
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        security['security_score'] = score
        
        # Determine rating based on score
        if score >= 90:
            security['rating'] = 'Excellent'
        elif score >= 75:
            security['rating'] = 'Good'
        elif score >= 60:
            security['rating'] = 'Average'
        elif score >= 40:
            security['rating'] = 'Below Average'
        else:
            security['rating'] = 'Poor'
        
        return security
    
    def install_apk(self, apk_path):
        """Install an APK using ADB"""
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file does not exist'}
        
        if not self.adb_available:
            return {'success': False, 'error': 'ADB not available for installation'}
        
        try:
            # Check for connected devices
            process = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if process.returncode != 0:
                return {'success': False, 'error': 'Error checking ADB devices: ' + process.stderr}
            
            # Parse device list
            device_output = process.stdout.strip().split('\n')
            if len(device_output) <= 1:
                return {'success': False, 'error': 'No devices connected to ADB'}
            
            # Install the APK
            process = subprocess.run(['adb', 'install', '-r', apk_path], capture_output=True, text=True)
            
            if process.returncode != 0:
                return {'success': False, 'error': 'Error installing APK: ' + process.stderr}
            
            if 'Success' in process.stdout:
                return {'success': True, 'message': 'APK installed successfully'}
            else:
                return {'success': False, 'error': 'Unknown error during installation'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_apk_contents(self, apk_path, output_dir=None):
        """Extract the contents of an APK file for detailed inspection"""
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file does not exist'}
        
        # Create output directory if not provided
        if not output_dir:
            apk_name = os.path.splitext(os.path.basename(apk_path))[0]
            output_dir = os.path.join(os.path.dirname(apk_path), f"{apk_name}_extracted")
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Extract the APK using zipfile
            with zipfile.ZipFile(apk_path, 'r') as z:
                z.extractall(output_dir)
            
            # Get content statistics
            stats = {
                'total_files': 0,
                'total_size': 0,
                'file_types': {}
            }
            
            for root, dirs, files in os.walk(output_dir):
                stats['total_files'] += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    stats['total_size'] += file_size
                    
                    # Categorize by extension
                    ext = os.path.splitext(file)[1].lower()
                    if not ext:
                        ext = 'no_extension'
                    
                    if ext not in stats['file_types']:
                        stats['file_types'][ext] = {'count': 0, 'size': 0}
                    
                    stats['file_types'][ext]['count'] += 1
                    stats['file_types'][ext]['size'] += file_size
            
            return {
                'success': True,
                'output_dir': output_dir,
                'stats': stats,
                'message': f'APK extracted to {output_dir}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def compare_apks(self, apk_path1, apk_path2):
        """Compare two APK files and highlight differences"""
        if not os.path.exists(apk_path1):
            return {'success': False, 'error': f'First APK file does not exist: {apk_path1}'}
            
        if not os.path.exists(apk_path2):
            return {'success': False, 'error': f'Second APK file does not exist: {apk_path2}'}
        
        try:
            # Analyze both APKs
            analysis1 = self.analyze_apk(apk_path1)
            analysis2 = self.analyze_apk(apk_path2)
            
            if not analysis1.get('success'):
                return {'success': False, 'error': f'Failed to analyze first APK: {analysis1.get("error")}'}
                
            if not analysis2.get('success'):
                return {'success': False, 'error': f'Failed to analyze second APK: {analysis2.get("error")}'}
            
            # Extract basic information for both APKs
            apk1_info = {
                'path': apk_path1,
                'package_name': analysis1.get('package_name'),
                'version_name': analysis1.get('version_name'),
                'version_code': analysis1.get('version_code'),
                'file_size': analysis1.get('apk_size')
            }
            
            apk2_info = {
                'path': apk_path2,
                'package_name': analysis2.get('package_name'),
                'version_name': analysis2.get('version_name'),
                'version_code': analysis2.get('version_code'),
                'file_size': analysis2.get('apk_size')
            }
            
            # Compare package names
            same_package = analysis1.get('package_name') == analysis2.get('package_name')
            
            # Compare versions if it's the same package
            newer_version = None
            if same_package:
                try:
                    version_code1 = int(analysis1.get('version_code', 0))
                    version_code2 = int(analysis2.get('version_code', 0))
                    
                    if version_code1 > version_code2:
                        newer_version = 'APK 1'
                    elif version_code2 > version_code1:
                        newer_version = 'APK 2'
                except ValueError:
                    pass
            
            # Compare components (activities, services, etc.)
            components = ['activities', 'services', 'receivers', 'providers']
            component_diff = {}
            
            for component in components:
                comp1 = set(analysis1.get(component, []))
                comp2 = set(analysis2.get(component, []))
                
                component_diff[component] = {
                    'only_in_apk1': list(comp1 - comp2),
                    'only_in_apk2': list(comp2 - comp1),
                    'common': list(comp1 & comp2)
                }
            
            # Compare permissions
            perm1 = set(analysis1.get('permissions', []))
            perm2 = set(analysis2.get('permissions', []))
            
            permission_diff = {
                'only_in_apk1': list(perm1 - perm2),
                'only_in_apk2': list(perm2 - perm1),
                'common': list(perm1 & perm2)
            }
            
            # Compare security scores
            security_score1 = analysis1.get('security_analysis', {}).get('security_score', 0)
            security_score2 = analysis2.get('security_analysis', {}).get('security_score', 0)
            
            security_comparison = {
                'apk1_score': security_score1,
                'apk2_score': security_score2,
                'difference': security_score1 - security_score2
            }
            
            # Compile comparison results
            result = {
                'success': True,
                'apk1': apk1_info,
                'apk2': apk2_info,
                'same_package': same_package,
                'newer_version': newer_version,
                'components': component_diff,
                'permissions': permission_diff,
                'security': security_comparison
            }
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_from_google_play(self, package_name, output_dir=None):
        """
        Download an APK from Google Play Store
        Note: This is a placeholder implementation as direct download from Google Play
        requires authentication and isn't officially supported
        """
        return {
            'success': False,
            'error': 'Direct download from Google Play Store is not supported in this version. Please use an APK from a trusted source.'
        }


# Create an instance for use in the application
apk_analyzer = APKAnalyzer()