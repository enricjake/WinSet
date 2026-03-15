import os
import glob
from typing import List, Dict, Tuple
from src.storage.importer import ProfileImporter
from src.models.profile import Profile

class PresetManager:
    """Discovers, loads, and manages default configuration presets."""

    def __init__(self, presets_dir: str = None):
        """
        Initialize the preset manager.
        Args:
            presets_dir: Path to the directory containing .json preset files.
                         Defaults to the 'presets' folder in the project root.
        """
        if presets_dir is None:
            # Assume presets are loaded from a folder adjacent to main executable/script
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.presets_dir = os.path.join(base_dir, "presets")
        else:
            self.presets_dir = presets_dir

        self.importer = ProfileImporter()
        self.available_presets: Dict[str, str] = {} # Map 'name' -> 'filepath'
        self.refresh_presets()

    def refresh_presets(self):
        """Scans the presets directory for available JSON files."""
        self.available_presets.clear()
        
        if not os.path.exists(self.presets_dir):
            print(f"Presets directory not found: {self.presets_dir}")
            return

        json_files = glob.glob(os.path.join(self.presets_dir, "*.json"))
        
        for file_path in json_files:
            # Load the file just to extract its metadata name securely without applying it
            try:
                success, msg, profile = self.importer.load_profile(file_path)
                if success and profile:
                    # We store it by lowercase internal name for easier lookup
                    preset_id = os.path.basename(file_path).replace('.json', '').lower()
                    self.available_presets[preset_id] = file_path
            except Exception as e:
                print(f"Failed to parse preset file {file_path}: {e}")

    def get_preset_list(self) -> List[str]:
        """Returns a list of available preset identifiers."""
        return list(self.available_presets.keys())

    def load_preset(self, preset_id: str) -> Tuple[bool, str, Profile | None]:
        """Loads a specific preset profile into memory."""
        preset_id = preset_id.lower()
        if preset_id not in self.available_presets:
            return False, f"Preset '{preset_id}' not found.", None
            
        file_path = self.available_presets[preset_id]
        return self.importer.load_profile(file_path)

    def apply_preset(self, preset_id: str, safe_mode: bool = True) -> Tuple[bool, str, Dict[str, bool]]:
        """Directly loads and applies a preset to the system."""
        success, msg, profile = self.load_preset(preset_id)
        if not success:
            return False, msg, {}
            
        results = self.importer.apply_profile(profile, safe_mode=safe_mode)
        
        # Check if any settings applied successfully
        if any(results.values()):
            return True, f"Preset '{preset_id}' applied successfully.", results
        else:
            return False, f"Failed to apply settings from preset '{preset_id}'.", results
