import json
import os
import hashlib
import base64
from typing import Dict, Any, Tuple

from src.models.profile import Profile
from src.models.setting import RegistrySetting, PowerSetting, ServiceSetting, SettingCategory, SettingType
from src.core.registry_handler import RegistryHandler

class ProfileImporter:
    """Imports and applies settings from a JSON profile file."""

    def __init__(self):
        self.registry = RegistryHandler()
        from src.core.setting_loader import SettingLoader
        self.loader = SettingLoader()
        self._master_settings = {}
        # Flatten settings from categories for easy lookup
        for cat in self.loader.get_categories():
            for s in self.loader.get_settings_for_category(cat):
                self._master_settings[s.name.lower()] = s
                self._master_settings[s.id.lower()] = s

    def _verify_checksum(self, data: dict) -> bool:
        """Verifies the integrity of the profile data using the checksum."""
        stored_checksum = data.get("checksum")
        if not stored_checksum:
            return False

        # Build a sanitized copy to avoid mutating caller-owned dictionaries.
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        data_str = json.dumps(data_without_checksum, sort_keys=True)
        calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()
        return stored_checksum == calculated_checksum

    def _deserialize_registry_value(self, setting_value: Any, value_type: str) -> Any:
        """Restore encoded profile values back to native registry-compatible types."""
        if (
            value_type == "REG_BINARY"
            and isinstance(setting_value, dict)
            and setting_value.get("__encoding__") == "base64"
            and isinstance(setting_value.get("data"), str)
        ):
            try:
                return base64.b64decode(setting_value["data"])
            except (ValueError, TypeError):
                return setting_value
        return setting_value

    def load_profile(self, file_path: str) -> Tuple[bool, str, Profile | None]:
        """Loads and validates a profile from disk."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}", None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "checksum" in data and not self._verify_checksum(data):
                return False, "Profile integrity check failed. The file may have been tampered with or corrupted.", None

            # Reconstruct the profile object
            profile = Profile.import_from_dict(data)
            
            # Reconstruct settings objects
            settings_data = data.get("settings", {})
            for sid, sdata in settings_data.items():
                setting = None
                
                # Check if this is a standard rich setting or a simplified preset setting
                is_rich = isinstance(sdata, dict) and "type" in sdata
                
                if is_rich:
                    stype = sdata.get("type")
                    if stype == SettingType.REGISTRY.value:
                        setting = RegistrySetting(
                            id=sdata["id"],
                            name=sdata["name"],
                            description=sdata["description"],
                            category=SettingCategory(sdata["category"]),
                            setting_type=SettingType(stype),
                            value=self._deserialize_registry_value(sdata["value"], sdata["value_type"]),
                            default_value=sdata.get("default_value"),
                            requires_admin=sdata.get("requires_admin", False),
                            requires_restart=sdata.get("requires_restart", False),
                            hive=sdata["hive"],
                            key_path=sdata["key_path"],
                            value_name=sdata["value_name"],
                            value_type=sdata["value_type"],
                            is_expanded=sdata.get("is_expanded", False)
                        )
                    # ... other types (Power, Service) could be added here
                else:
                    # Hydrate from master settings if only ID/Name and Value provided
                    lookup_key = sid.lower()
                    master = self._master_settings.get(lookup_key) or self._master_settings.get(lookup_key.replace("_", " "))
                    
                    if master:
                        value = sdata.get("value") if isinstance(sdata, dict) else sdata
                        if isinstance(master, RegistrySetting):
                            value = self._deserialize_registry_value(value, master.value_type)
                        if isinstance(master, RegistrySetting):
                            setting = RegistrySetting(
                                id=master.id,
                                name=master.name,
                                description=master.description,
                                category=master.category,
                                setting_type=master.setting_type,
                                value=value,
                                default_value=master.default_value,
                                hive=master.hive,
                                key_path=master.key_path,
                                value_name=master.value_name,
                                value_type=master.value_type
                            )
                
                if setting:
                    profile.add_setting(setting)

            return True, "Profile loaded successfully.", profile

        except Exception as e:
            return False, f"Error loading profile: {str(e)}", None

    def apply_profile(self, profile: Profile, safe_mode: bool = True) -> Dict[str, bool]:
        """Applies a loaded profile to the system."""
        results = {}
        for setting_id, setting in profile.settings.items():
            if safe_mode and setting.requires_restart:
                results[setting_id] = False
                continue

            if isinstance(setting, RegistrySetting):
                success = self.registry.write_value(
                    hive=setting.hive,
                    key_path=setting.key_path,
                    value_name=setting.value_name,
                    value_type=setting.value_type,
                    value=setting.value
                )
                results[setting_id] = success
                setting.is_applied = success
            else:
                # Fallback for future non-registry settings
                try:
                    results[setting_id] = setting.apply()
                except Exception:
                    results[setting_id] = False
                    
        return results
