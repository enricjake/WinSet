import pytest
import os
import json
import base64
from unittest.mock import patch, MagicMock
from src.storage.exporter import ProfileExporter
from src.storage.importer import ProfileImporter
from src.models.setting import RegistrySetting, SettingCategory, SettingType

@pytest.fixture
def sample_setting():
    return RegistrySetting(
        id="test_setting",
        name="Test",
        description="Test Setting",
        category=SettingCategory.SYSTEM,
        setting_type=SettingType.REGISTRY,
        value=1,
        default_value=0,
        hive="HKEY_CURRENT_USER",
        key_path="SOFTWARE\\WinSet\\Test",
        value_name="TestValue",
        value_type="REG_DWORD"
    )

@patch('src.core.registry_handler.RegistryHandler.read_value')
def test_profile_export(mock_read_value, tmp_path, sample_setting):
    """Test exporting a profile to JSON without executing live registry reads"""
    exporter = ProfileExporter()
    mock_read_value.return_value = 42 # Pretend the registry returns 42
    
    file_path = tmp_path / "test_export.json"
    success = exporter.export_profile([sample_setting], str(file_path), "Test Profile", "Desc")
    
    assert success is True
    assert os.path.exists(file_path)
    
    # Read back to verify
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["name"] == "Test Profile"
    assert "checksum" in data
    # Verify the mocked value was saved
    assert data["settings"]["test_setting"]["value"] == 42


def test_profile_import_checksum_tampered(tmp_path):
    """Test that the importer rejects manually modified JSON files"""
    importer = ProfileImporter()
    
    # Create a dummy fake JSON
    data = {
        "name": "Tampered",
        "created": "2023-11-01T10:00:00",
        "modified": "2023-11-01T10:00:00",
        "version": "1.0",
        "windows_version": "Win11",
        "description": "desc",
        "tags": [],
        "settings": {},
        "checksum": "fake_hash"
    }
    
    file_path = tmp_path / "tampered.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    success, msg, profile = importer.load_profile(str(file_path))
    assert success is False
    assert "checksum" in msg.lower() or "integrity" in msg.lower()

@patch('src.core.registry_handler.RegistryHandler.write_value')
def test_profile_import_and_apply(mock_write_value, tmp_path, sample_setting):
    """Test importing and applying a profile safely"""
    # First export a real valid profile
    exporter = ProfileExporter()
    with patch('src.core.registry_handler.RegistryHandler.read_value') as mock_read:
        mock_read.return_value = 1
        file_path = tmp_path / "valid.json"
        exporter.export_profile([sample_setting], str(file_path))
        
    # Now import it
    importer = ProfileImporter()
    success, msg, profile = importer.load_profile(str(file_path))
    
    assert success is True
    assert profile is not None
    
    # Apply it
    mock_write_value.return_value = True
    results = importer.apply_profile(profile)
    
    assert results["test_setting"] is True
    mock_write_value.assert_called_once()


def test_verify_checksum_does_not_mutate_input():
    """Checksum validation should not mutate caller-owned dictionaries."""
    importer = ProfileImporter()
    data = {
        "name": "Test Profile",
        "created": "2023-11-01T10:00:00",
        "modified": "2023-11-01T10:00:00",
        "version": "1.0",
        "windows_version": "Win11",
        "description": "desc",
        "tags": [],
        "settings": {},
        "checksum": "fake_hash",
    }
    original = dict(data)

    importer._verify_checksum(data)
    assert data == original


@patch('src.core.registry_handler.RegistryHandler.read_value')
def test_profile_export_binary_value_is_base64_encoded(mock_read_value, tmp_path, sample_setting):
    """REG_BINARY export should use a lossless base64 representation."""
    exporter = ProfileExporter()
    sample_setting.value_type = "REG_BINARY"
    raw = b"\x00\x01\xffbinary\x10"
    mock_read_value.return_value = raw

    file_path = tmp_path / "binary_export.json"
    success = exporter.export_profile([sample_setting], str(file_path), "Binary Profile")

    assert success is True
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    exported_value = data["settings"]["test_setting"]["value"]
    assert exported_value["__encoding__"] == "base64"
    assert base64.b64decode(exported_value["data"]) == raw


def test_profile_import_decodes_base64_binary():
    """Importer should decode base64 encoded REG_BINARY values."""
    importer = ProfileImporter()
    raw = b"\xaa\xbb\xcc\xdd"
    encoded = {
        "__encoding__": "base64",
        "data": base64.b64encode(raw).decode("ascii"),
    }

    decoded = importer._deserialize_registry_value(encoded, "REG_BINARY")
    assert decoded == raw
