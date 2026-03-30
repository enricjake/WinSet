"""
WinSet - Windows Configuration Toolkit
=======================================

Root package for the WinSet application. WinSet is a Python-based tool for
managing, applying, importing, and exporting Windows configuration settings
(referred to as "tweaks"). It provides a GUI-driven interface backed by a
type-safe data model and direct Windows Registry access.

Subpackages:
    core      - Low-level system interaction (e.g. registry read/write).
    gui       - User-facing interface built with CustomTkinter.
    models    - Data models for settings, profiles, and enums.
    presets   - Pre-built tweak collections for common use-cases.
    storage   - Persistence layer for saving/loading profiles and configs.
    utils     - Shared helper functions (validation, logging, serialization).
    resources - Bundled assets (icons, images, UI themes).

The package also exposes ``VERSION`` from ``version.py`` for release tracking.
"""

# Version string (e.g. "0.0.4-alpha") used for display, update checks, and
# config-compatibility assertions across the application.
from .version import VERSION

# Public API — consumers can do ``from src import VERSION``.
__all__ = ["VERSION"]
