"""
Presets package for WinSet
==========================

Provides pre-built collections of tweaks ("presets") that users can browse and
apply in a single click.  Each preset groups related settings — for example
"Gaming Optimisation", "Privacy Hardening", or "Developer Workstation" — so
common configuration scenarios require zero manual setup.

Modules in this package typically expose ``Profile`` instances (from
``src.models``) ready to be applied or exported.

Note: This package does not export symbols at the package level; individual
preset modules should be imported directly (e.g.
``from src.presets.gaming import GAMING_PROFILE``).
"""
