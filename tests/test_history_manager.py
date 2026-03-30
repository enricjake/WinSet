"""
Tests for history manager
"""

import pytest  # Pytest framework for fixtures and monkeypatch support
import sys  # Used to modify the Python module search path
import os  # Provides filesystem path and file deletion operations
import tempfile  # Creates temporary files for isolated database tests
import sqlite3  # SQLite database interface (used indirectly by HistoryManager)

# Add project root to path so 'src' package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.history_manager import (
    HistoryManager,
)  # Manages change history in an SQLite database
from src.models.setting import (
    RegistrySetting,
    SettingCategory,
    SettingType,
)  # Data models for settings


class TestHistoryManager:
    """Test HistoryManager class"""

    def setup_method(self):
        """Setup test database"""
        # Create a temporary database file for testing — each test gets its own isolated DB.
        # delete=False keeps the file on disk after closing so HistoryManager can open it.
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_file.close()  # Close the file handle so HistoryManager can open it exclusively
        # Instantiate HistoryManager pointing at the temporary database file.
        # self.history: HistoryManager instance under test
        self.history = HistoryManager(db_path=self.db_file.name)

    def teardown_method(self):
        """Cleanup test database"""
        self.history.close()  # Close the SQLite connection to release the file lock
        os.unlink(self.db_file.name)  # Delete the temporary database file from disk

    def test_initialization(self):
        """Test history manager initialization"""
        assert self.history is not None  # Verify the HistoryManager was created
        assert os.path.exists(
            self.db_file.name
        )  # Verify the database file exists on disk

    def test_log_and_retrieve_change(self):
        """Test logging and retrieving a change"""
        # Create a mock setting — a RegistrySetting representing a DWORD registry value.
        setting = RegistrySetting(
            id="test_setting",  # Unique identifier for this setting
            name="Test Setting",  # Human-readable display name
            description="A test setting",  # Description text
            category=SettingCategory.SYSTEM,  # Categorizes the setting under "System"
            setting_type=SettingType.REGISTRY,  # Indicates this is a registry-based setting
            value=1,  # Current value of the setting
            default_value=0,  # Factory default value
            hive="HKEY_CURRENT_USER",  # Registry hive root
            key_path="Software\\Test",  # Registry subkey path
            value_name="TestValue",  # Registry value entry name
            value_type="REG_DWORD",  # Registry data type (32-bit unsigned integer)
        )

        # Log a change from old_value=0 to new_value=1
        self.history.log_change(setting, old_value=0, new_value=1)

        # Retrieve history — returns a list of tuples from the changes table.
        history = self.history.get_history()
        assert len(history) == 1  # Exactly one change should be recorded

        change = history[0]  # Unpack the first (and only) change record
        assert change[2] == "Test Setting"  # Index 2: setting_name column
        assert change[3] == "0"  # Index 3: old_value column (stored as string)
        assert change[4] == "1"  # Index 4: new_value column (stored as string)

    def test_get_change_details(self):
        """Test retrieving change details"""
        # Create a RegistrySetting to log a change against.
        setting = RegistrySetting(
            id="test_setting",  # Unique setting identifier
            name="Test Setting",  # Display name
            description="A test setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry-based setting type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Registry hive
            key_path="Software\\Test",  # Registry key path
            value_name="TestValue",  # Registry value name
            value_type="REG_DWORD",  # Registry value type
        )

        self.history.log_change(setting, old_value=0, new_value=1)  # Record the change

        # Get the change ID from the history list to use for detail lookup.
        history = self.history.get_history()  # Retrieve all logged changes
        change_id = history[0][
            0
        ]  # Index 0 of the tuple is the change ID (auto-incremented)

        # Get full details for the specific change record.
        details = self.history.get_change_details(change_id)
        assert details is not None  # Verify details were returned
        assert details[0] == "HKEY_CURRENT_USER"  # Hive stored in the detail record
        assert details[2] == "TestValue"  # Value name stored in the detail record
        assert details[4] == "0"  # Old value stored in the detail record

    def test_revert_change(self, monkeypatch):
        """Test reverting a change"""
        # Create a setting and log a change to prepare for the revert test.
        setting = RegistrySetting(
            id="test_setting",  # Unique setting identifier
            name="Test Setting",  # Display name
            description="A test setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry-based type
            value=1,  # Current (new) value
            default_value=0,  # Default (old) value
            hive="HKEY_CURRENT_USER",  # Registry hive
            key_path="Software\\Test",  # Registry key path
            value_name="TestValue",  # Registry value name
            value_type="REG_DWORD",  # DWORD type
        )

        self.history.log_change(setting, old_value=0, new_value=1)  # Record the change

        # Mock registry handler — simulates writing a value back to the registry
        # without actually modifying the Windows registry.
        def mock_write_value(hive, key_path, value_name, value_type, value):
            # hive: str — registry hive name
            # key_path: str — subkey path
            # value_name: str — value entry name
            # value_type: str — registry type constant
            # value: any — value to write
            return True  # Simulate successful write

        # Create a MagicMock to stand in for the RegistryHandler class.
        from unittest.mock import MagicMock

        mock_handler = MagicMock()  # MagicMock object that auto-generates method stubs
        mock_handler.write_value = mock_write_value  # Attach the mock write function

        # Patch the RegistryHandler class in the module where HistoryManager imports it.
        # This ensures that when HistoryManager.revert_change() creates a RegistryHandler,
        # it gets our mock instead of the real one.
        monkeypatch.setattr(
            "src.core.registry_handler.RegistryHandler", lambda: mock_handler
        )

        # Get the change ID and revert the change.
        history = self.history.get_history()  # Retrieve the logged changes
        change_id = history[0][0]  # Get the ID of the change to revert

        success = self.history.revert_change(change_id)  # Attempt to revert
        assert success == True  # Revert should succeed

        # Check that the change is marked as reverted in the database.
        # Use the history manager's connection to avoid file locking issues.
        cursor = (
            self.history._conn.cursor()
        )  # Get a cursor from the existing DB connection
        cursor.execute("SELECT reverted FROM changes WHERE id = ?", (change_id,))
        result = cursor.fetchone()  # Fetch the single result row
        assert result[0] == 1  # reverted flag should be set to 1 (True)

    def test_get_changes_by_setting(self):
        """Test filtering changes by setting ID"""
        # Create two distinct settings to log separate changes against.
        setting1 = RegistrySetting(
            id="setting1",  # ID for the first setting
            name="Setting 1",  # Display name
            description="First setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="Value1",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )

        setting2 = RegistrySetting(
            id="setting2",  # ID for the second setting
            name="Setting 2",  # Display name
            description="Second setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="Value2",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )

        # Log changes for both settings — 2 changes for setting1, 1 for setting2.
        self.history.log_change(setting1, old_value=0, new_value=1)
        self.history.log_change(setting2, old_value=0, new_value=1)
        self.history.log_change(setting1, old_value=1, new_value=2)

        # Get changes filtered to only setting1.
        setting1_changes = self.history.get_changes_by_setting("setting1")
        assert (
            len(setting1_changes) == 2
        )  # Should return exactly 2 changes for setting1

        # Check that we have the right changes (old_value, new_value).
        # Note: changes are returned in reverse chronological order.
        # The tuple is (id, timestamp, old_value, new_value, reverted).
        # Since both changes may share the same timestamp, we check for both possibilities.

        # Collect the actual old and new values from the result tuples.
        old_values = [
            str(change[2]) for change in setting1_changes
        ]  # Extract old_value column
        new_values = [
            str(change[3]) for change in setting1_changes
        ]  # Extract new_value column

        # We should have one change with old=0,new=1 and one with old=1,new=2.
        assert "0" in old_values and "1" in old_values  # Both old values present
        assert "1" in new_values and "2" in new_values  # Both new values present
        assert (
            old_values.count("0") == 1 and old_values.count("1") == 1
        )  # Each appears once
        assert (
            new_values.count("1") == 1 and new_values.count("2") == 1
        )  # Each appears once

    def test_export_history(self):
        """Test exporting history to file"""
        # Create a setting and log a change to have data to export.
        setting = RegistrySetting(
            id="test_setting",  # Unique identifier
            name="Test Setting",  # Display name
            description="A test setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="TestValue",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )

        self.history.log_change(setting, old_value=0, new_value=1)  # Record a change

        # Export to a temporary JSON file.
        export_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        export_file.close()  # Close handle so export_history can write to it

        success = self.history.export_history(export_file.name)  # Perform the export
        assert success == True  # Export should succeed
        assert os.path.exists(export_file.name)  # File should exist on disk

        # Cleanup — delete the temporary export file.
        os.unlink(export_file.name)

    def test_clear_history(self):
        """Test clearing history"""
        # Create a setting and log two changes to have data to clear.
        setting = RegistrySetting(
            id="test_setting",  # Unique identifier
            name="Test Setting",  # Display name
            description="A test setting",  # Description
            category=SettingCategory.SYSTEM,  # System category
            setting_type=SettingType.REGISTRY,  # Registry type
            value=1,  # Current value
            default_value=0,  # Default value
            hive="HKEY_CURRENT_USER",  # Hive
            key_path="Software\\Test",  # Key path
            value_name="TestValue",  # Value name
            value_type="REG_DWORD",  # DWORD type
        )

        # Add some changes to the history.
        self.history.log_change(setting, old_value=0, new_value=1)
        self.history.log_change(setting, old_value=1, new_value=2)

        # Verify changes exist before clearing.
        history = self.history.get_history()
        assert len(history) == 2  # Two changes should be present

        # Clear the entire history.
        success = self.history.clear_history()
        assert success == True  # Clear operation should succeed

        # Verify history is now empty after clearing.
        history = self.history.get_history()
        assert len(history) == 0  # No changes should remain
