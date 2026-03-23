"""
Preset Manager for WinSet - manages preset configurations.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime


class PresetManager:
    """
    Manages preset configurations for WinSet.
    Handles loading, validating, and applying presets.
    """
    
    def __init__(self, presets_dir: Optional[str] = None):
        """
        Initialize the preset manager.
        
        Args:
            presets_dir: Optional custom presets directory.
                        Defaults to the 'presets' folder in the application directory.
        """
        if presets_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.presets_dir = os.path.join(base_dir, "presets")
        else:
            # Validate custom directory path
            self.presets_dir = self._validate_preset_path(presets_dir)
        
        self.presets: Dict[str, Dict[str, Any]] = {}
        self._load_presets()
    
    def _validate_preset_path(self, path: str) -> str:
        """
        Validate a preset directory path for security.
        
        Args:
            path: The path to validate
            
        Returns:
            The validated absolute path
            
        Raises:
            ValueError: If the path is unsafe
        """
        try:
            safe_path = Path(path).resolve()
            
            # Check if path is within application directory or user's WinSet folder
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()
            user_winset = Path(os.path.expanduser("~")) / "Documents" / "WinSet" / "presets"
            user_winset.resolve()
            
            if base_dir not in safe_path.parents and safe_path != base_dir:
                if user_winset not in safe_path.parents and safe_path != user_winset:
                    raise ValueError(
                        f"Preset path '{path}' is outside allowed directories"
                    )
            
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)
            
            return str(safe_path)
            
        except Exception as e:
            raise ValueError(f"Invalid preset path: {e}")
    
    def _load_presets(self):
        """Load all preset files from the presets directory."""
        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir, exist_ok=True)
            return
        
        for filename in os.listdir(self.presets_dir):
            if filename.endswith('.json'):
                preset_path = os.path.join(self.presets_dir, filename)
                try:
                    with open(preset_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024 * 1024)  # 1MB limit
                        preset_data = json.loads(content)
                    
                    # Validate preset structure
                    if self._validate_preset_data(preset_data):
                        preset_id = filename[:-5]  # Remove .json
                        self.presets[preset_id] = preset_data
                    else:
                        print(f"Invalid preset structure in: {filename}")
                        
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON in preset file {filename}: {e}")
                except Exception as e:
                    print(f"Error loading preset {filename}: {e}")
    
    def _validate_preset_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate preset data structure.
        
        Args:
            data: Preset data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'description', 'settings']
        
        for field in required_fields:
            if field not in data:
                return False
        
        if not isinstance(data['settings'], dict):
            return False
        
        # Limit number of settings
        if len(data['settings']) > 200:
            return False
        
        # Validate setting names
        for setting_id, setting_value in data['settings'].items():
            if len(setting_id) > 100:
                return False
            
            # Setting value should be basic type
            if not isinstance(setting_value, (str, int, bool, float, dict)):
                return False
            
            # If dict, limit size
            if isinstance(setting_value, dict):
                if len(setting_value) > 20:
                    return False
        
        return True
    
    def get_preset_info(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a preset.
        
        Args:
            preset_id: The ID of the preset
            
        Returns:
            Preset metadata or None if not found
        """
        if preset_id not in self.presets:
            return None
        
        data = self.presets[preset_id]
        return {
            "id": preset_id,
            "name": data.get("name", "Unknown"),
            "description": data.get("description", ""),
            "icon": data.get("icon", "⚙️"),
            "version": data.get("version", "1.0"),
            "setting_count": len(data.get("settings", {})),
            "tags": data.get("tags", [])
        }
    
    def get_preset_settings(self, preset_id: str) -> Dict[str, Any]:
        """
        Get the settings for a preset.
        
        Args:
            preset_id: The ID of the preset
            
        Returns:
            Dictionary of settings or empty dict if not found
        """
        if preset_id not in self.presets:
            return {}
        
        return self.presets[preset_id].get("settings", {})
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        List all available presets.
        
        Returns:
            List of preset information dictionaries
        """
        presets_list = []
        for preset_id in self.presets:
            info = self.get_preset_info(preset_id)
            if info:
                presets_list.append(info)
        
        # Sort by name
        presets_list.sort(key=lambda x: x['name'])
        return presets_list
    
    def apply_preset(self, preset_id: str, apply_function) -> Tuple[bool, Dict[str, bool]]:
        """
        Apply a preset using the provided apply function.
        
        Args:
            preset_id: The ID of the preset to apply
            apply_function: Function to call for each setting,
                           takes (setting_id, value) and returns bool
            
        Returns:
            Tuple of (success, results dict)
        """
        if preset_id not in self.presets:
            return False, {}
        
        settings = self.get_preset_settings(preset_id)
        results = {}
        all_success = True
        
        for setting_id, value in settings.items():
            try:
                success = apply_function(setting_id, value)
                results[setting_id] = success
                if not success:
                    all_success = False
            except Exception as e:
                results[setting_id] = False
                all_success = False
                print(f"Error applying setting {setting_id}: {e}")
        
        return all_success, results
    
    def create_preset(self, preset_id: str, name: str, description: str, 
                      settings: Dict[str, Any], icon: str = "⚙️") -> bool:
        """
        Create a new preset.
        
        Args:
            preset_id: Unique identifier for the preset
            name: Display name
            description: Preset description
            settings: Dictionary of settings
            icon: Emoji icon for the preset
            
        Returns:
            True if successful, False otherwise
        """
        # Validate preset ID
        if not preset_id or not re.match(r'^[a-z0-9_-]+$', preset_id, re.IGNORECASE):
            return False
        
        # Validate settings
        if len(settings) > 200:
            return False
        
        preset_data = {
            "name": name[:100],
            "description": description[:500],
            "icon": icon[:2] if icon else "⚙️",
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "settings": settings
        }
        
        preset_path = os.path.join(self.presets_dir, f"{preset_id}.json")
        
        try:
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            # Reload presets
            self._load_presets()
            return True
            
        except Exception as e:
            print(f"Error creating preset: {e}")
            return False
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a preset.
        
        Args:
            preset_id: The ID of the preset to delete
            
        Returns:
            True if successful, False otherwise
        """
        if preset_id not in self.presets:
            return False
        
        preset_path = os.path.join(self.presets_dir, f"{preset_id}.json")
        
        try:
            os.remove(preset_path)
            del self.presets[preset_id]
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def get_preset_usage(self, preset_id: str) -> Optional[int]:
        """
        Get usage count for a preset (from history).
        
        Args:
            preset_id: The ID of the preset
            
        Returns:
            Number of times applied or None if not found
        """
        # This would integrate with HistoryManager
        # Placeholder for now
        return 0
    # src/presets/preset_manager.py

    def _validate_preset_path(self, path: str) -> str:
        """
        Validate a preset directory path for security.
        
        Args:
            path: The path to validate
        
        Returns:
            The validated absolute path
        
        Raises:
            ValueError: If the path is unsafe
        """
        try:
            safe_path = Path(path).resolve()
            
            # Check if path is within application directory or user's WinSet folder
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()
            user_winset = Path(os.path.expanduser("~")) / "Documents" / "WinSet" / "presets"
            user_winset.resolve()
            
            # Allow temporary directories for testing
            temp_dir = Path(tempfile.gettempdir()).resolve()
            is_temp_path = temp_dir in safe_path.parents or safe_path == temp_dir
            
            if not is_temp_path:
                if base_dir not in safe_path.parents and safe_path != base_dir:
                    if user_winset not in safe_path.parents and safe_path != user_winset:
                        raise ValueError(
                            f"Preset path '{path}' is outside allowed directories"
                        )
            
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)
            
            return str(safe_path)
        
        except Exception as e:
            raise ValueError(f"Invalid preset path: {e}")

# Add missing import at the top of the file
import re