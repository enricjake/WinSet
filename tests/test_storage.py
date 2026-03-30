import pytest  # Pytest framework for fixtures and test markers
import os  # Provides filesystem path and existence checks
import json  # JSON serialization/deserialization for profile files
import base64  # Base64 encoding/decoding for binary registry values
from unittest.mock import (
    patch,
    MagicMock,
)  # patch: decorator to mock module attributes; MagicMock: flexible mock object
from src.storage.exporter import (
    ProfileExporter,
)  # Handles exporting settings profiles to JSON files
from src.storage.importer import (
    ProfileImporter,
)  # Handles importing and applying settings profiles from JSON
from src.models.setting import (
    RegistrySetting,
    SettingCategory,
    SettingType,
)  # Data models and enums for settings


@pytest.fixture
def sample_setting():
    # Returns a RegistrySetting instance used as test data across multiple tests.
    return RegistrySetting(
        id="test_setting",  # Unique identifier for the setting
        name="Test",  # Display name
        description="Test Setting",  # Description text
        category=SettingCategory.SYSTEM,  # Categorizes under System
        setting_type=SettingType.REGISTRY,  # Indicates registry-backed setting
        value=1,  # Current value
        default_value=0,  # Factory default value
        hive="HKEY_CURRENT_USER",  # Registry hive root
        key_path="SOFTWARE\\WinSet\\Test",  # Registry subkey path
        value_name="TestValue",  # Registry value entry name
        value_type="REG_DWORD",  # Registry type (32-bit unsigned integer)
    )


@patch("src.core.registry_handler.RegistryHandler.read_value")
def test_profile_export(mock_read_value, tmp_path, sample_setting):
    """Test exporting a profile to JSON without executing live registry reads"""
    # mock_read_value: MagicMock replacing RegistryHandler.read_value during this test
    # tmp_path: pytest built-in fixture providing a temporary Path directory
    # sample_setting: RegistrySetting from the fixture above
    exporter = ProfileExporter()  # Instantiate the profile exporter
    mock_read_value.return_value = 42  # Pretend the registry returns 42 for any read

    file_path = tmp_path / "test_export.json"  # Path object for the export destination
    success = exporter.export_profile(
        [sample_setting], str(file_path), "Test Profile", "Desc"
    )
    # [sample_setting]: list of settings to export
    # str(file_path): output file path as string
    # "Test Profile": profile display name
    # "Desc": profile description

    assert success is True  # Export should succeed
    assert os.path.exists(file_path)  # Exported file should exist on disk

    # Read back the exported file to verify its contents.
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)  # Deserialize JSON back into a Python dict

    assert data["name"] == "Test Profile"  # Profile name should match
    assert "checksum" in data  # Exported file should include an integrity checksum
    # Verify the mocked value (42) was correctly saved in the settings section.
    assert data["settings"]["test_setting"]["value"] == 42


def test_profile_import_checksum_tampered(tmp_path):
    """Test that the importer rejects manually modified JSON files"""
    # tmp_path: pytest built-in temporary directory fixture
    importer = ProfileImporter()  # Instantiate the profile importer

    # Create a dummy fake JSON with an intentionally wrong checksum to simulate tampering.
    data = {
        "name": "Tampered",  # Profile name
        "created": "2023-11-01T10:00:00",  # Creation timestamp
        "modified": "2023-11-01T10:00:00",  # Modification timestamp
        "version": "1.0",  # Schema version
        "windows_version": "Win11",  # Windows version at export time
        "description": "desc",  # Profile description
        "tags": [],  # Tags list (empty)
        "settings": {},  # Settings dict (empty)
        "checksum": "fake_hash",  # Invalid checksum — does not match computed hash
    }

    # Write the tampered profile to disk.
    file_path = tmp_path / "tampered.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)  # Serialize to JSON file

    # Attempt to load the tampered profile.
    success, msg, profile = importer.load_profile(str(file_path))
    # success: bool — whether loading succeeded
    # msg: str — status/error message
    # profile: dict or None — the loaded profile data
    assert success is False  # Loading should fail due to checksum mismatch
    assert (
        "checksum" in msg.lower() or "integrity" in msg.lower()
    )  # Error should mention checksum/integrity


@patch("src.core.registry_handler.RegistryHandler.write_value")
def test_profile_import_and_apply(mock_write_value, tmp_path, sample_setting):
    """Test importing and applying a profile safely"""
    # First export a real valid profile using a mocked read_value.
    exporter = ProfileExporter()  # Instantiate exporter
    with patch("src.core.registry_handler.RegistryHandler.read_value") as mock_read:
        mock_read.return_value = 1  # Mock registry read to return 1
        file_path = tmp_path / "valid.json"  # Export destination path
        exporter.export_profile([sample_setting], str(file_path))  # Export the setting

    # Now import the freshly exported profile.
    importer = ProfileImporter()  # Instantiate importer
    success, msg, profile = importer.load_profile(str(file_path))
    # success: bool — load success flag
    # msg: str — status message
    # profile: loaded profile dict

    assert success is True  # Import should succeed
    assert profile is not None  # Profile data should be returned

    # Apply the imported profile using a mocked write_value.
    mock_write_value.return_value = True  # Simulate successful registry write
    results = importer.apply_profile(profile)
    # results: dict mapping setting_id -> bool (success/failure per setting)

    assert results["test_setting"] is True  # The test setting should apply successfully
    mock_write_value.assert_called_once()  # write_value should have been called exactly once


def test_verify_checksum_does_not_mutate_input():
    """Checksum validation should not mutate caller-owned dictionaries."""
    importer = ProfileImporter()  # Instantiate importer
    # Create a profile data dict to test non-mutation.
    data = {
        "name": "Test Profile",  # Profile name
        "created": "2023-11-01T10:00:00",  # Creation timestamp
        "modified": "2023-11-01T10:00:00",  # Modification timestamp
        "version": "1.0",  # Schema version
        "windows_version": "Win11",  # Windows version
        "description": "desc",  # Description
        "tags": [],  # Tags list
        "settings": {},  # Settings dict
        "checksum": "fake_hash",  # Checksum value (invalid, but irrelevant for this test)
    }
    original = dict(data)  # Shallow copy to compare against after the call

    importer._verify_checksum(data)  # Call internal checksum verification
    assert data == original  # The input dict should not be modified by verification


@patch("src.core.registry_handler.RegistryHandler.read_value")
def test_profile_export_binary_value_is_base64_encoded(
    mock_read_value, tmp_path, sample_setting
):
    """REG_BINARY export should use a lossless base64 representation."""
    # mock_read_value: mocked registry read function
    # tmp_path: temporary directory fixture
    # sample_setting: RegistrySetting fixture
    exporter = ProfileExporter()  # Instantiate exporter
    sample_setting.value_type = "REG_BINARY"  # Override the setting type to binary
    raw = b"\x00\x01\xffbinary\x10"  # Raw binary data to simulate a REG_BINARY value
    mock_read_value.return_value = raw  # Mock the registry returning binary data

    file_path = tmp_path / "binary_export.json"  # Export destination
    success = exporter.export_profile(
        [sample_setting], str(file_path), "Binary Profile"
    )

    assert success is True  # Export should succeed
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)  # Read back the exported JSON

    exported_value = data["settings"]["test_setting"][
        "value"
    ]  # Extract the binary value field
    assert (
        exported_value["__encoding__"] == "base64"
    )  # Should be marked as base64 encoded
    assert (
        base64.b64decode(exported_value["data"]) == raw
    )  # Decoded data should match original bytes


def test_profile_import_decodes_base64_binary():
    """Importer should decode base64 encoded REG_BINARY values."""
    importer = ProfileImporter()  # Instantiate importer
    raw = b"\xaa\xbb\xcc\xdd"  # Original raw binary data
    encoded = {
        "__encoding__": "base64",  # Encoding marker
        "data": base64.b64encode(raw).decode(
            "ascii"
        ),  # Base64-encoded string of the raw bytes
    }

    decoded = importer._deserialize_registry_value(encoded, "REG_BINARY")
    # encoded: dict with __encoding__ and data fields
    # "REG_BINARY": registry type hint for the deserializer
    assert decoded == raw  # Decoded bytes should match the original raw data
