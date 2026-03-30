"""
Tests for WinSet model classes.
"""

import sys  # Used to modify the Python module search path
import os  # Provides path operations for locating source directories

# Add src to path so model modules can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models.setting import (
    RegistrySetting,
    SettingCategory,
    SettingType,
)  # Core model classes/enums


class TestModels:
    """Tests for model classes"""

    def test_registry_setting_creation(self):
        """Test creating a registry setting"""
        # Instantiate a RegistrySetting with all required fields to verify
        # the constructor stores values correctly and defaults are applied.
        setting = RegistrySetting(
            id="reg1",  # Unique identifier for the setting
            name="Registry Test",  # Human-readable display name
            description="Test registry setting",  # Description text
            category=SettingCategory.SYSTEM,  # Enum value categorizing the setting
            setting_type=SettingType.REGISTRY,  # Enum value indicating registry-backed type
            value=1,  # Current value of the setting
            default_value=0,  # Factory default value
            hive="HKEY_CURRENT_USER",  # Windows registry hive root
            key_path="Software\\Microsoft\\Windows\\CurrentVersion",  # Full subkey path
            value_name="TestValue",  # Name of the registry value entry
            value_type="REG_DWORD",  # Registry data type string
        )

        # Verify all constructor arguments are stored as instance attributes.
        assert setting.hive == "HKEY_CURRENT_USER"  # Hive should match what was passed
        assert (
            setting.key_path == "Software\\Microsoft\\Windows\\CurrentVersion"
        )  # Key path preserved
        assert setting.value_name == "TestValue"  # Value name preserved
        assert setting.value_type == "REG_DWORD"  # Value type preserved
        assert (
            setting.is_expanded is False
        )  # Default value — UI expansion state starts collapsed

    def test_registry_setting_validate_dword(self):
        """Test DWORD validation"""
        # Create a DWORD-typed setting to test value validation rules.
        setting = RegistrySetting(
            id="reg2",  # Unique identifier
            name="DWORD Test",  # Display name
            description="",  # Empty description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=0,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="Val",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )
        # validate() checks whether a given value is acceptable for this setting's type.
        assert setting.validate(0) is True  # Zero is a valid DWORD
        assert (
            setting.validate(4294967295) is True
        )  # Max DWORD value (2^32 - 1) is valid
        assert setting.validate(-1) is False  # Negative numbers are invalid for DWORD
        assert setting.validate("not_an_int") is False  # Strings are invalid for DWORD

    def test_registry_setting_validate_sz(self):
        """Test REG_SZ validation"""
        # Create a REG_SZ (string) typed setting to test string validation rules.
        setting = RegistrySetting(
            id="reg3",  # Unique identifier
            name="SZ Test",  # Display name
            description="",  # Empty description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value="",  # Current value (empty string)
            default_value="",  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="Val",  # Value name
            value_type="REG_SZ",  # String type
        )
        assert setting.validate("hello") is True  # Strings are valid for REG_SZ
        assert setting.validate(123) is False  # Integers are invalid for REG_SZ

    def test_registry_setting_export(self):
        """Test that export() returns the expected keys"""
        # Create a setting with HKEY_LOCAL_MACHINE hive to verify export serialization.
        setting = RegistrySetting(
            id="reg4",  # Unique identifier
            name="Export Test",  # Display name
            description="desc",  # Short description
            category=SettingCategory.APPEARANCE,  # Appearance category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_LOCAL_MACHINE",  # Hive (different from other tests to verify serialization)
            key_path="Software\\Test",  # Key path
            value_name="ExportVal",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )
        exported = setting.export()  # export() returns a dict of the setting's data
        assert (
            exported["hive"] == "HKEY_LOCAL_MACHINE"
        )  # Hive should be in exported dict
        assert (
            exported["value_name"] == "ExportVal"
        )  # Value name should be in exported dict
        assert (
            exported["value_type"] == "REG_DWORD"
        )  # Value type should be in exported dict
