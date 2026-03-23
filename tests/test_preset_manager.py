"""
Tests for Preset Manager.
"""

import pytest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.presets.preset_manager import PresetManager


class TestPresetManager:
    """Test PresetManager class."""
    
    def setup_method(self):
        """Create a temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PresetManager(presets_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_preset(self):
        """Test creating a new preset."""
        settings = {
            "test_setting_1": 1,
            "test_setting_2": "value"
        }
        
        result = self.manager.create_preset(
            preset_id="test_preset",
            name="Test Preset",
            description="A test preset",
            settings=settings,
            icon="🧪"
        )
        
        assert result is True
        
        # Verify preset was created
        info = self.manager.get_preset_info("test_preset")
        assert info is not None
        assert info["name"] == "Test Preset"
        assert info["description"] == "A test preset"
        assert info["setting_count"] == 2
    
    def test_list_presets(self):
        """Test listing presets."""
        # Create a couple of presets
        self.manager.create_preset("preset1", "Preset One", "First preset", {"a": 1})
        self.manager.create_preset("preset2", "Preset Two", "Second preset", {"b": 2})
        
        presets = self.manager.list_presets()
        assert len(presets) == 2
    
    def test_apply_preset(self):
        """Test applying a preset."""
        settings = {
            "test1": 1,
            "test2": "value"
        }
        
        self.manager.create_preset("test", "Test", "Test preset", settings)
        
        # Mock apply function
        applied = []
        def mock_apply(setting_id, value):
            applied.append((setting_id, value))
            return True
        
        success, results = self.manager.apply_preset("test", mock_apply)
        
        assert success is True
        assert len(applied) == 2
        assert results.get("test1") is True
        assert results.get("test2") is True
    
    def test_apply_preset_with_failure(self):
        """Test applying a preset with some failures."""
        settings = {
            "test1": 1,
            "test2": "value",
            "test3": 3
        }
        
        self.manager.create_preset("test", "Test", "Test preset", settings)
        
        # Mock apply function that fails for test2
        def mock_apply(setting_id, value):
            return setting_id != "test2"
        
        success, results = self.manager.apply_preset("test", mock_apply)
        
        assert success is False
        assert results.get("test1") is True
        assert results.get("test2") is False
        assert results.get("test3") is True
    
    def test_delete_preset(self):
        """Test deleting a preset."""
        self.manager.create_preset("to_delete", "To Delete", "Will be deleted", {"x": 1})
        assert self.manager.get_preset_info("to_delete") is not None
        
        result = self.manager.delete_preset("to_delete")
        assert result is True
        assert self.manager.get_preset_info("to_delete") is None
    
    def test_invalid_preset_id_rejected(self):
        """Test that invalid preset IDs are rejected."""
        invalid_ids = [
            "invalid/id",
            "invalid space",
            "invalid@char",
            "",  # Empty
            "a" * 300  # Too long
        ]
        
        for preset_id in invalid_ids:
            result = self.manager.create_preset(
                preset_id,
                "Name",
                "Description",
                {"a": 1}
            )
            assert result is False