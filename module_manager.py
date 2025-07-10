"""
Module Manager for Drive-Manager Pro.
Handles enabling/disabling of application modules and their dependencies.
"""

import os
import json
import datetime
from database import db_manager
from models import UserPreference

class ModuleManager:
    """Manages application module states and dependencies"""
    
    def __init__(self):
        """Initialize the module manager"""
        self.modules = {
            'file_management': {
                'name': 'File Management',
                'description': 'Core file browsing and organization features',
                'enabled': True,
                'core': True,  # Cannot be disabled
                'dependencies': [],
                'ui_components': ['file-browser', 'file-operations', 'file-metadata']
            },
            'ai_analysis': {
                'name': 'AI File Analysis',
                'description': 'AI-powered file analysis and tagging',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management'],
                'ui_components': ['ai-analysis-panel', 'smart-tags', 'file-recommendations']
            },
            'duplicate_detection': {
                'name': 'Duplicate Detection',
                'description': 'Find and manage duplicate files',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management'],
                'ui_components': ['duplicate-scanner', 'duplicate-results', 'cleanup-tools']
            },
            'cloud_storage': {
                'name': 'Cloud Storage',
                'description': 'Integration with cloud storage providers',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management'],
                'ui_components': ['cloud-sync-panel', 'cloud-status', 'sync-settings']
            },
            'media_handling': {
                'name': 'Media Processing',
                'description': 'Advanced media file processing and thumbnails',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management'],
                'ui_components': ['media-viewer', 'thumbnail-grid', 'media-metadata']
            },
            'ai_media_generation': {
                'name': 'AI Media Generation',
                'description': 'Generate images and videos using AI',
                'enabled': True,
                'core': False,
                'dependencies': ['media_handling'],
                'ui_components': ['ai-generator', 'generation-history', 'model-selector']
            },
            'apk_management': {
                'name': 'APK Management',
                'description': 'Create, analyze, and manage Android APK files',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management'],
                'ui_components': ['apk-creator', 'apk-analyzer', 'apk-library']
            },
            'app_generator': {
                'name': 'App Generator',
                'description': 'Generate applications from templates and prompts',
                'enabled': True,
                'core': False,
                'dependencies': ['apk_management'],
                'ui_components': ['app-templates', 'code-generator', 'app-preview']
            },
            'ui_extractor': {
                'name': 'UI Feature Extractor',
                'description': 'Extract UI elements and features from existing apps',
                'enabled': True,
                'core': False,
                'dependencies': ['apk_management'],
                'ui_components': ['ui-extractor', 'feature-library', 'extraction-tools']
            },
            'mind_mapping': {
                'name': 'Mind Mapping',
                'description': 'Visual relationship mapping between files',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management', 'ai_analysis'],
                'ui_components': ['mind-map-viewer', 'relationship-graph', 'visual-connections']
            },
            'user_accounts': {
                'name': 'User Accounts',
                'description': 'User authentication and profile management',
                'enabled': True,
                'core': False,
                'dependencies': [],
                'ui_components': ['login-form', 'profile-settings', 'user-dashboard']
            },
            'advanced_search': {
                'name': 'Advanced Search',
                'description': 'Powerful search with filters and AI assistance',
                'enabled': True,
                'core': False,
                'dependencies': ['file_management', 'ai_analysis'],
                'ui_components': ['search-bar', 'filter-panel', 'search-results']
            }
        }
        
        # Load user preferences
        self._load_module_states()
    
    def _load_module_states(self):
        """Load module states from user preferences"""
        try:
            session = db_manager.get_session()
            if not session:
                return
            
            # Get module preferences for the current user (default user for demo)
            preferences = session.query(UserPreference).filter_by(
                user_id=1,  # Default user
                key='modules_enabled'
            ).first()
            
            if preferences and preferences.value:
                try:
                    saved_modules = json.loads(preferences.value)
                    for module_id, enabled in saved_modules.items():
                        if module_id in self.modules:
                            # Don't disable core modules
                            if not self.modules[module_id]['core']:
                                self.modules[module_id]['enabled'] = enabled
                except json.JSONDecodeError:
                    pass
            
            session.close()
            
        except Exception as e:
            print(f"Error loading module states: {str(e)}")
    
    def _save_module_states(self):
        """Save current module states to user preferences"""
        try:
            session = db_manager.get_session()
            if not session:
                return
            
            # Prepare module states for saving
            module_states = {}
            for module_id, module_info in self.modules.items():
                module_states[module_id] = module_info['enabled']
            
            # Save or update preference
            preference = session.query(UserPreference).filter_by(
                user_id=1,  # Default user
                key='modules_enabled'
            ).first()
            
            if preference:
                preference.value = json.dumps(module_states)
                preference.updated_at = datetime.datetime.utcnow()
            else:
                preference = UserPreference(
                    user_id=1,
                    key='modules_enabled',
                    value=json.dumps(module_states)
                )
                session.add(preference)
            
            session.commit()
            session.close()
            
        except Exception as e:
            print(f"Error saving module states: {str(e)}")
    
    def get_module_status(self, module_id=None):
        """Get status of a specific module or all modules"""
        if module_id:
            if module_id in self.modules:
                module = self.modules[module_id].copy()
                module['id'] = module_id
                module['available'] = self._check_module_availability(module_id)
                return {
                    'success': True,
                    'module': module
                }
            else:
                return {
                    'success': False,
                    'error': f"Module '{module_id}' not found"
                }
        else:
            # Return all modules with their status
            modules_status = []
            for mod_id, mod_info in self.modules.items():
                module = mod_info.copy()
                module['id'] = mod_id
                module['available'] = self._check_module_availability(mod_id)
                modules_status.append(module)
            
            return {
                'success': True,
                'modules': modules_status
            }
    
    def toggle_module(self, module_id, enabled=None):
        """Toggle or set the enabled state of a module"""
        if module_id not in self.modules:
            return {
                'success': False,
                'error': f"Module '{module_id}' not found"
            }
        
        module = self.modules[module_id]
        
        # Check if module is core (cannot be disabled)
        if module['core'] and enabled is False:
            return {
                'success': False,
                'error': f"Cannot disable core module '{module['name']}'"
            }
        
        # Determine new state
        if enabled is None:
            new_state = not module['enabled']
        else:
            new_state = enabled
        
        # Check dependencies if enabling
        if new_state:
            dependency_check = self._check_dependencies(module_id)
            if not dependency_check['satisfied']:
                return {
                    'success': False,
                    'error': f"Dependencies not satisfied: {', '.join(dependency_check['missing'])}"
                }
        
        # Check dependent modules if disabling
        if not new_state:
            dependent_modules = self._get_dependent_modules(module_id)
            if dependent_modules:
                # Disable dependent modules as well
                for dep_module in dependent_modules:
                    self.modules[dep_module]['enabled'] = False
        
        # Set the new state
        old_state = module['enabled']
        self.modules[module_id]['enabled'] = new_state
        
        # Save changes
        self._save_module_states()
        
        # Get affected UI components
        affected_components = self._get_affected_ui_components(module_id)
        
        return {
            'success': True,
            'module_id': module_id,
            'module_name': module['name'],
            'old_state': old_state,
            'new_state': new_state,
            'affected_components': affected_components,
            'dependent_modules_disabled': dependent_modules if not new_state else [],
            'message': f"Module '{module['name']}' {'enabled' if new_state else 'disabled'}"
        }
    
    def _check_dependencies(self, module_id):
        """Check if module dependencies are satisfied"""
        module = self.modules[module_id]
        missing_deps = []
        
        for dep_id in module['dependencies']:
            if dep_id not in self.modules or not self.modules[dep_id]['enabled']:
                missing_deps.append(self.modules.get(dep_id, {}).get('name', dep_id))
        
        return {
            'satisfied': len(missing_deps) == 0,
            'missing': missing_deps
        }
    
    def _get_dependent_modules(self, module_id):
        """Get modules that depend on the given module"""
        dependent = []
        
        for mod_id, mod_info in self.modules.items():
            if module_id in mod_info['dependencies'] and mod_info['enabled']:
                dependent.append(mod_id)
        
        return dependent
    
    def _check_module_availability(self, module_id):
        """Check if module is available (dependencies satisfied)"""
        dependency_check = self._check_dependencies(module_id)
        return dependency_check['satisfied']
    
    def _get_affected_ui_components(self, module_id):
        """Get UI components affected by module state change"""
        if module_id in self.modules:
            return self.modules[module_id]['ui_components']
        return []
    
    def get_ui_component_states(self):
        """Get the enabled/disabled state for all UI components"""
        component_states = {}
        
        for module_id, module_info in self.modules.items():
            is_enabled = module_info['enabled'] and self._check_module_availability(module_id)
            
            for component in module_info['ui_components']:
                component_states[component] = {
                    'enabled': is_enabled,
                    'module': module_id,
                    'module_name': module_info['name']
                }
        
        return {
            'success': True,
            'components': component_states
        }
    
    def get_module_configuration(self):
        """Get complete module configuration for UI"""
        config = {
            'modules': [],
            'ui_components': {},
            'dependencies': {}
        }
        
        # Add module information
        for mod_id, mod_info in self.modules.items():
            module_config = {
                'id': mod_id,
                'name': mod_info['name'],
                'description': mod_info['description'],
                'enabled': mod_info['enabled'],
                'core': mod_info['core'],
                'available': self._check_module_availability(mod_id),
                'dependencies': mod_info['dependencies'],
                'ui_components': mod_info['ui_components']
            }
            config['modules'].append(module_config)
        
        # Add UI component states
        component_states = self.get_ui_component_states()
        config['ui_components'] = component_states['components']
        
        # Add dependency map
        for mod_id, mod_info in self.modules.items():
            config['dependencies'][mod_id] = {
                'requires': mod_info['dependencies'],
                'required_by': self._get_dependent_modules(mod_id)
            }
        
        return {
            'success': True,
            'config': config
        }
    
    def reset_to_defaults(self):
        """Reset all modules to their default enabled state"""
        changes = []
        
        for module_id, module_info in self.modules.items():
            if not module_info['core']:  # Don't change core modules
                old_state = module_info['enabled']
                module_info['enabled'] = True  # Default to enabled
                
                if old_state != module_info['enabled']:
                    changes.append({
                        'module_id': module_id,
                        'module_name': module_info['name'],
                        'old_state': old_state,
                        'new_state': module_info['enabled']
                    })
        
        # Save changes
        self._save_module_states()
        
        return {
            'success': True,
            'changes': changes,
            'message': f"Reset {len(changes)} modules to default state"
        }
    
    def get_build_configuration(self):
        """Get configuration for building the application with only enabled modules"""
        enabled_modules = []
        disabled_modules = []
        build_exclusions = []
        
        for module_id, module_info in self.modules.items():
            if module_info['enabled']:
                enabled_modules.append({
                    'id': module_id,
                    'name': module_info['name'],
                    'components': module_info['ui_components']
                })
            else:
                disabled_modules.append({
                    'id': module_id,
                    'name': module_info['name'],
                    'components': module_info['ui_components']
                })
                
                # Add to build exclusions
                build_exclusions.extend(module_info['ui_components'])
        
        return {
            'success': True,
            'build_config': {
                'enabled_modules': enabled_modules,
                'disabled_modules': disabled_modules,
                'ui_exclusions': build_exclusions,
                'total_modules': len(self.modules),
                'enabled_count': len(enabled_modules),
                'disabled_count': len(disabled_modules)
            }
        }


# Create an instance for use in the application
module_manager = ModuleManager()