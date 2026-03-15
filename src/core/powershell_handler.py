"""
PowerShell handler for WinSet - executes WMI and PowerShell scripts.
"""

import subprocess
from typing import Tuple

class PowerShellHandler:
    """Handles execution of PowerShell commands and scripts."""

    def run_command(self, command: str) -> Tuple[bool, str]:
        """
        Execute a PowerShell command.
        
        Args:
            command: The PowerShell command string to execute.
            
        Returns:
            Tuple containing boolean success flag and the command output or error message.
        """
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def set_power_plan(self, plan_guid: str) -> Tuple[bool, str]:
        """
        Set the active power plan.
        
        Args:
            plan_guid: The GUID of the power plan.
            
        Returns:
            Tuple containing boolean success flag and output message.
        """
        command = f"powercfg /setactive {plan_guid}"
        return self.run_command(command)
        
    def disable_service(self, service_name: str) -> Tuple[bool, str]:
        """
        Disable a Windows service.
        """
        command = f"Set-Service -Name '{service_name}' -StartupType Disabled; Stop-Service -Name '{service_name}' -Force"
        return self.run_command(command)
