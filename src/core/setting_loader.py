"""
Setting Loader for WinSet - Loads settings from JSON with security validation.
"""

import json  # For parsing the settings.json file
import os  # For filesystem path operations and existence checks
import re  # For regex-based security pattern matching on registry key paths
import sys  # Imported for potential system-level operations (not directly used)
from pathlib import Path  # For safe, OS-independent path resolution and validation
from typing import (
    List,
    Dict,
    Optional,
    Any,
)  # Type hints for function signatures and class attributes
from src.models.setting import (
    RegistrySetting,
    SettingCategory,
    SettingType,
    Setting,
)  # Domain models representing Windows registry settings and their categorization


def _safe_print(*args, **kwargs):
    """Print with Unicode-safe encoding."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode with replacement characters when the terminal
        # cannot handle Unicode (e.g., Windows cmd with ASCII codepage).
        # Each argument is encoded to ASCII with '?' replacements for
        # unmappable characters, then decoded back to a printable string.
        safe_args = [
            str(arg).encode("ascii", "replace").decode("ascii") for arg in args
        ]
        print(*safe_args, **kwargs)


class SettingLoader:
    """Loads settings from resources/settings.json with security validation"""

    # CATEGORY_MAP: Maps human-readable category names (as they appear in the
    # JSON settings file) to the internal SettingCategory enum values. This
    # allows the JSON to use descriptive names like "System Appearance" while
    # the application uses structured enum values. Unmapped names default to
    # SettingCategory.SYSTEM (handled in load_settings).
    CATEGORY_MAP = {
        "System Appearance": SettingCategory.APPEARANCE,  # Desktop, theme, display tweaks
        "File Explorer Settings": SettingCategory.FILE_EXPLORER,  # Explorer view and behavior options
        "Taskbar & Start Menu": SettingCategory.TASKBAR,  # Taskbar position, Start menu layout
        "Power Settings": SettingCategory.POWER,  # Sleep, hibernate, power plan options
        "Privacy Options": SettingCategory.PRIVACY,  # Telemetry, app permissions
        "Privacy Settings": SettingCategory.PRIVACY,  # Alternate JSON label for privacy group
        "Keyboard & Mouse": SettingCategory.KEYBOARD,  # Input device sensitivity and behavior
        "Mouse & Keyboard Settings": SettingCategory.KEYBOARD,  # Alternate JSON label for input group
        "Regional & Language Settings": SettingCategory.SYSTEM,  # Locale settings (falls under SYSTEM)
        "Accessibility Settings": SettingCategory.SYSTEM,  # Ease-of-access (falls under SYSTEM)
        "Gaming Settings": SettingCategory.SYSTEM,  # Game bar, DVR (falls under SYSTEM)
        "System & Performance": SettingCategory.SYSTEM,  # Performance tuning (falls under SYSTEM)
        "Network Settings": SettingCategory.NETWORK,  # Proxy, adapter, firewall settings
        "Advanced Settings": SettingCategory.SYSTEM,  # Miscellaneous advanced tweaks
    }

    # ALLOWED_HIVES: Whitelist of Windows registry hive roots that settings
    # are permitted to target. Only these two hives are accepted during
    # validation to prevent settings from modifying HKEY_CLASSES_ROOT,
    # HKEY_USERS, or other sensitive hives that could destabilize the system.
    ALLOWED_HIVES = ["HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE"]

    # BLOCKED_KEY_PATTERNS: Regex patterns for registry key paths that are
    # explicitly forbidden even within allowed hives. These protect critical
    # system areas such as SAM (Security Account Manager), security policies,
    # and secure pipe servers. The path-traversal pattern (\\.\\.\) prevents
    # crafted paths from escaping the intended registry namespace.
    BLOCKED_KEY_PATTERNS = [
        r"\\\\Security\\\\",  # Security policy keys
        r"\\\\SAM\\\\",  # Security Account Manager
        r"\\\\System\\\\CurrentControlSet\\\\Control\\\\SecurePipeServers",  # Secure pipe servers
        r"\\\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Policies\\\\System\\\\*",  # System policies
        r"\\\\.\\.\\\\",  # Path traversal (e.g., ..\..\)
    ]

    def __init__(self, resource_path: Optional[str] = None):
        """
        Initialize setting loader with optional custom resource path.

        Args:
            resource_path: Optional path to settings.json. If not provided,
                          uses the default location within the application.

        Raises:
            ValueError: If the provided resource path is outside the application directory.
        """
        # If no custom path is given, derive the default path by navigating
        # two directories up from this file (src/core -> project root),
        # then into the "resources" folder for settings.json.
        if resource_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.resource_path = os.path.join(base_dir, "resources", "settings.json")
        else:
            # Validate external path to prevent path traversal attacks
            # and ensure it points to a safe, allowed location.
            self.resource_path = self._validate_resource_path(resource_path)

        # settings_by_category: Dictionary mapping each SettingCategory enum
        # to a list of RegistrySetting objects belonging to that category.
        # Populated by load_settings() during initialization.
        self.settings_by_category: Dict[SettingCategory, List[RegistrySetting]] = {}

        # Immediately load and parse settings from the JSON file so the
        # loader is ready to serve settings as soon as it is constructed.
        self.load_settings()

    def _validate_resource_path(self, path: str) -> str:
        """
        Validate that a resource path is safe to access.

        Args:
            path: The path to validate

        Returns:
            The resolved safe path

        Raises:
            ValueError: If the path is unsafe
        """
        try:
            # Resolve the path to an absolute, symlink-resolved form to
            # eliminate any ".." or symbolic link tricks.
            safe_path = Path(path).resolve()

            # Determine the application's base directory (two levels up from
            # this file) and resolve it for accurate comparison.
            base_dir = Path(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ).resolve()

            # Check if the resolved path is inside the application directory.
            # If not, also allow the user's ~/Documents/WinSet folder as a
            # secondary permitted location for custom user profiles.
            if base_dir not in safe_path.parents and safe_path != base_dir:
                # user_docs: The user's Documents/WinSet directory, which is
                # an additional allowed location for custom settings files.
                user_docs = Path(os.path.expanduser("~")) / "Documents" / "WinSet"
                if (
                    user_docs.resolve() not in safe_path.parents
                    and safe_path != user_docs.resolve()
                ):
                    raise ValueError(
                        f"Resource path '{path}' is outside allowed directories. "
                        f"Allowed: {base_dir} or {user_docs}"
                    )

            # Ensure the file has a .json extension to prevent loading
            # arbitrary file types (e.g., .exe, .dll, .bat).
            if safe_path.suffix.lower() != ".json":
                raise ValueError(f"Invalid file type. Only .json files are allowed.")

            # Check file size if the file already exists on disk.
            # A 10 MB cap prevents denial-of-service via oversized files.
            if safe_path.exists():
                size = safe_path.stat().st_size
                if size > 10 * 1024 * 1024:  # 10 MB limit
                    raise ValueError(f"File too large: {size} bytes (max 10MB)")

            return str(safe_path)

        except Exception as e:
            raise ValueError(f"Invalid resource path: {e}")

    def _validate_setting_data(
        self, s_data: dict, category_name: str
    ) -> tuple[bool, str]:
        """
        Validate setting data before creating RegistrySetting.

        Args:
            s_data: Setting dictionary from JSON — a single setting entry
                    containing fields like "name", "hive", "key", "value", "type".
            category_name: Category name string used for error reporting
                           to identify which category a bad setting belongs to.

        Returns:
            Tuple of (is_valid, error_message) — True and empty string if
            valid, or False with a descriptive error message if invalid.
        """
        # required: The five mandatory fields every setting entry must contain.
        required = ["name", "hive", "key", "value", "type"]
        for field in required:
            if field not in s_data:
                return False, f"Missing required field: {field}"

        # name: The display name of the setting. Capped at 200 characters
        # to prevent excessively long names from bloating the UI.
        name = s_data.get("name", "")
        if len(name) > 200:
            return False, f"Setting name too long: {len(name)} chars (max 200)"

        # hive: The registry hive root (e.g., HKEY_CURRENT_USER).
        # Must be in the ALLOWED_HIVES whitelist for security.
        hive = s_data["hive"]
        if hive not in self.ALLOWED_HIVES:
            return False, f"Invalid hive: {hive}. Allowed: {self.ALLOWED_HIVES}"

        # key_path: The registry key path beneath the hive (e.g.,
        # "Software\Microsoft\Windows\CurrentVersion").
        # Checked for path traversal (".."), network path prefixes ("\\\\"),
        # and matches against BLOCKED_KEY_PATTERNS regex list.
        key_path = s_data.get("key", "")
        if ".." in key_path:
            return False, f"Invalid key path - contains path traversal: {key_path}"

        if key_path.startswith("\\\\"):
            return False, f"Invalid key path - starts with network path: {key_path}"

        # Iterate through each blocked pattern and reject the setting if
        # the key path matches any of them (case-insensitive).
        for pattern in self.BLOCKED_KEY_PATTERNS:
            if re.search(pattern, key_path, re.IGNORECASE):
                return False, f"Blocked registry path pattern: {pattern}"

        # Enforce maximum key path length of 512 characters.
        if len(key_path) > 512:
            return False, f"Key path too long: {len(key_path)} chars (max 512)"

        # value_name: The specific registry value name within the key.
        # Capped at 255 characters (Windows registry limit).
        value_name = s_data.get("value", "")
        if len(value_name) > 255:
            return False, f"Value name too long: {len(value_name)} chars (max 255)"

        # valid_types: The set of acceptable Windows registry value types.
        # REG_SZ = string, REG_DWORD = 32-bit int, REG_BINARY = binary blob,
        # REG_MULTI_SZ = multi-string, REG_EXPAND_SZ = expandable string,
        # REG_QWORD = 64-bit int.
        valid_types = [
            "REG_SZ",
            "REG_DWORD",
            "REG_BINARY",
            "REG_MULTI_SZ",
            "REG_EXPAND_SZ",
            "REG_QWORD",
        ]
        if s_data["type"] not in valid_types:
            return False, f"Invalid registry type: {s_data['type']}"

        # value: The default value for the setting (optional in JSON).
        # If present, validate that it matches the expected type constraints:
        #   - REG_DWORD must be a non-negative integer within 32-bit range.
        #   - REG_SZ / REG_EXPAND_SZ must be a string <= 32767 characters.
        value = s_data.get("default_value")
        if value is not None:
            if s_data["type"] == "REG_DWORD":
                if not isinstance(value, int) or value < 0 or value > 4294967295:
                    return False, f"Invalid DWORD value: {value}"
            elif s_data["type"] in ["REG_SZ", "REG_EXPAND_SZ"]:
                if not isinstance(value, str) or len(value) > 32767:
                    return False, f"Invalid string value length"

        return True, ""

    def _validate_category_data(self, cat_data: dict) -> tuple[bool, str]:
        """
        Validate category data structure.

        Args:
            cat_data: Category dictionary from JSON — contains "name" and
                      "settings" keys.

        Returns:
            Tuple of (is_valid, error_message) — True and empty string if
            valid, or False with a descriptive error message if invalid.
        """
        # Every category must have a "name" field for identification.
        if "name" not in cat_data:
            return False, "Category missing 'name' field"

        # Every category must have a "settings" field containing the list
        # of individual setting entries.
        if "settings" not in cat_data:
            return False, f"Category '{cat_data.get('name')}' missing 'settings' field"

        # The "settings" field must be a list, not a dict or other type.
        if not isinstance(cat_data["settings"], list):
            return False, f"Category '{cat_data.get('name')}' settings is not a list"

        # Limit to 100 settings per category to prevent memory exhaustion
        # from an abnormally large JSON payload.
        if len(cat_data["settings"]) > 100:
            return (
                False,
                f"Too many settings in category: {len(cat_data['settings'])} (max 100)",
            )

        return True, ""

    def load_settings(self):
        """Load settings from JSON file with comprehensive validation."""
        # Abort early if the settings file does not exist on disk.
        if not os.path.exists(self.resource_path):
            _safe_print(f"Settings resource not found: {self.resource_path}")
            return

        try:
            with open(self.resource_path, "r", encoding="utf-8") as f:
                # Read the entire file content, capped at 50 MB, to prevent
                # denial-of-service from excessively large files.
                content = f.read(50 * 1024 * 1024)  # 50 MB max read
                # Parse the JSON string into a Python data structure.
                data = json.loads(content)
        except json.JSONDecodeError as e:
            _safe_print(f"Invalid JSON in settings file: {e}")
            return
        except Exception as e:
            _safe_print(f"Error reading settings file: {e}")
            return

        # The top-level JSON structure must be a list of category objects.
        if not isinstance(data, list):
            _safe_print("Settings file must contain a list of categories")
            return

        # Cap total categories at 50 to prevent resource exhaustion.
        if len(data) > 50:
            _safe_print("Too many categories in settings file")
            return

        # Iterate over each category dictionary in the parsed JSON list.
        for cat_data in data:
            # Validate the category structure before processing its settings.
            valid, error = self._validate_category_data(cat_data)
            if not valid:
                _safe_print(f"Skipping invalid category: {error}")
                continue

            # cat_name: The human-readable category name from the JSON
            # (e.g., "System Appearance").
            cat_name = cat_data.get("name")

            # enum_cat: The corresponding SettingCategory enum value looked
            # up from CATEGORY_MAP; defaults to SettingCategory.SYSTEM for
            # any unrecognized category name.
            enum_cat = self.CATEGORY_MAP.get(cat_name, SettingCategory.SYSTEM)

            # Ensure the category list exists in the dictionary before appending.
            if enum_cat not in self.settings_by_category:
                self.settings_by_category[enum_cat] = []

            # settings_loaded: Counter tracking how many valid settings were
            # successfully loaded for the current category.
            settings_loaded = 0

            # Iterate over each setting dictionary within the category.
            for s_data in cat_data.get("settings", []):
                # Validate individual setting data before constructing the model.
                valid, error = self._validate_setting_data(s_data, cat_name)
                if not valid:
                    _safe_print(
                        f"Skipping setting '{s_data.get('name', 'unknown')}' in category '{cat_name}': {error}"
                    )
                    continue

                try:
                    # safe_id: A sanitized identifier derived from the setting
                    # name by replacing non-alphanumeric characters with
                    # underscores and lowercasing. Used as the setting's unique ID.
                    safe_id = re.sub(
                        r"[^a-z0-9_]", "_", s_data.get("name", "unknown").lower()
                    )

                    # Construct a RegistrySetting model object from the validated
                    # JSON data. Fields are truncated to their max allowed lengths.
                    setting = RegistrySetting(
                        id=safe_id,  # Sanitized unique ID
                        name=s_data.get("name", "Unknown Setting")[
                            :200
                        ],  # Display name (max 200 chars)
                        description=s_data.get("description", "")[
                            :500
                        ],  # User-facing description (max 500 chars)
                        category=enum_cat,  # Enum category this setting belongs to
                        setting_type=SettingType.REGISTRY,  # All loaded settings are registry-based
                        value=None,  # Actual value; read from registry at runtime
                        default_value=s_data.get(
                            "default_value"
                        ),  # Default value from JSON (optional)
                        hive=s_data[
                            "hive"
                        ],  # Registry hive root (e.g., HKEY_CURRENT_USER)
                        key_path=s_data.get("key", "").replace("\\\\", "\\")[
                            :512
                        ],  # Registry key path, normalized backslashes (max 512)
                        value_name=s_data.get("value", "")[
                            :255
                        ],  # Registry value name (max 255)
                        value_type=s_data[
                            "type"
                        ],  # Registry value type (e.g., REG_DWORD)
                        options=None,  # Deprecated options field, not populated here
                    )

                    # If the JSON provides a "values" field, attach it to the
                    # setting as enumerated options. Supports two formats:
                    #   1. A dict mapping keys to labels (e.g., {"0": "Left", "1": "Center"})
                    #   2. A comma-separated string (e.g., "0 = Left, 1 = Center")
                    if "values" in s_data:
                        if isinstance(s_data["values"], dict):
                            # Limit values dict to 50 entries to prevent abuse.
                            if len(s_data["values"]) <= 50:
                                setting.values = s_data["values"]
                        elif isinstance(s_data["values"], str):
                            # options: Dict built by splitting the string on
                            # commas, then splitting each pair on '='.
                            options = {}
                            for pair in s_data["values"].split(","):
                                pair = pair.strip()
                                if "=" in pair:
                                    key, val = pair.split("=", 1)
                                    options[key.strip()] = val.strip()
                            if len(options) <= 50:
                                setting.values = options

                    # Alternatively, if a "range" field is present, store it
                    # as the allowed values list and flag the setting as a
                    # range-based setting (e.g., slider min/max).
                    elif "range" in s_data:
                        if (
                            isinstance(s_data["range"], list)
                            and len(s_data["range"]) <= 100
                        ):
                            setting.values = s_data["range"]
                            setting.is_range = True  # Marks this setting as range-based

                    # If the JSON includes "option_hints" (a dict of value ->
                    # tooltip strings), attach them to the setting for UI display.
                    # Capped at 50 entries.
                    if "option_hints" in s_data:
                        if isinstance(s_data["option_hints"], dict):
                            if len(s_data["option_hints"]) <= 50:
                                setting.option_hints = s_data["option_hints"]

                    # Append the fully constructed setting to its category list.
                    self.settings_by_category[enum_cat].append(setting)
                    settings_loaded += 1

                except Exception as e:
                    _safe_print(f"Error loading setting {s_data.get('name')}: {e}")
                    continue

            # Warn if a category yielded zero valid settings after processing.
            if settings_loaded == 0:
                _safe_print(
                    f"Warning: No valid settings loaded for category '{cat_name}'"
                )

    def get_settings_for_category(
        self, category: SettingCategory
    ) -> List[RegistrySetting]:
        """
        Get all settings for a specific category.

        Args:
            category: The SettingCategory enum value to look up.

        Returns:
            A list of RegistrySetting objects for the requested category,
            or an empty list if no settings exist for that category.
        """
        return self.settings_by_category.get(category, [])

    def get_categories(self) -> List[SettingCategory]:
        """
        Get list of available categories.

        Returns:
            A list of SettingCategory enum keys that have at least one
            loaded setting, used by the UI to populate category tabs/lists.
        """
        return list(self.settings_by_category.keys())
