"""
Models package for WinSet
=========================

Defines the data models that represent every configurable setting, tweak, and
profile in WinSet.  All models are implemented as Python dataclasses for
immutability-friendly, type-safe, and serialisable representations.

Exports:
    Setting         -- Abstract base dataclass for all settings; defines the
                       common interface (validate, apply, export).
    RegistrySetting -- Concrete subclass for Windows Registry-based tweaks;
                       holds the target hive, key path, value name, and
                       expected value.
    SettingType     -- Enum classifying how a setting is applied at the OS
                       level (registry edit, file modification, system call,
                       power-plan change).
    SettingCategory -- Enum grouping settings by user-facing area (appearance,
                       privacy, taskbar, performance, etc.) for UI organisation.
    Profile         -- Top-level container that groups related settings into a
                       named, versioned, exportable unit of Windows
                       configuration.
"""

# --- Setting models (from models/setting.py) ---
# Setting:          Base dataclass every tweak type inherits from.
# RegistrySetting:  Registry-specific tweak with hive/key/value fields.
# SettingType:      Enum — REGISTRY, FILE, SYSTEM_CALL, POWER_PLAN, etc.
# SettingCategory:  Enum — APPEARANCE, PRIVACY, TASKBAR, PERFORMANCE, etc.
from .setting import Setting, RegistrySetting, SettingType, SettingCategory

# --- Profile model (from models/profile.py) ---
# Profile: Named collection of Setting objects with metadata (author, version,
# checksum, creation date) and methods for serialisation and integrity checks.
from .profile import Profile

# Explicit public API consumed by the rest of the codebase.
__all__ = ["Setting", "RegistrySetting", "SettingType", "SettingCategory", "Profile"]
