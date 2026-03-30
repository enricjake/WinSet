"""
WinSet version information.
"""

# Semantic version string for the WinSet application.
# Format follows Semantic Versioning (semver): MAJOR.MINOR.PATCH-PRERELEASE
#   - MAJOR (0): Incremented for incompatible API or feature changes. Currently 0, indicating the project is in pre-release and has not yet reached a stable public API.
#   - MINOR (0): Incremented for new functionality added in a backwards-compatible manner. Currently 0, meaning no feature-level releases have been cut yet.
#   - PATCH (4): Incremented for backwards-compatible bug fixes or minor improvements.
#   - PRERELEASE (-alpha): Denotes a pre-release identifier indicating the software is still in early development/testing and not considered production-ready.
# This value is used throughout WinSet for display in the UI, logging, update checks,
# and to ensure configuration compatibility across tool versions.
VERSION = "0.0.4-alpha"
