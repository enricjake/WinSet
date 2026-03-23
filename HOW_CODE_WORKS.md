# How WinSet Code Works

## Architecture Overview
WinSet follows a modular architecture with clear separation of concerns:

1. **Entry Point** (`winset.py`): 
   - Checks for administrator privileges
   - Launches the main GUI window

2. **Core Components**:
   - **Settings System**: Defines setting types and categories
   - **Registry Handler**: Reads/writes Windows Registry values
   - **PowerShell Handler**: Executes PowerShell commands for system operations
   - **Setting Loader**: Loads setting definitions from JSON resources

3. **Data Models** (`src/models/`):
   - `Setting`: Base class for all setting types
   - `RegistrySetting`: Registry-specific settings with apply/validation logic
   - `PowerSetting`: Power plan management
   - `ServiceSetting`: Windows service control
   - `Profile`: Collection of settings with import/export capabilities

4. **Preset System** (`src/presets/preset_manager.py`):
   - Discovers and loads JSON preset files
   - Maps preset names to file paths
   - Loads and applies presets via ProfileImporter

5. **Storage** (`src/storage/`):
   - `ProfileImporter`: Loads profiles from JSON
   - `ProfileExporter`: Saves profiles to JSON
   - Backup management utilities

6. **GUI** (`src/gui/main_window.py`):
   - Main application interface
   - Displays settings by category
   - Manages preset application and profile operations

## Data Flow
1. **Startup**: 
   - `winset.py` → checks admin → launches `MainWindow`

2. **Settings Loading**:
   - `SettingLoader` reads `resources/settings.json`
   - Creates `RegistrySetting` objects organized by category
   - Settings are made available to GUI for display

3. **Preset Application**:
   - User selects preset in GUI
   - `PresetManager` locates preset file
   - `ProfileImporter` loads JSON into `Profile` object
   - `Profile.apply_all()` iterates through settings
   - Each setting's `apply()` method calls appropriate handler:
     - `RegistrySetting` → `RegistryHandler.write_value()`
     - `PowerSetting` → `PowerShellHandler.set_power_plan()`
     - `ServiceSetting` → `PowerShellHandler.disable_service()`

4. **Persistence**:
   - Profiles can be exported/imported via `ProfileExporter`/`ProfileImporter`
   - Includes checksum verification for integrity

## Key Implementation Details
- **Thread Safety**: Handlers are instantiated per-use to avoid state issues
- **Error Handling**: Operations return success/failure booleans with logging
- **Admin Requirements**: Automatic elevation prompt for privileged operations
- **Extensibility**: New setting types can be added by extending `Setting` class
- **Resource Management**: Settings definitions externalized in JSON for easy updates

## Dependencies
- Python standard library (tkinter, winreg, subprocess, etc.)
- Windows OS (for registry/PowerShell integration)
- No external Python packages required for core functionality

This design allows WinSet to safely and efficiently manage Windows settings through a unified interface while maintaining modularity and extensibility.