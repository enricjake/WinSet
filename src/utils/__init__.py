"""
Utilities package for WinSet
============================

Shared helper functions and small classes used across the entire WinSet
codebase.  This package avoids circular dependencies by providing only pure
utility code with no imports from other WinSet packages.

Typical contents:
    - Logging configuration and formatters
    - Input/path validation helpers
    - Serialisation utilities (JSON/YAML helpers)
    - Platform-detection and OS-version checks
    - String formatting and UI-text helpers

Note: This package does not export symbols at the package level; individual
utility modules should be imported directly (e.g.
``from src.utils.validators import validate_registry_path``).
"""
