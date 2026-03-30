"""
Build script for WinSet — packages the app into a standalone Windows .exe
using PyInstaller.

Usage:
    python scripts/build_exe.py
"""

import subprocess  # For spawning the PyInstaller process as a child process
import sys  # For sys.executable (the current Python interpreter path) and sys.exit (clean exit with status codes)
import shutil  # For shutil.rmtree — recursively deletes directories (used to clean build artefacts)
import os  # For os.pathsep — the platform-specific path separator (';' on Windows, ':' on Unix)
from pathlib import (
    Path,
)  # For Path-based filesystem operations (resolve, exists, parent, / operator)
import importlib.util  # For importlib.util.find_spec — checks whether a module is installed without importing it


# Absolute path to the root of the WinSet repository.
# __file__ is the path of this script (scripts/build_exe.py).
# .resolve() normalises it to an absolute path with symlinks resolved.
# .parent gives the 'scripts' directory; .parent.parent gives the project root.
# All other paths in this file are derived from PROJECT_ROOT.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def clean_dist():
    """Remove previous build artefacts."""
    # Iterate over the two directories PyInstaller creates during a build:
    #   "dist"  — contains the final compiled executable(s)
    #   "build" — contains intermediate build files (work files, .spec cache, etc.)
    for folder in ("dist", "build"):
        # Construct the full path by joining the folder name onto PROJECT_ROOT.
        # The '/' operator on a Path object performs OS-aware path joining.
        path = PROJECT_ROOT / folder

        # Only attempt deletion if the folder actually exists from a prior build.
        if path.exists():
            try:
                # shutil.rmtree removes the directory tree recursively,
                # deleting all files and subdirectories within it.
                shutil.rmtree(path)
                print(f"Cleaned {folder}/")
            except PermissionError:
                # On Windows, a PermissionError occurs if the exe is still running
                # (the OS locks the file). Prompt the user to close it first.
                print(f"Error: Access denied while cleaning '{folder}'.")
                print("Please ensure 'WinSet.exe' is closed and try again.")
                # Exit with code 1 to signal failure to any calling script or CI pipeline.
                sys.exit(1)


def build():
    """Run PyInstaller to produce a single-file executable."""

    # --- Pre-flight check ---
    # Verify PyInstaller is installed before attempting to run it.
    # find_spec returns None if the module is not on sys.path, avoiding a
    # costly import and any side effects it might trigger.
    if importlib.util.find_spec("PyInstaller") is None:
        print("Error: PyInstaller module not found.")
        print("Please run: pip install pyinstaller")
        sys.exit(1)

    # --- Path definitions for PyInstaller inputs ---
    # main_script: the application's entry-point Python file.
    # PyInstaller analyses this file to discover all transitive imports.
    main_script = PROJECT_ROOT / "winset.py"

    # icon_path: the .ico file used as the Windows application icon for the exe.
    # Located under the docs/ directory in the repository.
    icon_path = PROJECT_ROOT / "docs" / "icon.ico"

    # presets_data_path: tells PyInstaller to bundle the 'presets' directory
    # into the frozen application. The format is "source;dest" on Windows or
    # "source:dest" on Unix. os.pathsep provides the correct separator for
    # the current platform.
    presets_data_path = f"{PROJECT_ROOT / 'presets'}{os.pathsep}presets"

    # resources_data_path: tells PyInstaller to bundle the 'src/resources'
    # directory (which contains settings/config resources for WinSet).
    # The destination inside the bundle is "src/resources".
    resources_data_path = (
        f"{PROJECT_ROOT / 'src' / 'resources'}{os.pathsep}src/resources"
    )

    # --- Assemble the PyInstaller command-line arguments ---
    # cmd is a list of strings that will be passed to subprocess.Popen.
    # Each element corresponds to one shell token (no shell=True needed).
    cmd = [
        sys.executable,  # The current Python interpreter (ensures we use the same env)
        "-m",
        "PyInstaller",  # Invoke PyInstaller as a module so we don't depend on PATH
        "--onefile",  # Produce a single self-extracting .exe instead of a folder of files
        "--windowed",  # Mark the exe as a GUI application (no console window pops up).
        # On Windows this sets the subsystem to IMAGE_SUBSYSTEM_WINDOWS_GUI.
        "--name",
        "WinSet",  # Base name for the output exe and the .spec file (WinSet.exe)
        "--icon",
        str(icon_path) if icon_path.exists() else "NONE",
        # Embed the icon in the exe. Falls back to "NONE" (no icon)
        # if the .ico file is missing, so the build doesn't fail.
        "--add-data",
        presets_data_path,
        # Include the presets folder as bundled data.
        # At runtime, PyInstaller extracts it to a temp dir accessible
        # via sys._MEIPASS / sys.executable path tricks.
        "--add-data",
        resources_data_path,
        # Include the settings resources folder as bundled data.
        str(main_script),  # The script PyInstaller should analyse and freeze.
    ]

    print("Running PyInstaller…")

    # --- Execute PyInstaller as a subprocess ---
    # cwd=PROJECT_ROOT ensures PyInstaller creates its 'dist' and 'build'
    # directories at the project root, keeping the output predictable.
    # We use Popen (not run) so we can handle KeyboardInterrupt cleanly.
    try:
        process = subprocess.Popen(cmd, cwd=PROJECT_ROOT)
        # .communicate() reads stdout/stderr and waits for the process to finish.
        # Passing no timeout means we wait indefinitely — PyInstaller builds
        # can take several minutes for large projects.
        stdout, stderr = process.communicate()
    except KeyboardInterrupt:
        # If the user presses Ctrl+C while PyInstaller is running, we need to
        # terminate the child process gracefully so it doesn't leave zombie
        # processes or locked files behind.
        print("\nBuild interrupted. Terminating PyInstaller…")
        process.terminate()  # Send SIGTERM (or TerminateProcess on Windows)
        try:
            # Give the process up to 5 seconds to exit gracefully.
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it still hasn't exited, force-kill it immediately.
            process.kill()
            process.wait()  # Reap the process to avoid a zombie
        print("Build cancelled.")
        sys.exit(1)

    # --- Check the exit code ---
    # A non-zero return code means PyInstaller encountered an error
    # (e.g. missing dependency, import analysis failure).
    if process.returncode != 0:
        print("Build failed.")
        # Propagate PyInstaller's exit code so CI systems can detect the failure.
        sys.exit(process.returncode)

    # Build succeeded — report the location of the output executable.
    # dist/WinSet.exe is the single-file bundle users can distribute.
    print(f"Build complete — output is in {PROJECT_ROOT / 'dist' / 'WinSet.exe'}")


# Entry point: executed only when this script is run directly,
# not when it is imported as a module by another script.
if __name__ == "__main__":
    clean_dist()  # Step 1 — wipe out any previous build outputs
    build()  # Step 2 — run PyInstaller to create the new exe
