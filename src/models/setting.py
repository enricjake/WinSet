"""
Setting models for WinSet
"""

from dataclasses import dataclass, field, KW_ONLY
from typing import Any, Optional, Dict
from enum import Enum
from datetime import datetime

import winreg

class SettingType(Enum):
    """Type of setting"""
    REGISTRY = "registry"
    FILE = "file"
    SYSTEM = "system"
    POWER = "power"


class SettingCategory(Enum):
    """Category of setting"""
    APPEARANCE = "appearance"
    FILE_EXPLORER = "file_explorer"
    TASKBAR = "taskbar"
    POWER = "power"
    PRIVACY = "privacy"
    SYSTEM = "system"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    NETWORK = "network"


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
        raise NotImplementedError(f"Validate not implemented for {self.__class__.__name__}")

    def apply(self) -> bool:
        """Apply this setting to the system"""
        raise NotImplementedError(f"Apply not implemented for {self.__class__.__name__}")

    def export(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "category": self.category.value,
            "type": self.setting_type.value,
            "requires_admin": self.requires_admin,
            "requires_restart": self.requires_restart
        }


@dataclass
class RegistrySetting(Setting):
    """Setting stored in Windows Registry"""
    # KW_ONLY sentinel: all fields below this are keyword-only.
    # This is required because the base Setting class has optional fields
    # (e.g. last_modified) that would otherwise conflict with these
    # required (no-default) fields in the subclass.
    _: KW_ONLY
    hive: str  # HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, etc.
    key_path: str
    value_name: str
    value_type: str  # REG_SZ, REG_DWORD, etc.
    # Optional fields with defaults
    is_expanded: bool = False  # For REG_EXPAND_SZ
    options: Optional[Dict[str, Any]] = None  # For multi-value settings (dropdown options)
    is_range: bool = False  # For slider ranges

    def __post_init__(self):
        """Validate after initialization"""
        # Set the setting_type automatically if not already set
        if self.setting_type == SettingType.REGISTRY:
            pass  # Already correct
        else:
            # Force to registry type
            object.__setattr__(self, 'setting_type', SettingType.REGISTRY)

    def validate(self, value: Any) -> bool:
        """Validate based on registry type"""
        if self.value_type == "REG_DWORD":
            return isinstance(value, int) and 0 <= value <= 4294967295
        elif self.value_type == "REG_SZ" or self.value_type == "REG_EXPAND_SZ":
            return isinstance(value, str)
        elif self.value_type == "REG_BINARY":
            return isinstance(value, (bytes, bytearray))
        elif self.value_type == "REG_MULTI_SZ":
            return isinstance(value, list) and all(isinstance(s, str) for s in value)
        elif self.value_type == "REG_QWORD":
            return isinstance(value, int) and 0 <= value <= 18446744073709551615
        return True

    def apply(self) -> bool:
        """Apply to registry by delegating to the robust RegistryHandler."""
        # Local import to avoid circular dependency issues at module level
        from src.core.registry_handler import RegistryHandler

        handler = RegistryHandler()
        success = handler.write_value(
            hive=self.hive,
            key_path=self.key_path,
            value_name=self.value_name,
            value_type=self.value_type,
            value=self.value,
        )
        return success

    def export(self) -> dict:
        """Export registry setting to dict"""
        base_dict = super().export()
        base_dict.update({
            "hive": self.hive,
            "key_path": self.key_path,
            "value_name": self.value_name,
            "value_type": self.value_type,
            "is_expanded": self.is_expanded
        })
        return base_dict
@dataclass
class PowerSetting(Setting):
    """Setting for Windows Power Plans"""
    _: KW_ONLY
    plan_guid: str

    def __post_init__(self):
        if self.setting_type != SettingType.POWER:
            object.__setattr__(self, 'setting_type', SettingType.POWER)

    def apply(self) -> bool:
        from src.core.powershell_handler import PowerShellHandler
        ps = PowerShellHandler()
        success, _ = ps.set_power_plan(self.plan_guid)
        self.is_applied = success
        return success


@dataclass
class ServiceSetting(Setting):
    """Setting for Windows Services"""
    _: KW_ONLY
    service_name: str
    startup_type: str = "Disabled" # Disabled, Manual, Automatic

    def __post_init__(self):
        if self.setting_type != SettingType.SYSTEM:
            object.__setattr__(self, 'setting_type', SettingType.SYSTEM)

    def apply(self) -> bool:
        from src.core.powershell_handler import PowerShellHandler
        ps = PowerShellHandler()
        if self.startup_type == "Disabled":
            success, _ = ps.disable_service(self.service_name)
        else:
            # Add more service methods to PowerShellHandler if needed
            command = f"Set-Service -Name '{self.service_name}' -StartupType {self.startup_type}"
            success, _ = ps.run_command(command)
        
        self.is_applied = success
        return success
