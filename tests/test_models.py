def test_registry_setting_creation(self):
    """Test creating a registry setting"""
    setting = RegistrySetting(
        id="reg1",
        name="Registry Test",
        description="Test registry setting",
        category=SettingCategory.SYSTEM,
        setting_type=SettingType.REGISTRY,
        value=1,
        default_value=0,
        hive="HKEY_CURRENT_USER",  # Required field
        key_path="Software\\Microsoft\\Windows\\CurrentVersion",  # Required
        value_name="TestValue",  # Required
        value_type="REG_DWORD"  # Required
    )
    
    assert setting.hive == "HKEY_CURRENT_USER"
    assert setting.key_path == "Software\\Microsoft\\Windows\\CurrentVersion"
    assert setting.value_name == "TestValue"
    assert setting.value_type == "REG_DWORD"
    assert setting.is_expanded == False  # Default value