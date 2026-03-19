from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json
import hashlib

from .setting import Setting, RegistrySetting, SettingCategory, SettingType

@dataclass
class Profile:
    """Complete settings profile"""
    name: str
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Setting] = field(default_factory=dict)
    version: str = "1.0"
    windows_version: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    @property
    def setting_count(self) -> int:
        return len(self.settings)
    
    @property
    def checksum(self) -> str:
        """Generate checksum for integrity verification"""
        data = json.dumps(self.export(include_checksum=False), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def add_setting(self, setting: Setting):
        """Add or update a setting"""
        self.settings[setting.id] = setting
        self.modified = datetime.now()
    
    def remove_setting(self, setting_id: str):
        """Remove a setting"""
        if setting_id in self.settings:
            del self.settings[setting_id]
            self.modified = datetime.now()
    
    def apply_all(self, safe_mode: bool = True) -> Dict[str, bool]:
        """Apply all settings to the system"""
        results = {}
        for setting_id, setting in self.settings.items():
            if safe_mode and setting.requires_restart:
                # Skip restart-required settings in safe mode
                results[setting_id] = False
                continue
            
            try:
                results[setting_id] = setting.apply()
            except Exception as e:
                results[setting_id] = False
                # Log error
        return results
    
    def export(self, include_checksum: bool = True) -> dict:
        """Export profile to dictionary"""
        data = {
            "name": self.name,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "version": self.version,
            "windows_version": self.windows_version,
            "description": self.description,
            "tags": self.tags,
            "settings": {
                sid: s.export() for sid, s in self.settings.items()
            }
        }
        if include_checksum:
            data["checksum"] = self.checksum
        return data
    
    @classmethod
    def import_from_dict(cls, data: dict) -> 'Profile':
        """Create profile from dictionary"""
        profile = cls(
            name=data.get("name", "Unnamed Profile"),
            created=datetime.fromisoformat(data["created"]) if "created" in data else datetime.now(),
            modified=datetime.fromisoformat(data["modified"]) if "modified" in data else datetime.now(),
            version=data.get("version", "1.0"),
            windows_version=data.get("windows_version", ""),
            description=data.get("description", ""),
            tags=data.get("tags", [])
        )
        
        for sid, sdata in data.get("settings", {}).items():
            setting_type_str = sdata.get("type")

            if setting_type_str == SettingType.REGISTRY.value:
                try:
                    category_enum = SettingCategory(sdata.get("category", "system"))

                    setting = RegistrySetting(
                        id=sdata["id"],
                        name=sdata["name"],
                        description=sdata.get("description", ""),
                        category=category_enum,
                        setting_type=SettingType.REGISTRY,
                        value=sdata.get("value"),
                        default_value=None,  # Not available in export
                        requires_admin=sdata.get("requires_admin", False),
                        requires_restart=sdata.get("requires_restart", False),
                        hive=sdata["hive"],
                        key_path=sdata["key_path"],
                        value_name=sdata["value_name"],
                        value_type=sdata["value_type"],
                    )
                    profile.add_setting(setting)
                except (KeyError, ValueError) as e:
                    print(f"Skipping setting '{sid}' due to missing/invalid data in profile: {e}")
            
        return profile