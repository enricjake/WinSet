import ctypes
import subprocess
import os
import sys

class BackupManager:
    """Manages Windows System Restore points for safe application rollbacks."""

    @staticmethod
    def is_admin() -> bool:
        """Check if the script is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def create_restore_point(self, description: str = "WinSet Configuration Backup") -> bool:
        """
        Creates a Windows System Restore point.
        Requires Administrator privileges.
        """
        if not self.is_admin():
            print("Cannot create restore point: Administrator privileges required.")
            return False

        try:
            # We use PowerShell to invoke WMI creation of a restore point
            # 0 = Application install
            # 100 = Begin system change
            ps_script = f"""
            Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
            """
            
            # Execute the PowerShell command
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                print(f"Successfully created system restore point: {description}")
                return True
            else:
                print(f"Failed to create restore point. Details: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"Exception during restore point creation: {e}")
            return False
