"""
Storage package for WinSet
==========================

Implements the persistence layer responsible for saving, loading, importing, and
exporting WinSet profiles and application configuration.  This includes:

    - Local file-system storage of profiles as JSON files
    - Import/export of ``.winset`` profile bundles
    - Application settings persistence (theme, last-used profile, window state)
    - Backup and restore of original registry values before applying tweaks

Modules in this package handle all I/O so that the rest of the application
remains decoupled from the on-disk format.

Note: This package does not export symbols at the package level; individual
storage modules should be imported directly (e.g.
``from src.storage.profile_store import ProfileStore``).
"""
