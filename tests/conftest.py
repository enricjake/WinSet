"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "name": "Test Profile",
        "description": "A test profile",
        "version": "1.0",
        "settings": {
            "test_setting_1": {
                "value": 1,
                "description": "Test setting 1"
            },
            "test_setting_2": {
                "value": "test",
                "description": "Test setting 2"
            }
        }
    }

@pytest.fixture
def sample_registry_setting():
    """Sample registry setting for testing"""
    return {
        "hive": "HKEY_CURRENT_USER",
        "key_path": "Software\\WinSet\\Test",
        "value_name": "TestValue",
        "value_type": "REG_DWORD",
        "value": 1,
        "name": "Test Setting",
        "description": "A test registry setting"
    }

@pytest.fixture
def mock_registry(monkeypatch):
    """Mock registry access for testing"""
    class MockRegistry:
        def __init__(self):
            self.values = {}
            self.keys = {}
            
        def OpenKey(self, hive, key_path, reserved, access):
            key_id = f"{hive}\\{key_path}"
            if key_id not in self.keys:
                self.keys[key_id] = {}
            return key_id
            
        def CreateKey(self, hive, key_path):
            key_id = f"{hive}\\{key_path}"
            self.keys[key_id] = {}
            return key_id
            
        def SetValueEx(self, key, value_name, reserved, value_type, value):
            if key not in self.keys:
                self.keys[key] = {}
            self.keys[key][value_name] = (value, value_type)
            self.values[value_name] = value
            return True
            
        def QueryValueEx(self, key, value_name):
            if key in self.keys and value_name in self.keys[key]:
                return self.keys[key][value_name]
            return (None, None)
            
        def CloseKey(self, key):
            pass
    
    mock_reg = MockRegistry()
    
    # Mock winreg functions
    monkeypatch.setattr('winreg.OpenKey', mock_reg.OpenKey)
    monkeypatch.setattr('winreg.CreateKey', mock_reg.CreateKey)
    monkeypatch.setattr('winreg.SetValueEx', mock_reg.SetValueEx)
    monkeypatch.setattr('winreg.QueryValueEx', mock_reg.QueryValueEx)
    monkeypatch.setattr('winreg.CloseKey', mock_reg.CloseKey)
    
    # Mock winreg constants
    monkeypatch.setattr('winreg.HKEY_CURRENT_USER', 'HKEY_CURRENT_USER')
    monkeypatch.setattr('winreg.HKEY_LOCAL_MACHINE', 'HKEY_LOCAL_MACHINE')
    monkeypatch.setattr('winreg.HKEY_CLASSES_ROOT', 'HKEY_CLASSES_ROOT')
    monkeypatch.setattr('winreg.HKEY_CURRENT_CONFIG', 'HKEY_CURRENT_CONFIG')
    monkeypatch.setattr('winreg.HKEY_USERS', 'HKEY_USERS')
    
    monkeypatch.setattr('winreg.REG_SZ', 'REG_SZ')
    monkeypatch.setattr('winreg.REG_DWORD', 'REG_DWORD')
    monkeypatch.setattr('winreg.REG_BINARY', 'REG_BINARY')
    monkeypatch.setattr('winreg.REG_MULTI_SZ', 'REG_MULTI_SZ')
    monkeypatch.setattr('winreg.REG_EXPAND_SZ', 'REG_EXPAND_SZ')
    monkeypatch.setattr('winreg.REG_QWORD', 'REG_QWORD')
    
    return mock_reg