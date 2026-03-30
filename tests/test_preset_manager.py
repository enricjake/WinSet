"""
Tests for Preset Manager.
"""

import pytest  # Pytest framework for test structure
import sys  # Used to modify the Python module search path
import os  # Provides filesystem path operations
import json  # JSON serialization (used indirectly by PresetManager)
import tempfile  # Creates temporary directories for isolated preset tests

# Add project root to path so 'src' package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.presets.preset_manager import (
    PresetManager,
)  # Manages creation, loading, and application of presets


class TestPresetManager:
    """Test PresetManager class."""

    def setup_method(self):
        """Create a temporary directory for tests."""
        # Create an isolated temp directory for each test to avoid cross-test contamination.
        self.temp_dir = tempfile.mkdtemp()  # str path to the temporary directory
        # Instantiate PresetManager pointing at the temp directory.
        # self.manager: PresetManager under test, scoped to the temp directory
        self.manager = PresetManager(presets_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil  # Imported here to avoid top-level dependency

        shutil.rmtree(
            self.temp_dir, ignore_errors=True
        )  # Recursively delete the temp dir

    def test_create_preset(self):
        """Test creating a new preset."""
        # Define a dictionary of settings to include in the preset.
        settings = {
            "test_setting_1": 1,  # Integer setting value
            "test_setting_2": "value",  # String setting value
        }

        # Create a new preset with an ID, name, description, settings, and icon.
        result = self.manager.create_preset(
            preset_id="test_preset",  # Unique filesystem-safe identifier
            name="Test Preset",  # Display name
            description="A test preset",  # Description text
            settings=settings,  # Dict of setting_id -> value
            icon="🧪",  # Emoji icon for display
        )

        assert result is True  # Creation should succeed

        # Verify the preset was created correctly by reading back its metadata.
        info = self.manager.get_preset_info(
            "test_preset"
        )  # Retrieve preset metadata dict
        assert info is not None  # Preset should exist
        assert info["name"] == "Test Preset"  # Name should match
        assert info["description"] == "A test preset"  # Description should match
        assert info["setting_count"] == 2  # Should report 2 settings

    def test_list_presets(self):
        """Test listing presets."""
        # Create a couple of presets to populate the directory.
        self.manager.create_preset("preset1", "Preset One", "First preset", {"a": 1})
        self.manager.create_preset("preset2", "Preset Two", "Second preset", {"b": 2})

        presets = self.manager.list_presets()  # Returns list of preset metadata dicts
        assert len(presets) == 2  # Both presets should be listed

    def test_apply_preset(self):
        """Test applying a preset."""
        # Define settings for the preset to apply.
        settings = {
            "test1": 1,  # First test setting
            "test2": "value",  # Second test setting
        }

        self.manager.create_preset(
            "test", "Test", "Test preset", settings
        )  # Create the preset

        # Mock apply function — records which settings were applied and always succeeds.
        applied = []  # List to track (setting_id, value) tuples that were applied

        def mock_apply(setting_id, value):
            # setting_id: str — the ID of the setting being applied
            # value: any — the value to apply
            applied.append((setting_id, value))  # Record the application
            return True  # Simulate successful application

        # Apply the preset using the mock function as the callback.
        success, results = self.manager.apply_preset("test", mock_apply)

        assert success is True  # Overall application should succeed
        assert len(applied) == 2  # Both settings should have been applied
        assert results.get("test1") is True  # test1 should report success
        assert results.get("test2") is True  # test2 should report success

    def test_apply_preset_with_failure(self):
        """Test applying a preset with some failures."""
        # Define three settings to test partial failure handling.
        settings = {
            "test1": 1,  # Will succeed
            "test2": "value",  # Will fail
            "test3": 3,  # Will succeed
        }

        self.manager.create_preset(
            "test", "Test", "Test preset", settings
        )  # Create the preset

        # Mock apply function that fails only for "test2".
        def mock_apply(setting_id, value):
            # setting_id: str — the setting being applied
            # value: any — the value to apply
            return (
                setting_id != "test2"
            )  # Return False for "test2", True for all others

        # Apply the preset — should report partial failure.
        success, results = self.manager.apply_preset("test", mock_apply)

        assert success is False  # Overall success should be False due to test2 failure
        assert results.get("test1") is True  # test1 should succeed
        assert results.get("test2") is False  # test2 should fail
        assert results.get("test3") is True  # test3 should succeed

    def test_delete_preset(self):
        """Test deleting a preset."""
        # Create a preset specifically to test deletion.
        self.manager.create_preset(
            "to_delete", "To Delete", "Will be deleted", {"x": 1}
        )
        assert (
            self.manager.get_preset_info("to_delete") is not None
        )  # Verify it exists first

        result = self.manager.delete_preset("to_delete")  # Delete the preset
        assert result is True  # Deletion should succeed
        assert (
            self.manager.get_preset_info("to_delete") is None
        )  # Preset should no longer exist

    def test_invalid_preset_id_rejected(self):
        """Test that invalid preset IDs are rejected."""
        # List of preset IDs that should be rejected by validation.
        invalid_ids = [
            "invalid/id",  # Contains path separator (security risk)
            "invalid space",  # Contains whitespace
            "invalid@char",  # Contains special character
            "",  # Empty string
            "a" * 300,  # Exceeds maximum length
        ]

        # Each invalid ID should cause create_preset to return False.
        for preset_id in invalid_ids:
            result = self.manager.create_preset(
                preset_id,  # The invalid preset ID to test
                "Name",  # Display name (ignored due to invalid ID)
                "Description",  # Description (ignored due to invalid ID)
                {"a": 1},  # Settings dict (ignored due to invalid ID)
            )
            assert result is False  # Creation should be rejected for every invalid ID
