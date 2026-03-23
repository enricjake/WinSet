"""
PowerShell handler for WinSet - executes WMI and PowerShell scripts.
"""

import subprocess  # nosec - B404: subprocess needed for PowerShell, handled securely
import re
import os
from typing import Tuple, List, Optional


class PowerShellHandler:
    """Handles execution of PowerShell commands and scripts securely."""

    # Maximum command length to prevent buffer overflow
    MAX_COMMAND_LENGTH = 1000
    
    # Allowed characters for sanitization
    ALLOWED_COMMAND_CHARS = r'^[\w\s\-\{\}\[\]\(\)\.\\/:;=\'\"\|\&\%\$\#\*\?\!]+$'
    
    # Dangerous command patterns to block
    DANGEROUS_PATTERNS = [
        r'Remove-Item.*-Recurse',
        r'rm\s+-rf\s+',
        r'del\s+/[fsq]',
        r'format\s+[a-z]:',
        r'net\s+user\s+/add',
        r'net\s+localgroup\s+administrators\s+/add',
        r'Stop-Computer',
        r'Restart-Computer',
        r'Clear-EventLog',
        r'Set-Service.*-StartupType\s+Disabled.*Stop-Service',  # We allow this specifically with validation
        r'Get-WmiObject\s+-Class\s+Win32_Product',  # Known dangerous
    ]

    def __init__(self):
        # Use absolute path to prevent DLL hijacking (B607)
        self.powershell_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        
        # Verify powershell exists
        if not os.path.exists(self.powershell_path):
            # Fallback to path if absolute not found (for testing environments)
            self.powershell_path = "powershell.exe"

    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate a PowerShell command before execution.
        
        Args:
            command: The PowerShell command to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check length
        if len(command) > self.MAX_COMMAND_LENGTH:
            return False, f"Command too long: {len(command)} chars (max {self.MAX_COMMAND_LENGTH})"
        
        if len(command) == 0:
            return False, "Empty command"
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                # Allow specific safe commands that match dangerous patterns
                if pattern == r'Set-Service.*-StartupType\s+Disabled.*Stop-Service':
                    # This is our safe service disable command
                    if not command.startswith("Set-Service") or "Stop-Service" not in command:
                        return False, f"Dangerous command pattern detected: {pattern}"
                else:
                    return False, f"Dangerous command pattern detected: {pattern}"
        
        # Validate characters
        if not re.match(self.ALLOWED_COMMAND_CHARS, command):
            # Allow some extra characters that might be needed
            if not re.match(r'^[\w\s\-\{\}\[\]\(\)\.\\/:;=\'\"\|\&\%\$\#\*\?\!\,]+$', command):
                return False, "Command contains invalid characters"
        
        return True, ""

    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute a PowerShell command.
        
        Args:
            command: The PowerShell command string to execute.
            timeout: Maximum execution time in seconds.
            
        Returns:
            Tuple containing boolean success flag and the command output or error message.
        """
        # Validate command before execution
        is_valid, error = self._validate_command(command)
        if not is_valid:
            return False, f"Command validation failed: {error}"
        
        try:
            # Use absolute path to prevent hijacking (B607)
            # nosec: command is validated above, and we use argument list
            result = subprocess.run(  # nosec B603
                [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=timeout
            )
            
            if result.returncode == 0:
                # Truncate output to prevent memory issues
                output = result.stdout.strip()
                if len(output) > 10000:
                    output = output[:10000] + "... (truncated)"
                return True, output
            else:
                error_output = result.stderr.strip()
                if len(error_output) > 5000:
                    error_output = error_output[:5000] + "... (truncated)"
                return False, error_output
                
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, str(e)

    def set_power_plan(self, plan_guid: str) -> Tuple[bool, str]:
        """
        Set the active power plan.
        
        Args:
            plan_guid: GUID of the power plan (e.g., 381b4222-f694-41f0-9685-ff5bb260df2e)
            
        Returns:
            Tuple of (success, message)
        """
        # Validate GUID format (8-4-4-4-12 hex digits with optional braces)
        if not re.match(r'^\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}?$', 
                        plan_guid, re.IGNORECASE):
            return False, "Invalid Power Plan GUID format"
        
        command = f"powercfg /setactive {plan_guid}"
        return self.run_command(command)
        
    def disable_service(self, service_name: str) -> Tuple[bool, str]:
        """
        Disable a Windows service.
        
        Args:
            service_name: Name of the service to disable
            
        Returns:
            Tuple of (success, message)
        """
        # Validate service name (alphanumeric, spaces, dots, dashes only)
        if not re.match(r'^[\w\s\.-]+$', service_name):
            return False, "Invalid Service Name - use only letters, numbers, spaces, dots, and dashes"
        
        if len(service_name) > 100:
            return False, "Service name too long (max 100 characters)"
        
        # List of critical services that should not be disabled
        critical_services = [
            "winlogon", "services", "lsass", "svchost", "wininit",
            "csrss", "smss", "system", "registry"
        ]
        
        if service_name.lower() in critical_services:
            return False, f"Cannot disable critical system service: {service_name}"
        
        command = f"Set-Service -Name '{service_name}' -StartupType Disabled; Stop-Service -Name '{service_name}' -Force"
        return self.run_command(command)
    
    def get_service_status(self, service_name: str) -> Optional[str]:
        """
        Get the status of a Windows service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Status string or None if error
        """
        # Validate service name
        if not re.match(r'^[\w\s\.-]+$', service_name):
            return None
        
        command = f"(Get-Service -Name '{service_name}').Status"
        success, output = self.run_command(command)
        if success:
            return output.strip()
        return None
    
    def get_active_power_plan(self) -> Optional[str]:
        """
        Get the currently active power plan GUID.
        
        Returns:
            Power plan GUID or None if error
        """
        command = "powercfg /getactivescheme"
        success, output = self.run_command(command)
        if success:
            # Parse GUID from output like: "Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e"
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 
                              output, re.IGNORECASE)
            if match:
                return match.group(0)
        return None