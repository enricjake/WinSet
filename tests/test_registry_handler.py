"""
Tests for registry handler
"""

import pytest  # Pytest framework for fixtures, monkeypatch, and exception assertion
import sys  # Used to modify the Python module search path
import os  # Provides path operations

# Add src to path so core and model modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.registry_handler import (
    RegistryHandler,
)  # Handles Windows registry read/write operations
from models.setting import RegistrySetting  # Data model for registry-backed settings


class TestRegistryHandler:
    """Test RegistryHandler class"""

    def test_handler_initialization(self):
        """Test creating registry handler"""
        handler = RegistryHandler()  # Instantiate a new RegistryHandler
        assert handler is not None  # Verify the handler object was created

    def test_hive_conversion(self):
        """Test hive string to constant conversion"""
        handler = RegistryHandler()  # Create a handler instance

        # _get_hive_constant converts a hive name string to the corresponding
        # winreg module constant (e.g. "HKEY_CURRENT_USER" -> winreg.HKEY_CURRENT_USER).
        # Test valid hive names — each should return a non-None constant.
        assert handler._get_hive_constant("HKEY_CURRENT_USER") is not None  # HKCU
        assert handler._get_hive_constant("HKEY_LOCAL_MACHINE") is not None  # HKLM
        assert handler._get_hive_constant("HKEY_CLASSES_ROOT") is not None  # HKCR

        # Test invalid hive — should raise ValueError for unrecognized hive names.
        with pytest.raises(ValueError):
            handler._get_hive_constant("INVALID_HIVE")  # Not a real hive name

    def test_type_conversion(self):
        """Test registry type string to constant conversion"""
        handler = RegistryHandler()  # Create a handler instance

        # _get_type_constant converts a type name string to the winreg constant integer.
        assert handler._get_type_constant("REG_SZ") == 1  # winreg.REG_SZ = 1 (string)
        assert (
            handler._get_type_constant("REG_DWORD") == 4
        )  # winreg.REG_DWORD = 4 (32-bit int)
        assert (
            handler._get_type_constant("REG_BINARY") == 3
        )  # winreg.REG_BINARY = 3 (binary)

        # Invalid type name should raise ValueError.
        with pytest.raises(ValueError):
            handler._get_type_constant("INVALID_TYPE")  # Not a recognized registry type

    def test_read_write_mock(self, mock_registry, monkeypatch):
        """Test registry operations with mock"""
        handler = RegistryHandler()  # Create a handler instance

        # Mock the actual registry operations to avoid touching the real Windows registry.
        def mock_open_key(hive, key, reserved, access):
            # hive: str — hive name constant
            # key: str — subkey path
            # reserved: int — reserved parameter
            # access: int — access rights
            return "mock_key"  # Return a fake key handle

        def mock_set_value(key, value_name, reserved, type_const, value):
            # key: str — key handle
            # value_name: str — name of value to set
            # reserved: int — reserved parameter
            # type_const: int — registry type constant
            # value: any — value to write
            mock_registry.values[value_name] = value  # Store value in the mock registry
            return True  # Simulate successful write

        # Patch winreg functions with mock implementations.
        monkeypatch.setattr("winreg.OpenKey", mock_open_key)  # Replace OpenKey
        monkeypatch.setattr("winreg.SetValueEx", mock_set_value)  # Replace SetValueEx

        # Test writing a DWORD value through the handler.
        result = handler.write_value(
            "HKEY_CURRENT_USER",  # Hive name
            "Software\\Test",  # Key path
            "TestValue",  # Value name
            "REG_DWORD",  # Value type
            42,  # Value to write
        )
        assert result == True  # Write should succeed
        assert mock_registry.values["TestValue"] == 42  # Value should be stored in mock

    def test_bulk_operations_mock(self, mock_registry, monkeypatch):
        """Test bulk registry operations with mock"""
        handler = RegistryHandler()  # Create a handler instance

        # Mock the actual registry operations for bulk testing.
        def mock_open_key(hive, key, reserved, access):
            # hive: str — hive name
            # key: str — subkey path
            # reserved: int — reserved
            # access: int — access rights
            return "mock_key"  # Return a fake key handle

        def mock_set_value(key, value_name, reserved, type_const, value):
            # key: str — key handle
            # value_name: str — value name
            # reserved: int — reserved
            # type_const: int — type constant
            # value: any — value to write
            mock_registry.values[value_name] = value  # Store in mock registry
            return True

        def mock_query_value(key, value_name):
            # key: str — key handle
            # value_name: str — value name to look up
            # Returns: tuple (value, type_constant) or (None, None)
            return mock_registry.values.get(
                value_name, None
            ), 1  # 1 = REG_SZ type constant

        # Patch winreg functions for bulk operations.
        monkeypatch.setattr("winreg.OpenKey", mock_open_key)  # Replace OpenKey
        monkeypatch.setattr("winreg.SetValueEx", mock_set_value)  # Replace SetValueEx
        monkeypatch.setattr(
            "winreg.QueryValueEx", mock_query_value
        )  # Replace QueryValueEx

        # Test bulk write — list of (hive, key_path, value_name, type, value) tuples.
        operations = [
            (
                "HKEY_CURRENT_USER",
                "Software\\Test",
                "Value1",
                "REG_DWORD",
                1,
            ),  # DWORD op
            (
                "HKEY_CURRENT_USER",
                "Software\\Test",
                "Value2",
                "REG_SZ",
                "test",
            ),  # String op
        ]

        results = handler.write_multiple_values(operations)  # Execute bulk write
        assert len(results) == 2  # Should return results for both operations
        assert all(results.values())  # All operations should have succeeded

        # Test bulk read — read multiple values from the same key.
        read_results = handler.read_multiple_values(
            "HKEY_CURRENT_USER",  # Hive name
            "Software\\Test",  # Key path
            ["Value1", "Value2", "Value3"],  # List of value names to read
        )
        assert len(read_results) == 3  # Should return results for all 3 names
        assert read_results["Value1"] == 1  # Value1 was written as DWORD 1
        assert read_results["Value2"] == "test"  # Value2 was written as string "test"
        assert (
            read_results["Value3"] is None
        )  # Value3 was never written — should be None

    def test_key_operations_mock(self, monkeypatch):
        """Test key existence checking with mock"""
        handler = RegistryHandler()  # Create a handler instance

        # Create a mock PyHKEY object that behaves like a real PyHKEY handle.
        # This simulates the opaque handle objects returned by winreg.OpenKey.
        class MockPyHKEY:
            def __init__(self):
                self.closed = False  # Track whether the handle has been closed

            def Close(self):
                # Simulates closing a registry key handle.
                self.closed = True  # Mark as closed
                return None

            def __enter__(self):
                # Context manager entry — returns self for 'with' statement support.
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                # Context manager exit — closes the handle when leaving the 'with' block.
                # exc_type: exception type (or None if no exception)
                # exc_val: exception value (or None)
                # exc_tb: exception traceback (or None)
                self.Close()  # Ensure handle is closed

        def mock_open_key_success(hive, key, reserved, access):
            # Simulates a successful key open — returns a MockPyHKEY handle.
            return MockPyHKEY()

        def mock_open_key_fail(hive, key, reserved, access):
            # Simulates a failed key open — raises FileNotFoundError.
            raise FileNotFoundError("Key not found")

        # Mock CloseKey to accept our mock object.
        def mock_close_key(key):
            # key: any — key handle (may be MockPyHKEY or real handle)
            if hasattr(key, "Close"):
                key.Close()  # Call Close if the object supports it
            return None

        # Test key_exists returns True when OpenKey succeeds.
        monkeypatch.setattr(
            "winreg.OpenKey", mock_open_key_success
        )  # Key open succeeds
        monkeypatch.setattr("winreg.CloseKey", mock_close_key)  # Patch CloseKey
        assert handler.key_exists("HKEY_CURRENT_USER", "Software\\Test") == True

        # Test key_exists returns False when OpenKey raises FileNotFoundError.
        monkeypatch.setattr("winreg.OpenKey", mock_open_key_fail)  # Key open fails
        assert handler.key_exists("HKEY_CURRENT_USER", "Software\\Test") == False
