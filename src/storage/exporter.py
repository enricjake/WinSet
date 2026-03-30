import json  # For serializing profile data to JSON format for file output
import os  # For filesystem operations like creating output directories
import platform  # For querying the current Windows OS version string
import base64  # For encoding binary registry values as ASCII-safe strings
from typing import List  # For type-hinting lists of RegistrySetting objects

# WinSet data models representing a configuration profile and individual registry settings
from src.models.profile import Profile
from src.models.setting import RegistrySetting

# Handles low-level reads from the Windows Registry via the winreg module
from src.core.registry_handler import RegistryHandler


class ProfileExporter:
    """Exports current system settings to a JSON profile file."""

    def __init__(self):
        """Initialize the exporter with a RegistryHandler."""
        # RegistryHandler instance used to read live values from the Windows Registry.
        # It wraps winreg calls and provides a simplified read_value(hive, key_path, value_name) API.
        self.registry = RegistryHandler()

    def _get_windows_version(self) -> str:
        """Retrieves the Windows OS version."""
        # Combines platform.system() (e.g. "Windows"),
        # platform.release() (e.g. "10"), and
        # platform.version() (e.g. "10.0.19041") into a single descriptive string.
        # This string is stored in the exported profile so users know which OS the
        # settings were captured from.
        return f"{platform.system()} {platform.release()} ({platform.version()})"

    def _serialize_registry_value(self, setting: RegistrySetting, value):
        """Convert non-JSON-safe registry values into lossless JSON form.

        Parameters
        ----------
        setting : RegistrySetting
            The setting descriptor that declares the registry value's type
            (e.g. "REG_BINARY", "REG_DWORD"). Used to decide how to encode value.
        value : Any
            The raw value returned by RegistryHandler.read_value(). May be an
            int, str, bytes, bytearray, or None depending on the registry type.

        Returns
        -------
        Any
            Either the original value (if already JSON-serializable) or a dict
            with an "__encoding__" key so the value can be round-tripped losslessly.
        """
        # REG_BINARY values arrive as bytes/bytearray which JSON cannot serialize directly.
        # We encode them as base64 ASCII strings wrapped in a sentinel dict so the
        # importer can detect and decode them back to raw bytes later.
        if setting.value_type == "REG_BINARY" and isinstance(value, (bytes, bytearray)):
            return {
                "__encoding__": "base64",  # Sentinel key identifying the encoding scheme
                "data": base64.b64encode(bytes(value)).decode(
                    "ascii"
                ),  # Base64-encoded binary payload as an ASCII string
            }
        # All other types (int, str, etc.) are already JSON-safe and returned unchanged.
        return value

    def export_profile(
        self,
        settings_to_export: List[RegistrySetting],
        output_path: str,
        profile_name: str = "Exported Profile",
        description: str = "",
    ) -> bool:
        """Reads current system values for provided settings and saves them to a file.

        This is the main entry point for the export workflow. It:
        1. Creates a Profile with metadata (name, description, OS version).
        2. Reads each requested setting's live value from the registry.
        3. Serializes non-JSON-safe values (e.g. binary blobs).
        4. Writes the complete profile to a JSON file with an integrity checksum.

        Parameters
        ----------
        settings_to_export : List[RegistrySetting]
            The list of setting descriptors whose current registry values should
            be captured. Each entry specifies a hive, key path, and value name.
        output_path : str
            Full file path where the JSON profile will be written.
            Parent directories are created automatically if they don't exist.
        profile_name : str, optional
            Human-readable name for the profile (default "Exported Profile").
            Stored in the JSON metadata block.
        description : str, optional
            Free-text description of what this profile captures (default "").
            Stored in the JSON metadata block for user documentation.

        Returns
        -------
        bool
            True if the export completed successfully, False if any exception
            occurred (the error is printed to stdout).
        """
        try:
            # -----------------------------------------------------------
            # Step 1 – Build a Profile object with user-supplied metadata
            # -----------------------------------------------------------
            # Profile holds the name, description, OS version, and a list
            # of captured RegistrySetting objects. It also generates a
            # checksum when export() is called to detect tampering.
            profile = Profile(
                name=profile_name,  # Display name for the saved profile
                description=description,  # Optional user-facing description
                windows_version=self._get_windows_version(),  # OS version at time of capture
            )

            # -----------------------------------------------------------
            # Step 2 – Read each setting's live value from the registry
            # -----------------------------------------------------------
            for setting in settings_to_export:
                # Query the Windows Registry for the current value of this setting.
                # hive: the root key (e.g. HKEY_CURRENT_USER)
                # key_path: the subkey path (e.g. "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer")
                # value_name: the specific value name within that key
                current_value = self.registry.read_value(
                    hive=setting.hive,
                    key_path=setting.key_path,
                    value_name=setting.value_name,
                )

                # Only include settings that actually exist in the registry.
                # A None return means the key/value was not found, so we skip it
                # rather than writing a null entry into the profile.
                if current_value is not None:
                    # Encode binary or other non-JSON-safe types into a
                    # serializable representation (e.g. base64 wrapper dict).
                    setting.value = self._serialize_registry_value(
                        setting, current_value
                    )
                    # Add the populated setting to the profile's internal list.
                    profile.add_setting(setting)

            # -----------------------------------------------------------
            # Step 3 – Write the profile to disk as a JSON file
            # -----------------------------------------------------------
            # Ensure the destination directory tree exists. os.path.abspath
            # resolves relative paths, and os.path.dirname extracts the
            # directory portion so makedirs can create it recursively.
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # profile.export() returns a dict containing metadata, settings,
            # and a SHA-256 checksum for integrity verification.
            # json.dump serializes it to the file with 4-space indentation
            # for human readability, using UTF-8 to support Unicode values.
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(profile.export(), f, indent=4)

            # Indicate successful export to the caller (GUI or CLI layer).
            return True

        except Exception as e:
            # Catch-all for registry access errors, file I/O failures, or
            # serialization issues. Print the error so the user can diagnose
            # the problem and return False to signal failure.
            print(f"Error exporting profile: {e}")
            return False
