import json
import os
from typing import List, Dict
from src.models.setting import RegistrySetting, SettingCategory, SettingType

class SettingLoader:
    """Loads settings from resources/settings.json"""

    CATEGORY_MAP = {
        "System Appearance": SettingCategory.APPEARANCE,
        "File Explorer Settings": SettingCategory.FILE_EXPLORER,
        "Taskbar & Start Menu": SettingCategory.TASKBAR,
        "Power Settings": SettingCategory.POWER,
        "Privacy Options": SettingCategory.PRIVACY,
        "Keyboard & Mouse": SettingCategory.KEYBOARD,
        "Network Settings": SettingCategory.NETWORK,
        "Advanced Settings": SettingCategory.SYSTEM
    }

    def __init__(self, resource_path: str = None):
        if resource_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.resource_path = os.path.join(base_dir, "resources", "settings.json")
        else:
            self.resource_path = resource_path
        
        self.settings_by_category: Dict[SettingCategory, List[RegistrySetting]] = {}
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.resource_path):
            print(f"Settings resource not found: {self.resource_path}")
            return

        with open(self.resource_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for cat_data in data:
            cat_name = cat_data.get("name")
            enum_cat = self.CATEGORY_MAP.get(cat_name, SettingCategory.SYSTEM)
            
            if enum_cat not in self.settings_by_category:
                self.settings_by_category[enum_cat] = []

            for s_data in cat_data.get("settings", []):
                # Create a RegistrySetting object
                # Some fields might be missing depending on how clean the MD was
                # We'll use defaults and sanitize
                
                try:
                    setting = RegistrySetting(
                        id=s_data.get("name", "unknown").lower().replace(" ", "_"),
                        name=s_data.get("name", "Unknown Setting"),
                        description=s_data.get("description", ""),
                        category=enum_cat,
                        setting_type=SettingType.REGISTRY,
                        value=None, # To be read from registry later
                        default_value=None,
                        hive=s_data.get("hive", "HKEY_CURRENT_USER"),
                        key_path=s_data.get("key", "").replace("\\\\", "\\"),
                        value_name=s_data.get("value", ""),
                        value_type=s_data.get("type", "REG_DWORD")
                    )
                    self.settings_by_category[enum_cat].append(setting)
                except Exception as e:
                    print(f"Error loading setting {s_data.get('name')}: {e}")

    def get_settings_for_category(self, category: SettingCategory) -> List[RegistrySetting]:
        return self.settings_by_category.get(category, [])

    def get_categories(self) -> List[SettingCategory]:
        return list(self.settings_by_category.keys())
