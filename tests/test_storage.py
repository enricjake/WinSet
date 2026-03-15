import pytest
import os
import json
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
