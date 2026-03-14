from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum
from datetime import datetime

class SettingType(Enum):
    REGISTRY = "registry"
    FILE = "file"
    SYSTEM = "system"
    POWER = "power"

class SettingCategory(Enum):
    APPEARANCE = "appearance"
    FILE_EXPLORER = "file_explorer"
    TASKBAR = "taskbar"
    POWER = "power"
    PRIVACY = "privacy"
    SYSTEM = "system"

@dataclass
class Setting:
    """Base class for all settings"""
    id: str
    name: str
    description: str
    category: SettingCategory
    setting_type: SettingType
    value: Any
    default_value: Any
    is_applied: bool = False
    requires_admin: bool = False
    requires_restart: bool = False
    last_modified: Optional[datetime] = None
    
    def validate(self, value: Any) -> bool:
        """Validate if a value is acceptable"""
        raise NotImplementedError
    
    def apply(self) -> bool:
        """Apply this setting to the system"""
        raise NotImplementedError
    
    def export(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "category": self.category.value,
            "type": self.setting_type.value
        }

@dataclass
class RegistrySetting(Setting):
    """Setting stored in Windows Registry"""
    hive: str  # HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE
    key_path: str
    value_name: str
    value_type: str  # REG_SZ, REG_DWORD, etc.
    
    def validate(self, value: Any) -> bool:
        # Validate based on registry type
        if self.value_type == "REG_DWORD":
            return isinstance(value, int) and 0 <= value <= 4294967295
        elif self.value_type == "REG_SZ":
            return isinstance(value, str)
        return True
    
    def apply(self) -> bool:
        # Apply to registry
        import winreg
        try:
            key = winreg.OpenKey(
                getattr(winreg, self.hive),
                self.key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, self.value_name, 0, 
                            getattr(winreg, self.value_type), self.value)
            winreg.CloseKey(key)
            self.is_applied = True
            return True
        except Exception as e:
            print(f"Failed to apply {self.name}: {e}")
            return False