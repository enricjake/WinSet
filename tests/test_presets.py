import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.presets.preset_manager import PresetManager

@pytest.fixture
def mock_presets_dir(tmp_path):
    """Create a temporary directory with a couple mock JSON presets"""
    dev_json = """{
        "name": "Developer Mode",
        "created": "2023-11-01T10:00:00",
        "modified": "2023-11-01T10:00:00",
        "version": "1.0",
        "windows_version": "Win",
        "description": "desc",
        "checksum": "fake",
        "settings": {}
    }"""
    
    # Needs a real checksum for the manager to load it properly
    # A trick is to use the ProfileExporter to generate a valid empty json
    from src.storage.exporter import ProfileExporter
    from src.models.profile import Profile
    import json
    
    p = Profile(name="Mock Preset")
    data = p.export()
    
    with open(tmp_path / "mock1.json", "w") as f:
        json.dump(data, f)
        
    p2 = Profile(name="Mock Preset 2")
    data2 = p2.export()
    
    with open(tmp_path / "mock2.json", "w") as f:
        json.dump(data2, f)
        
    return str(tmp_path)


def test_preset_discovery(mock_presets_dir):
    """Test that the manager correctly finds .json files in the dir"""
    manager = PresetManager(presets_dir=mock_presets_dir)
    presets = manager.get_preset_list()
    
    assert len(presets) == 2
    assert "mock1" in presets
    assert "mock2" in presets

@patch('src.storage.importer.ProfileImporter.apply_profile')
def test_preset_application(mock_apply, mock_presets_dir):
    """Test applying a preset translates to an importer apply call"""
    manager = PresetManager(presets_dir=mock_presets_dir)
    mock_apply.return_value = {"mock_setting": True} # Assume one setting applied successfully
    
    success, msg, results = manager.apply_preset("mock1")
    
    assert success is True
    assert results["mock_setting"] is True
    mock_apply.assert_called_once()
    
def test_preset_application_not_found():
    """Test trying to apply a preset that doesn't exist"""
    manager = PresetManager()
    
    success, msg, results = manager.apply_preset("non_existent_preset_999")
    
    assert success is False
    assert "not found" in msg.lower()
