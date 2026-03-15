# WinSet App Testing Guide

Testing an application that deeply modifies the Windows Registry and System state requires a careful approach. If done incorrectly, testing could inadvertently damage the host machine's configuration.

This guide outlines how to safely and effectively test WinSet using both automated testing frameworks (Pytest) and manual QA processes.

---

## 1. Automated Testing (Pytest)

We rely on Pytest to enforce internal logic correctness without touching the live Windows Registry. The overarching principle is **Mocking**. Tests should never actually apply settings or create System Restore Points on the developer's computer.

### Running Tests

To run the entire test suite and verify code coverage:
```powershell
python -m pytest tests/ --cov=src/
```

### Writing Safe Tests
When writing tests for modules like `src/storage/importer.py` or `src/presets/preset_manager.py`, you **must** use Pytest's `monkeypatch` or Python's `unittest.mock.patch` to intercept calls to the `RegistryHandler` and `BackupManager`.

**Example:**
Instead of letting a preset test accidentally disable telemetry on your dev machine, use a mock:

```python
from unittest.mock import patch, MagicMock
from src.presets.preset_manager import PresetManager

@patch('src.core.registry_handler.RegistryHandler.write_value')
def test_preset_application(mock_registry_write):
    # Setup
    manager = PresetManager()
    mock_registry_write.return_value = True # Pretend the registry write succeeded

    # Execution
    success, msg, results = manager.apply_preset("gaming")

    # Assertion
    assert success is True
    # Verify the method was called to apply a setting, but no real registry changes happened!
    mock_registry_write.assert_called() 
```

---

## 2. Manual User Acceptance Testing (UAT)

To verify the compiled output, the GUI, and actual System State changes (like turning off UI Transparency), manual testing is required.

### ⚠️ IMPORTANT: Safe Testing Sandbox ⚠️

**NEVER perform manual testing on your primary workstation if you are applying potentially destructive presets or importing unknown Json configurations!**

You should test applying presets using one of the following methods:

**Method A: Windows Sandbox (Recommended)**
Windows Sandbox provides a disposable, clean Windows environment that resets entirely when closed. 
1. Open the Start Menu and search for **Windows Sandbox**. (Enable it via "Turn Windows features on or off" if missing).
2. Copy the compiled `dist/WinSet.exe` executable and paste it directly onto the Sandbox desktop.
3. Run `WinSet.exe` (approve the UAC Admin prompt).
4. Apply the *Developer Mode* or *Performance* preset.
5. Verify the changes (e.g., Hidden files are now visible, minimize animations are gone).
6. Simply close the Sandbox to instantly undo all changes.

**Method B: Virtual Machines (Hyper-V / VirtualBox)**
If you need to test Windows Restarts (because some settings like *Disable Telemetry* require a reboot to take effect), use a Virtual Machine with snapshot capability.
1. Boot up a clean Windows 10/11 VM.
2. Create a "Pre-Winset" snapshot.
3. Run `WinSet.exe` and push settings.
4. Restart the VM.
5. Verify changes applied successfully across reboots.
6. Restore the "Pre-Winset" VM snapshot to return to a clean testing state.

### Using the Release Artifact
Always do your final manual testing using the exact artifact that users run.
1. Compile the project via `python scripts/build_exe.py`.
2. Move `/dist/WinSet.exe` completely out of the project folder (e.g., to your Desktop or a VM).
3. Ensure the app still runs, UI buttons work, and Presets correctly map and load without throwing "Missing File" exceptions (the preset JSONs must be internally bundled by Pyinstaller).
