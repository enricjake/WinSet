from dataclasses import (
    dataclass,
    field,
)  # dataclass decorator and field() for defaults in dataclass attributes
from datetime import (
    datetime,
)  # Used to track when profiles are created and last modified
from typing import (
    Dict,
    List,
    Optional,
)  # Type hints for dictionary, list, and optional values
import json  # Used to serialize profile data to JSON for checksum generation and export
import hashlib  # Used to compute SHA-256 checksums for profile integrity verification

from .setting import (
    Setting,
    RegistrySetting,
    SettingCategory,
    SettingType,
)  # Setting models: base class, registry-specific implementation, category/type enums


@dataclass
class Profile:
    """Complete settings profile — the top-level container in WinSet that groups
    related settings (registry tweaks, service configurations, etc.) into a
    named, versioned, exportable unit of Windows configuration."""

    # Human-readable name for the profile (e.g. "Gaming Optimization", "Dev Workstation")
    name: str

    # Timestamp of when this profile was first created; defaults to the current time on instantiation
    created: datetime = field(default_factory=datetime.now)

    # Timestamp of the last modification (updated whenever a setting is added or removed)
    modified: datetime = field(default_factory=datetime.now)

    # Mapping of setting IDs (strings) to Setting objects that compose this profile
    settings: Dict[str, Setting] = field(default_factory=dict)

    # Schema version of the profile, used for forward/backward compatibility during import/export
    version: str = "1.0"

    # The Windows build/version this profile targets (e.g. "22H2", "23H2"); empty if generic
    windows_version: str = ""

    # Optional longer description explaining what this profile does or is intended for
    description: str = ""

    # Arbitrary string labels for filtering/searching profiles (e.g. ["gaming", "performance"])
    tags: List[str] = field(default_factory=list)

    @property
    def setting_count(self) -> int:
        """Return the total number of settings contained in this profile."""
        return len(
            self.settings
        )  # Dictionary size equals the number of Setting entries

    @property
    def checksum(self) -> str:
        """Generate a SHA-256 checksum for the profile's exported data so that
        users can verify file integrity after sharing or storing profiles on disk."""
        # Serialize the profile to a JSON string (without the checksum field itself to avoid recursion)
        data = json.dumps(self.export(include_checksum=False), sort_keys=True)
        # Produce a hex-encoded SHA-256 hash of the canonical JSON representation
        return hashlib.sha256(data.encode()).hexdigest()

    def add_setting(self, setting: Setting):
        """Add a new setting or replace an existing one (keyed by setting.id)
        and bump the modified timestamp so external tooling knows the profile changed."""
        self.settings[setting.id] = setting  # Store/overwrite by unique setting ID
        self.modified = (
            datetime.now()
        )  # Update modified timestamp to reflect the change

    def remove_setting(self, setting_id: str):
        """Delete the setting identified by setting_id from this profile, if it exists,
        and update the modified timestamp accordingly."""
        if setting_id in self.settings:  # Guard against KeyError on absent settings
            del self.settings[setting_id]  # Remove the setting entry
            self.modified = datetime.now()  # Record the modification time

    def apply_all(self, safe_mode: bool = True) -> Dict[str, bool]:
        """Iterate through every setting in the profile and apply it to the live
        Windows system.  Returns a dict mapping each setting ID to True/False
        indicating whether it was applied successfully.

        Parameters
        ----------
        safe_mode : bool
            When True (default), settings that require a system restart are
            skipped to avoid unexpected reboots during a batch apply.  Set to
            False to apply everything including restart-required settings."""

        results: Dict[str, bool] = {}  # Accumulates success/failure for each setting
        for (
            setting_id,
            setting,
        ) in self.settings.items():  # Iterate over every setting in the profile
            if safe_mode and setting.requires_restart:
                # In safe mode we intentionally skip settings that would force a reboot
                results[setting_id] = False
                continue  # Move on to the next setting

            try:
                # Delegate to the Setting subclass (e.g. RegistrySetting) to write the value
                results[setting_id] = setting.apply()
            except Exception as e:
                # If application fails, record failure; the error is logged upstream
                results[setting_id] = False
                # Log error (actual logging handled elsewhere in the WinSet pipeline)

        return results  # Return the full success/failure map to the caller

    def export(self, include_checksum: bool = True) -> dict:
        """Serialize the profile into a plain dictionary suitable for JSON export.

        Parameters
        ----------
        include_checksum : bool
            When True (default), a SHA-256 checksum key is appended to the
            output.  Set to False internally to avoid recursive checksum
            computation when generating the checksum itself."""

        # Build the core profile data dict with scalar fields
        data: dict = {
            "name": self.name,
            "created": self.created.isoformat(),  # ISO 8601 string for portability
            "modified": self.modified.isoformat(),
            "version": self.version,
            "windows_version": self.windows_version,
            "description": self.description,
            "tags": self.tags,
            "settings": {
                sid: s.export()
                for sid, s in self.settings.items()  # Export each Setting to a dict
            },
        }
        if include_checksum:
            # Append integrity checksum so imported files can be validated
            data["checksum"] = self.checksum
        return data  # Return the serializable dictionary

    @classmethod
    def import_from_dict(cls, data: dict) -> "Profile":
        """Reconstruct a Profile instance from a dictionary (typically loaded
        from a JSON file).  Handles missing keys gracefully with defaults and
        skips individual settings that contain invalid or incomplete data.

        Parameters
        ----------
        data : dict
            The deserialized profile dictionary previously produced by export()."""

        # Instantiate the Profile with fields from the dict, falling back to sensible defaults
        profile = cls(
            name=data.get("name", "Unnamed Profile"),  # Default name when none provided
            created=datetime.fromisoformat(data["created"])
            if "created" in data
            else datetime.now(),
            modified=datetime.fromisoformat(data["modified"])
            if "modified" in data
            else datetime.now(),
            version=data.get("version", "1.0"),  # Default to version 1.0 if absent
            windows_version=data.get(
                "windows_version", ""
            ),  # Empty string when not specified
            description=data.get("description", ""),
            tags=data.get("tags", []),  # Default to an empty tag list
        )

        # Reconstruct each saved Setting from its dictionary representation
        for sid, sdata in data.get(
            "settings", {}
        ).items():  # sid = setting ID string; sdata = setting dict
            setting_type_str = sdata.get(
                "type"
            )  # The SettingType enum value stored as a string

            if setting_type_str == SettingType.REGISTRY.value:
                # Handle registry-based settings (the primary WinSet setting type)
                try:
                    # Convert the category string back into the SettingCategory enum
                    category_enum = SettingCategory(sdata.get("category", "system"))

                    # Build a RegistrySetting with all required fields from the serialized data
                    setting = RegistrySetting(
                        id=sdata["id"],  # Unique identifier for the setting
                        name=sdata["name"],  # Display name
                        description=sdata.get(
                            "description", ""
                        ),  # Optional human-readable description
                        category=category_enum,  # Grouping category (system, UI, network, etc.)
                        setting_type=SettingType.REGISTRY,  # Confirms this is a registry setting
                        value=sdata.get("value"),  # The desired value to apply
                        default_value=None,  # Original default not preserved in export data
                        requires_admin=sdata.get(
                            "requires_admin", False
                        ),  # Admin elevation needed?
                        requires_restart=sdata.get(
                            "requires_restart", False
                        ),  # Reboot needed?
                        hive=sdata["hive"],  # Registry hive (e.g. HKLM, HKCU)
                        key_path=sdata["key_path"],  # Full registry key path
                        value_name=sdata["value_name"],  # Name of the registry value
                        value_type=sdata[
                            "value_type"
                        ],  # Data type (REG_DWORD, REG_SZ, etc.)
                    )
                    profile.add_setting(
                        setting
                    )  # Insert the reconstructed setting into the profile
                except (KeyError, ValueError) as e:
                    # Skip settings with missing required fields or invalid enum values
                    print(
                        f"Skipping setting '{sid}' due to missing/invalid data in profile: {e}"
                    )

        return profile  # Return the fully reconstructed Profile instance
