"""
Main window for WinSet application
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# Import managers
# Import managers
from src.storage.exporter import ProfileExporter
from src.storage.importer import ProfileImporter
from src.presets.preset_manager import PresetManager
from src.utils.backup_manager import BackupManager
from src.core.registry_handler import RegistryHandler
from src.core.powershell_handler import PowerShellHandler
from src.core.setting_loader import SettingLoader
from src.models.setting import RegistrySetting, SettingCategory, SettingType

class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("WinSet - Windows Configuration Toolkit")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set icon (if you create one later)
        # self.root.iconbitmap("assets/icon.ico")
        
        # Initialize Managers
        self.preset_manager = PresetManager()
        self.importer = ProfileImporter()
        self.exporter = ProfileExporter()
        self.backup_manager = BackupManager()
        self.registry_handler = RegistryHandler()
        self.powershell_handler = PowerShellHandler()
        self.setting_loader = SettingLoader()
        
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # Center window
        self.center_window()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Settings...", command=self.export_settings)
        file_menu.add_command(label="Import Settings...", command=self.import_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Presets menu
        presets_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Presets", menu=presets_menu)
        presets_menu.add_command(label="🎮 Gaming Mode", command=lambda: self.apply_preset("gaming"))
        presets_menu.add_command(label="💻 Developer Mode", command=lambda: self.apply_preset("developer"))
        presets_menu.add_command(label="🔒 Privacy Max", command=lambda: self.apply_preset("privacy"))
        presets_menu.add_command(label="⚡ Performance", command=lambda: self.apply_preset("performance"))
        presets_menu.add_command(label="🔋 Battery Saver", command=lambda: self.apply_preset("battery"))
        presets_menu.add_separator()
        presets_menu.add_command(label="Manage Presets...", command=self.manage_presets)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Backup Registry", command=self.backup_registry)
        tools_menu.add_command(label="System Restore Point", command=self.create_restore_point)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.open_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_docs)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def _create_toolbar(self):
        """Create toolbar with buttons"""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, padding=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Quick action buttons
        ttk.Button(toolbar, text="📦 EXPORT", command=self.export_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 IMPORT", command=self.import_settings).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="🎮 GAMING", command=lambda: self.apply_preset("gaming")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💻 DEV", command=lambda: self.apply_preset("developer")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔒 PRIVACY", command=lambda: self.apply_preset("privacy")).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="⚙️ MANUAL", command=self.open_manual).pack(side=tk.LEFT, padx=2)
        
    def _create_main_area(self):
        """Create main content area"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Welcome tab
        self.welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.welcome_frame, text="🏠 Welcome")
        self._create_welcome_tab()
        
        # Quick Export tab
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="📦 Quick Export")
        self._create_export_tab()
        
        # Presets tab
        self.presets_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.presets_frame, text="⚡ Presets")
        self._create_presets_tab()
        
        # Manual Config tab
        self.manual_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_frame, text="⚙️ Manual Config")
        self._create_manual_tab()
        
    def _create_welcome_tab(self):
        """Create welcome screen content"""
        # Welcome message
        welcome_label = ttk.Label(
            self.welcome_frame,
            text="Welcome to WinSet!",
            font=("Arial", 24, "bold")
        )
        welcome_label.pack(pady=30)
        
        # Description
        desc_text = """WinSet helps you manage all your Windows settings in one place.

• Export your current configuration to a file
• Import settings on a new PC with one click
• Apply optimized presets for gaming, development, privacy, and more
• Fine-tune individual settings with an easy-to-use interface

Get started by choosing an option below:"""
        
        desc_label = ttk.Label(self.welcome_frame, text=desc_text, justify=tk.CENTER)
        desc_label.pack(pady=20)
        
        # Quick action buttons
        button_frame = ttk.Frame(self.welcome_frame)
        button_frame.pack(pady=30)
        
        ttk.Button(
            button_frame,
            text="📦 Quick Export",
            command=self.export_settings,
            width=20
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="⚡ Browse Presets",
            command=lambda: self.notebook.select(self.presets_frame),
            width=20
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="⚙️ Manual Config",
            command=self.open_manual,
            width=20
        ).pack(side=tk.LEFT, padx=10)
        
        # System info
        info_frame = ttk.LabelFrame(self.welcome_frame, text="System Information", padding=10)
        info_frame.pack(fill=tk.X, padx=50, pady=20)
        
        # Get Windows version (simplified)
        import platform
        win_version = platform.platform()
        
        ttk.Label(info_frame, text=f"Windows: {win_version}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Python: {sys.version.split()[0]}").pack(anchor=tk.W)
        ttk.Label(info_frame, text="Status: Ready").pack(anchor=tk.W)
        
    def _create_export_tab(self):
        """Create export tab content"""
        ttk.Label(self.export_frame, text="Export Settings", font=("Arial", 16)).pack(pady=10)
        
        # Category selection
        categories_frame = ttk.LabelFrame(self.export_frame, text="Select Categories to Export", padding=10)
        categories_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Checkboxes for categories
        self.category_vars = {}
        
        for i, category in enumerate(self.setting_loader.get_categories()):
            cat_display = f"{category.value.upper().replace('_', ' ')}"
            var = tk.BooleanVar(value=True)
            self.category_vars[category] = var
            ttk.Checkbutton(categories_frame, text=cat_display, variable=var).grid(
                row=i//2, column=i%2, sticky=tk.W, padx=20, pady=5
            )
        
        # Buttons
        button_frame = ttk.Frame(self.export_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Select All", command=self.select_all_categories).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all_categories).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Selected", command=self.export_selected).pack(side=tk.LEFT, padx=20)
        
    def _create_presets_tab(self):
        """Create presets tab with cards"""
        # Title
        ttk.Label(self.presets_frame, text="One-Click Presets", font=("Arial", 16)).pack(pady=10)
        
        # Create canvas with scrollbar for presets
        canvas = tk.Canvas(self.presets_frame)
        scrollbar = ttk.Scrollbar(self.presets_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Preset definitions
        presets = [
            {
                "name": "🎮 Gaming Mode",
                "desc": "Maximize FPS and gaming performance",
                "features": "• Game Mode ON\n• Visual Effects OFF\n• GPU Priority ON\n• Background Apps OFF",
                "color": "#2E7D32"
            },
            {
                "name": "💻 Developer Mode",
                "desc": "Configure for software development",
                "features": "• File Extensions SHOW\n• Hidden Files SHOW\n• PowerShell Unrestricted\n• Developer Mode ON",
                "color": "#1565C0"
            },
            {
                "name": "🔒 Privacy Max",
                "desc": "Maximum privacy and security",
                "features": "• Telemetry OFF\n• Location OFF\n• Camera/Mic OFF\n• Advertising ID OFF",
                "color": "#C62828"
            },
            {
                "name": "⚡ Performance",
                "desc": "Optimize for speed",
                "features": "• Animations OFF\n• High Performance Power\n• Visual Effects OFF\n• Processor Scheduling",
                "color": "#F57C00"
            },
            {
                "name": "🔋 Battery Saver",
                "desc": "Extend laptop battery life",
                "features": "• Power Saving Mode\n• Screen Dimming\n• Aggressive Sleep\n• Background Apps OFF",
                "color": "#00796B"
            },
            {
                "name": "📺 Media Center",
                "desc": "Optimize for media playback",
                "features": "• Keep System Awake\n• Media Sharing ON\n• Display OFF Never\n• Audio Enhancements",
                "color": "#6A1B9A"
            }
        ]
        
        # Create preset cards
        for preset in presets:
            self._create_preset_card(scrollable_frame, preset)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
    def _create_preset_card(self, parent, preset):
        """Create a preset card"""
        card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=2, padding=10)
        card.pack(fill=tk.X, pady=5, padx=5)
        
        # Preset name
        name_label = ttk.Label(card, text=preset["name"], font=("Arial", 14, "bold"))
        name_label.pack(anchor=tk.W)
        
        # Description
        desc_label = ttk.Label(card, text=preset["desc"], foreground="gray")
        desc_label.pack(anchor=tk.W, pady=2)
        
        # Features
        features_label = ttk.Label(card, text=preset["features"], justify=tk.LEFT)
        features_label.pack(anchor=tk.W, pady=5)
        
        # Apply button
        btn = ttk.Button(
            card,
            text="APPLY PRESET",
            command=lambda p=preset["name"]: self.apply_preset(p)
        )
        btn.pack(anchor=tk.E)
        
    def _create_manual_tab(self):
        """Create manual configuration tab with categorization."""
        ttk.Label(self.manual_frame, text="Manual Configuration", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Search/Filter frame
        filter_frame = ttk.Frame(self.manual_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_manual_config())
        ttk.Entry(filter_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Main scrollable area
        container = ttk.Frame(self.manual_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.manual_canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.manual_canvas.yview)
        self.manual_scrollable_frame = ttk.Frame(self.manual_canvas)
        
        self.manual_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.manual_canvas.configure(scrollregion=self.manual_canvas.bbox("all"))
        )
        
        self.manual_canvas.create_window((0, 0), window=self.manual_scrollable_frame, anchor="nw")#, width=self.manual_canvas.winfo_width())
        self.manual_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.manual_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial population
        self.refresh_manual_config()

    def refresh_manual_config(self):
        """Populate or refresh the manual config list based on filter."""
        # Clear existing
        for widget in self.manual_scrollable_frame.winfo_children():
            widget.destroy()
            
        search_query = self.search_var.get().lower()
        
        # Store checkbox vars to track state
        self.manual_vars = {} 

        for category in self.setting_loader.get_categories():
            settings = self.setting_loader.get_settings_for_category(category)
            
            # Filter settings
            filtered_settings = [s for s in settings if search_query in s.name.lower() or search_query in (s.description or "").lower()]
            
            if not filtered_settings:
                continue
                
            # Category Header
            cat_frame = ttk.LabelFrame(self.manual_scrollable_frame, text=f"📂 {category.value.upper().replace('_', ' ')}", padding=5)
            cat_frame.pack(fill=tk.X, pady=10, padx=5)
            
            for setting in filtered_settings:
                s_frame = ttk.Frame(cat_frame)
                s_frame.pack(fill=tk.X, pady=2)
                
                # Check if it should be toggled on (live registry read)
                current_val = self.registry_handler.read_value(setting.hive, setting.key_path, setting.value_name)
                
                # Simplified toggle check
                is_on = False
                if setting.value_type == "REG_DWORD":
                    is_on = (current_val == 1)
                elif setting.value_type == "REG_SZ":
                    # Some strings are "1"/"0" or "Enabled"/"Disabled"
                    is_on = str(current_val).lower() in ["1", "enabled", "yes", "on"]
                
                var = tk.BooleanVar(value=is_on)
                self.manual_vars[setting.id] = (setting, var)
                
                def toggle_command(s=setting, v=var):
                    # Defaulting to 1/0 for most toggles
                    new_val = 1 if v.get() else 0
                    if s.value_type == "REG_SZ":
                        new_val = "1" if v.get() else "0"
                        
                    success = self.registry_handler.write_value(
                        s.hive, s.key_path, s.value_name, s.value_type, new_val
                    )
                    if success:
                        self.status_label.config(text=f"Updated: {s.name}")
                    else:
                        messagebox.showerror("Error", f"Failed to update {s.name}")
                        v.set(not v.get())
                
                check = ttk.Checkbutton(s_frame, text=setting.name, variable=var, command=toggle_command)
                check.pack(side=tk.LEFT)
                
                if setting.description:
                    help_label = ttk.Label(s_frame, text=" (?)", foreground="blue", cursor="hand2")
                    help_label.pack(side=tk.LEFT)
                    help_label.bind("<Button-1>", lambda e, s=setting: messagebox.showinfo(s.name, s.description))

    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=2)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready | Run as Administrator: Yes",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.version_label = ttk.Label(
            self.status_bar,
            text="v0.1.0",
            anchor=tk.E
        )
        self.version_label.pack(side=tk.RIGHT)
    
    # Command methods
    def export_settings(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Profile"
        )
        if not file_path:
            return
            
        settings_to_export = []
        # If we have manual settings toggled/indexed, use those. 
        # For now, let's export all settings that have been explicitly identified in manual_vars
        if hasattr(self, 'manual_vars'):
            for setting_id, (setting, var) in self.manual_vars.items():
                if var.get(): # If "on", export it
                    # Update setting value from live registry
                    current_val = self.registry_handler.read_value(setting.hive, setting.key_path, setting.value_name)
                    setting.value = current_val
                    settings_to_export.append(setting)

        if not settings_to_export:
            # Fallback to a default set if nothing is selected manually
            messagebox.showwarning("No Selection", "Please check at least one setting in 'Manual Config' to export.")
            return
        
        success = self.exporter.export_profile(settings_to_export, file_path, profile_name="WinSet Custom Export")
        if success:
            messagebox.showinfo("Export Successful", f"Profile successfully exported to:\n{file_path}")
        else:
            messagebox.showerror("Export Failed", "There was an error exporting the profile.")
        
    def import_settings(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Select Profile to Import"
        )
        if not file_path:
            return
            
        success, msg, profile = self.importer.load_profile(file_path)
        if not success:
            messagebox.showerror("Import Failed", msg)
            return
            
        if messagebox.askyesno("Confirm Import", f"Are you sure you want to apply settings from '{profile.name}'?"):
            self.backup_manager.create_restore_point(f"WinSet - Before Profile '{profile.name}'")
            results = self.importer.apply_profile(profile)
            
            success_count = sum(1 for v in results.values() if v)
            messagebox.showinfo(
                "Import Complete", 
                f"Successfully applied {success_count} settings from '{profile.name}'."
            )
        
    def apply_preset(self, preset_name):
        preset_id = preset_name.split(" ")[-1].lower() if " " in preset_name else preset_name.lower()
        if preset_id == "max": preset_id = "privacy"
        if preset_id == "mode": preset_id = preset_name.split(" ")[1].lower()
        if preset_name == "developer": preset_id = "developer"
        if preset_name == "gaming": preset_id = "gaming"
        if preset_name == "privacy": preset_id = "privacy"
        if preset_name == "performance": preset_id = "performance"
        if preset_name == "battery": preset_id = "battery"

        
        if messagebox.askyesno("Confirm Preset", f"Are you sure you want to apply the '{preset_name}' preset?"):
            self.backup_manager.create_restore_point(f"WinSet - Before {preset_name}")
            success, msg, results = self.preset_manager.apply_preset(preset_id)
            
            if success:
                success_count = sum(1 for v in results.values() if v)
                messagebox.showinfo("Preset Applied", f"Successfully applied {success_count} settings for '{preset_name}'.\n\nSome changes may require a restart to take full effect.")
            else:
                messagebox.showerror("Error", f"Failed to apply preset:\n{msg}")
        
    def manage_presets(self):
        messagebox.showinfo("Manage Presets", "Preset management coming soon!")
        
    def backup_registry(self):
        success = self.backup_manager.create_restore_point("WinSet Manual User Backup")
        if success:
            messagebox.showinfo("Backup Successful", "System Restore Point created successfully.")
        else:
            messagebox.showerror("Backup Failed", "Failed to create System Restore Point. Make sure you are running as Administrator and System Restore is enabled.")
        
    def create_restore_point(self):
        self.backup_registry()
        
    def open_settings(self):
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
        
    def open_manual(self):
        self.notebook.select(self.manual_frame)
        
    def open_docs(self):
        import webbrowser
        webbrowser.open("https://github.com/yourusername/WinSet/docs/USER_GUIDE.md")
        
    def check_updates(self):
        messagebox.showinfo("Updates", "You're running the latest version!")
        
    def show_about(self):
        about_text = """WinSet v0.1.0

Windows Configuration Toolkit

A complete solution for backing up, restoring, and optimizing Windows settings.

MIT License - Open Source

Created with ❤️ for the Windows community"""
        messagebox.showinfo("About WinSet", about_text)
        
    def select_all_categories(self):
        for var in self.category_vars.values():
            var.set(True)
            
    def clear_all_categories(self):
        for var in self.category_vars.values():
            var.set(False)
            
    def export_selected(self):
        """Export settings for selected categories."""
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        if not selected_categories:
            messagebox.showwarning("No Selection", "Please select at least one category to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Selected Categories"
        )
        if not file_path:
            return

        settings_to_export = []
        for category in selected_categories:
            cat_settings = self.setting_loader.get_settings_for_category(category)
            for setting in cat_settings:
                # Read live value
                current_val = self.registry_handler.read_value(setting.hive, setting.key_path, setting.value_name)
                setting.value = current_val
                settings_to_export.append(setting)
        
        success = self.exporter.export_profile(settings_to_export, file_path, profile_name="WinSet Category Export")
        if success:
            messagebox.showinfo("Export Successful", f"Exported {len(settings_to_export)} settings across {len(selected_categories)} categories.")
        else:
            messagebox.showerror("Export Failed", "There was an error exporting the profile.")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()