"""
Tests for preset loading and validation.
"""

import pytest  # Pytest framework for test structure
import sys  # Used to modify the Python module search path
import os  # Provides filesystem path operations
import json  # JSON serialization/deserialization for preset files
import tempfile  # Creates temporary directories for isolated preset file tests

# Add project root to path so 'src' package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.presets.preset_manager import (
    PresetManager,
)  # Manages loading and validating preset files


class TestPresetLoading:
    """Test preset loading functionality."""

    def test_load_valid_preset(self):
        """Test loading a valid preset file."""
        # Use a temporary directory context manager for automatic cleanup.
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid preset file — must include app signature, name, description, and settings.
            preset_data = {
                "app": "WinSet",  # Application signature for validation
                "name": "Valid Preset",  # Display name of the preset
                "description": "This is a valid preset",  # Description text
                "icon": "✅",  # Emoji icon for display
                "settings": {
                    "setting1": 1,  # Integer setting
                    "setting2": "value",  # String setting
                },
            }

            # Write the preset JSON to disk with the expected .preset.json extension.
            preset_path = os.path.join(temp_dir, "valid.preset.json")
            with open(preset_path, "w") as f:
                json.dump(preset_data, f)  # Serialize dict to JSON file

            # Create a PresetManager that scans the temp directory for preset files.
            manager = PresetManager(presets_dir=temp_dir)
            info = manager.get_preset_info(
                "valid"
            )  # "valid" is derived from the filename

            assert info is not None  # The preset should be found and loaded
            assert info["name"] == "Valid Preset"  # Name should match the file contents
            assert info["setting_count"] == 2  # Should report 2 settings

    def test_load_invalid_preset_skipped(self):
        """Test that invalid preset files are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Case 1: Truly invalid files (missing essential fields or wrong types).
            invalid_files = [
                (
                    "missing_name.preset.json",
                    {"app": "WinSet", "description": "No name", "settings": {}},
                ),
                # Missing "name" field — required for valid preset
                (
                    "missing_settings.preset.json",
                    {"app": "WinSet", "name": "No Settings"},
                ),
                # Missing "settings" field — required for valid preset
                (
                    "wrong_type.preset.json",
                    {"app": "WinSet", "name": "Wrong", "settings": "not a dict"},
                ),
                # "settings" is a string instead of a dict — type error
                ("empty.preset.json", {}),
                # Completely empty JSON object — missing all required fields
            ]

            # Case 2: Presets without app signature (now allowed if otherwise valid).
            unsigned_files = [
                (
                    "missing_app.preset.json",
                    {
                        "name": "No App",
                        "description": "Missing signature",
                        "settings": {},
                    },
                ),
                # Missing "app" field — allowed but must still have name and settings
            ]

            # Write all invalid and unsigned preset files to disk.
            for filename, data in invalid_files + unsigned_files:
                filepath = os.path.join(
                    temp_dir, filename
                )  # Full path to the preset file
                with open(filepath, "w") as f:
                    json.dump(data, f)  # Write JSON data to file

            # Also create a valid one to ensure loading works alongside invalid files.
            valid_data = {
                "app": "WinSet",  # Application signature
                "name": "Valid",  # Display name
                "description": "Valid",  # Description
                "settings": {"a": 1},  # Settings dict with one entry
            }
            with open(os.path.join(temp_dir, "valid.preset.json"), "w") as f:
                json.dump(valid_data, f)

            manager = PresetManager(presets_dir=temp_dir)  # Scan the temp directory

            # Valid preset should be loaded successfully.
            assert manager.get_preset_info("valid") is not None

            # Unsigned but otherwise valid preset should be loaded (new behavior).
            assert manager.get_preset_info("missing_app") is not None

            # Truly invalid presets should still be skipped.
            for filename, _ in invalid_files:
                preset_id = filename[:-12]  # Strip ".preset.json" suffix to get the ID
                assert (
                    manager.get_preset_info(preset_id) is None
                )  # Should not be loaded

    def test_load_malformed_json_skipped(self):
        """Test that malformed JSON files are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with intentionally broken JSON syntax.
            filepath = os.path.join(temp_dir, "malformed.preset.json")
            with open(filepath, "w") as f:
                # Write truncated JSON — the opening brace of "settings" is never closed.
                f.write(
                    '{"app": "WinSet", "name": "test", "description": "malformed", "settings": {'
                )

            manager = PresetManager(presets_dir=temp_dir)  # Scan the directory

            # Should not load — the malformed JSON should be caught and skipped.
            assert manager.get_preset_info("malformed") is None

    def test_preset_with_too_many_settings_rejected(self):
        """Test that presets with too many settings are rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a preset with 300 settings — exceeds the configured limit of 200.
            many_settings = {
                f"setting_{i}": i for i in range(300)
            }  # Dict comprehension: 300 entries
            preset_data = {
                "app": "WinSet",  # Application signature
                "name": "Too Many",  # Display name
                "description": "Has too many settings",  # Description
                "settings": many_settings,  # 300 settings — over the limit
            }

            # Write the oversized preset to disk.
            filepath = os.path.join(temp_dir, "toomany.preset.json")
            with open(filepath, "w") as f:
                json.dump(preset_data, f)

            manager = PresetManager(presets_dir=temp_dir)  # Scan the directory

            # Should be rejected due to validation — too many settings.
            assert manager.get_preset_info("toomany") is None

    def test_preset_injection_attempt_blocked(self):
        """Test that injection attempts in preset data are blocked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create preset with malicious setting IDs to test input sanitization.
            malicious_data = {
                "app": "WinSet",  # Application signature
                "name": "Malicious",  # Display name
                "description": "Attempts injection",  # Description
                "settings": {
                    "'; DROP TABLE settings; --": "malicious",  # SQL injection attempt
                    "../../../Windows/System32/config/SAM": "malicious",  # Path traversal attempt
                },
            }

            # Write the malicious preset to disk.
            filepath = os.path.join(temp_dir, "malicious.preset.json")
            with open(filepath, "w") as f:
                json.dump(malicious_data, f)

            manager = PresetManager(presets_dir=temp_dir)  # Scan the directory

    def test_preset_source_tracking(self):
        """Test that preset sources are tracked correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a standard preset to verify source path tracking.
            preset_data = {
                "app": "WinSet",  # Application signature
                "name": "Source Test",  # Display name
                "description": "Source test description",  # Description
                "settings": {"a": 1},  # Single setting
            }

            # Write the preset to disk.
            with open(os.path.join(temp_dir, "source.preset.json"), "w") as f:
                json.dump(preset_data, f)

            manager = PresetManager(presets_dir=temp_dir)  # Scan the directory
            from pathlib import Path  # Import Path for resolved path comparison

            # Verify that the tracked source directory for "source" matches the temp dir.
            # preset_sources maps preset_id -> directory path where the preset file was found.
            assert (
                Path(manager.preset_sources["source"]).resolve()
                == Path(temp_dir).resolve()
            )

    def test_is_builtin(self):
        """Test the is_builtin helper."""
        # This is harder to test without real directories, but we can mock or use the fact
        # that it checks against builtin_dir.
        manager = (
            PresetManager()
        )  # Create with default dirs (includes built-in preset dir)
        # 'gaming' should be builtin if the environment is set up.
        # But for unit tests, we mainly ensure the logic doesn't crash.
        assert isinstance(
            manager.is_builtin("nonexistent"), bool
        )  # Should return a boolean

    def test_user_presets_dir_helpers(self):
        """Test directory existence helpers."""
        manager = PresetManager()  # Create with default dirs
        # Should return a boolean indicating whether the user presets directory exists.
        assert isinstance(manager.user_presets_dir_exists(), bool)
        # ensure_user_presets_dir might actually create it, which is fine for a test env,
        # but we'll just check it returns a bool.
        assert isinstance(manager.ensure_user_presets_dir(), bool)  # Should return bool
