"""
Core package for WinSet
=======================

Provides the low-level system interaction layer. This package is responsible
for all direct communication with the Windows operating system, most notably
reading from and writing to the Windows Registry via the ``winreg`` API.

Exports:
    RegistryHandler -- Thread-safe wrapper around ``winreg`` that maps
        human-readable hive names (e.g. "HKCU") to their numeric constants,
        enforces path-validation rules, and provides context-manager support
        for safe key opening/closing.
"""

# RegistryHandler: the central class for all Windows Registry operations in
# WinSet.  It handles opening/closing keys, reading values, writing/deleting
# values, and enumerating sub-keys — all with built-in validation and logging.
from .registry_handler import RegistryHandler

# Explicit public API so ``from src.core import *`` only exposes RegistryHandler.
__all__ = ["RegistryHandler"]
