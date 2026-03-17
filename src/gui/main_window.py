"""
Main window for WinSet application - Professional Configuration Tool Design
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import threading
import time

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
    """Main application window with professional configuration tool design"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("WinSet - Windows Configuration Toolkit")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)
        
        # Initialize Managers
        self.preset_manager = PresetManager()
        self.importer = ProfileImporter()
        self.exporter = ProfileExporter()
        self.backup_manager = BackupManager()
        self.registry_handler = RegistryHandler()
        self.powershell_handler = PowerShellHandler()
        self.setting_loader = SettingLoader()
        
        # UI State
        self.is_busy = False
        self.expanded_settings = {}  # Track which settings are expanded
        self.expanded_setting_id = None
        self.manual_row_widgets = {}
        
        self._setup_ui()
        self.center_window()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_ui(self):
        """Create main UI layout with professional styling"""
        # Use clam theme for better compatibility
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            try:
                style.theme_use('default')
            except:
                pass
        
        # Professional styling with proper contrast
        bg_color = "#ffffff"  # Clean white background
        fg_color = "#212529"  # Dark text
        accent_color = "#0066cc"  # Professional blue
        border_color = "#dee2e6"  # Light border

        # Store colors for use in other methods
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.accent_color = accent_color
        self.border_color = border_color
        
        # Configure styles - all text black for maximum readability
        # The 'clam' theme gives labels a gray default background; force it to the app surface.
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground="black", font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=bg_color, font=("Segoe UI", 18, "bold"), foreground="black")
        style.configure("Bold.TLabel", background=bg_color, font=("Segoe UI", 10, "bold"), foreground="black")
        style.configure("Setting.TLabel", background=bg_color, font=("Segoe UI", 11, "bold"), foreground="black")
        style.configure("Description.TLabel", background=bg_color, font=("Segoe UI", 9), foreground="black")
        
        style.configure("TButton", 
                       background="#ffffff", 
                       foreground="black", 
                       font=("Segoe UI", 9),
                       padding=8,
                       borderwidth=1,
                       relief="solid")
        style.map("TButton",
                 background=[("active", "#e9ecef"), ("pressed", accent_color)],
                 foreground=[("pressed", "white")])
        
        style.configure("Accent.TButton", 
                       background=accent_color, 
                       foreground="white", 
                       font=("Segoe UI", 9, "bold"),
                       padding=8,
                       borderwidth=0,
                       relief="flat")
        style.map("Accent.TButton",
                 background=[("active", "#0056b3"), ("pressed", "#004085")])
        
        style.configure("TCheckbutton", 
                       background=bg_color, 
                       foreground="black", 
                       font=("Segoe UI", 9))
        
        style.configure("TEntry", 
                       fieldbackground="white", 
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))

        style.configure(
            "TLabelframe",
            background=bg_color,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=bg_color,
            foreground="black",
            font=("Segoe UI", 9, "bold"),
        )
        
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#ffffff",
            foreground="black",
            padding=[15, 10],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        # Keep selected tab readable: black-on-light instead of white-on-blue.
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff"), ("active", "#ffffff")],
            foreground=[("selected", "black"), ("active", "black")],
        )
        
        style.configure(
            "TProgressbar",
            background=accent_color,
            troughcolor="#ffffff",
            borderwidth=0,
        )
        
        style.configure("TCombobox", 
                       fieldbackground="white",
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))
        
        style.configure("TScale", 
                       background=bg_color,
                       troughcolor="#ffffff",
                       borderwidth=1,
                       relief="solid")
        style.configure("Horizontal.TScale", background=bg_color)
        
        # Apply theme to root window
        self.root.configure(bg=bg_color)

        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.home_frame = ttk.Frame(self.notebook)
        self.presets_frame = ttk.Frame(self.notebook)
        self.manual_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.home_frame, text=" Home ")
        self.notebook.add(self.presets_frame, text=" Presets ")
        self.notebook.add(self.manual_frame, text=" Manual Configuration ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._create_home_tab()
        self._create_presets_tab()
        self._create_manual_tab()

        # Status bar at bottom
        self.status_frame = ttk.Frame(self.main_frame, relief=tk.SOLID, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        # Hidden by default

    def _create_home_tab(self):
        """Create home tab content"""
        container = ttk.Frame(self.home_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Welcome section
        welcome_frame = ttk.LabelFrame(container, text="Welcome", padding=20)
        welcome_frame.pack(fill=tk.X, pady=(0, 25))
        
        welcome_label = ttk.Label(welcome_frame, text="WinSet", style="Header.TLabel")
        welcome_label.pack(anchor="w", pady=(0, 10))
        
        desc_label = ttk.Label(welcome_frame, 
                             text="Windows Configuration Toolkit\nEasily backup, restore, and optimize your Windows experience.", 
                             font=("Segoe UI", 12))
        desc_label.pack(anchor="w", pady=(0, 15))
        
        # Quick actions
        actions_frame = ttk.LabelFrame(container, text="Quick Actions", padding=20)
        actions_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Action buttons in a grid
        ttk.Button(actions_frame, text="📤 Export Settings", command=self.export_settings, width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="📥 Import Settings", command=self.import_settings, width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="🔄 Create Restore Point", command=self.create_restore_point, width=20).pack(fill=tk.X, pady=(0, 10))
        
        # System info
        info_frame = ttk.LabelFrame(container, text="System Information", padding=20)
        info_frame.pack(fill=tk.X, pady=(0, 25))
        
        ttk.Label(info_frame, text="Ready to configure your Windows system with professional-grade tools.", 
                 font=("Segoe UI", 10)).pack(anchor="w")

    def _create_presets_tab(self):
        """Create presets tab content"""
        container = ttk.Frame(self.presets_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        ttk.Label(container, text="Configuration Presets", style="Header.TLabel").pack(anchor="w", pady=(0, 20))
        
        # Presets grid
        presets_frame = ttk.Frame(container)
        presets_frame.pack(fill=tk.BOTH, expand=True)
        
        presets = [
            {"id": "gaming", "title": "🎮 Gaming Mode", "desc": "Optimize system for gaming performance"},
            {"id": "developer", "title": "💻 Developer Mode", "desc": "Configure for development workflows"},
            {"id": "privacy", "title": "🔒 Privacy Max", "desc": "Maximum privacy and security settings"},
            {"id": "performance", "title": "⚡ Peak Performance", "desc": "Unlock full system performance"},
            {"id": "battery", "title": "🔋 Battery Saver", "desc": "Optimize for extended battery life"}
        ]
        
        for i, p in enumerate(presets):
            row = i // 2
            col = i % 2
            
            preset_card = ttk.LabelFrame(presets_frame, text="", padding=15, relief=tk.RIDGE, borderwidth=1)
            preset_card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            presets_frame.grid_columnconfigure(col, weight=1)
            
            ttk.Label(preset_card, text=p["title"], style="Bold.TLabel").pack(anchor="w", pady=(0, 5))
            ttk.Label(preset_card, text=p["desc"], style="Description.TLabel").pack(anchor="w", pady=(0, 10))
            ttk.Button(preset_card, text="Apply Preset", 
                      command=lambda pid=p["id"]: self.apply_preset(pid)).pack(fill=tk.X)

    def _create_manual_tab(self):
        """Create manual configuration tab"""
        container = ttk.Frame(self.manual_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Header with search
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Manual Configuration", style="Header.TLabel").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT)
        
        # Scrollable settings area
        scroll_frame = ttk.Frame(container)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.manual_canvas = tk.Canvas(scroll_frame, highlightthickness=0, bg=self.bg_color)
        manual_scroll = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.manual_canvas.yview)
        self.manual_scrollable = ttk.Frame(self.manual_canvas)

        self.manual_scrollable.bind("<Configure>", lambda e: self.manual_canvas.configure(scrollregion=self.manual_canvas.bbox("all")))
        self.manual_window_id = self.manual_canvas.create_window((0, 0), window=self.manual_scrollable, anchor="nw")
        self.manual_canvas.configure(yscrollcommand=manual_scroll.set)

        # Make the inner frame always match the canvas width (no wasted space)
        self.manual_canvas.bind(
            "<Configure>",
            lambda e: self.manual_canvas.itemconfigure(self.manual_window_id, width=e.width),
        )
        
        self.manual_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        manual_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self._bind_scroll_events()
        search_entry.bind("<KeyRelease>", self._on_search)

    def _bind_scroll_events(self):
        """Bind scroll events to work properly"""
        self.manual_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.manual_frame.bind("<MouseWheel>", self._on_mouse_wheel)
        self.manual_scrollable.bind("<MouseWheel>", self._on_mouse_wheel)
        self.notebook.bind("<MouseWheel>", self._on_global_mouse_wheel)
        self.main_frame.bind("<MouseWheel>", self._on_global_mouse_wheel)
        self.manual_canvas.bind("<Map>", self._rebind_scroll_events)

    def _rebind_scroll_events(self, event=None):
        """Rebind scroll events to include new widgets"""
        def bind_recursive(widget):
            widget.bind("<MouseWheel>", self._on_mouse_wheel)
            for child in widget.winfo_children():
                bind_recursive(child)
        
        bind_recursive(self.manual_scrollable)

    def _on_global_mouse_wheel(self, event):
        """Handle global mouse wheel events"""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Manual Configuration" in selected_tab:
            self._on_mouse_wheel(event)

    def _on_tab_changed(self, event):
        """Handle tab change events."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Manual Configuration" in selected_tab:
            self.refresh_manual_config()
            self.root.after(100, self._rebind_scroll_events)

    def _on_search(self, event):
        """Handle search box updates."""
        self.refresh_manual_config()

    def _on_mouse_wheel(self, event):
        """Handles mouse wheel scrolling for the manual config canvas."""
        if self.manual_canvas.winfo_exists():
            self.manual_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_manual_config(self):
        """Refresh the list of manual settings"""
        for widget in self.manual_scrollable.winfo_children():
            widget.destroy()
            
        search_query = self.search_var.get().lower()
        self.manual_vars = {}
        self.manual_row_widgets = {}

        for category in self.setting_loader.get_categories():
            settings = self.setting_loader.get_settings_for_category(category)
            filtered = [s for s in settings if search_query in s.name.lower() or search_query in (s.description or "").lower()]
            
            if not filtered: continue
                
            # Category header (flat, modern; avoids LabelFrame shading)
            category_container = ttk.Frame(self.manual_scrollable)
            category_container.pack(fill=tk.X, pady=(14, 6), padx=10)

            ttk.Label(
                category_container,
                text=category.value.replace("_", " ").title(),
                style="Bold.TLabel",
            ).pack(anchor="w")
            ttk.Separator(category_container, orient="horizontal").pack(fill=tk.X, pady=(6, 0))

            category_frame = ttk.Frame(self.manual_scrollable)
            category_frame.pack(fill=tk.X, pady=(6, 0), padx=10)

            for setting in filtered:
                self._create_setting_row(category_frame, setting)
        
        self.root.after(50, self._rebind_scroll_events)

    def _create_setting_row(self, parent, setting):
        """Create a row for a setting with professional controls"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=4)
        
        # Check current state
        current_val = self.registry_handler.read_value(setting.hive, setting.key_path, setting.value_name)
        
        # Setting name (clickable)
        setting_id = f"setting_{setting.id}"
        is_expanded = (self.expanded_setting_id == setting_id)
        
        # Create expandable setting frame
        setting_frame = ttk.Frame(row_frame)
        setting_frame.pack(fill=tk.X)
        
        # Header with triangle and name
        header_frame = ttk.Frame(setting_frame)
        header_frame.pack(fill=tk.X)
        
        # Triangle indicator
        triangle = "▼" if is_expanded else "▶"
        triangle_label = ttk.Label(header_frame, text=triangle, font=("Segoe UI", 10), foreground=self.accent_color)
        triangle_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Setting name
        name_label = ttk.Label(header_frame, text=setting.name, style="Setting.TLabel", 
                            cursor="hand2")
        name_label.pack(side=tk.LEFT)
        
        # Bind click event to toggle expansion
        for widget in [triangle_label, name_label]:
            widget.bind("<Button-1>", lambda e, sid=setting_id: self._toggle_setting_expansion(sid))
        
        # Options frame (initially hidden)
        options_frame = ttk.Frame(setting_frame)
        if is_expanded:
            options_frame.pack(fill=tk.X, pady=(12, 0), padx=(25, 0))
        
        # Parse setting options
        options = self._parse_setting_options(setting, current_val)
        
        buttons = []
        slider_var = None
        if self._should_use_slider(setting, options):
            slider_var = self._create_slider_control(options_frame, setting, current_val, options, setting_id)
        elif len(options) > 2:
            buttons = self._create_button_controls(options_frame, setting, current_val, options, setting_id)
        else:
            buttons = self._create_simple_controls(options_frame, setting, current_val, options, setting_id)

        if setting.description:
            ttk.Label(options_frame, text=setting.description, style="Description.TLabel", wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(8, 0))

        self.manual_row_widgets[setting_id] = {
            "setting": setting,
            "triangle": triangle_label,
            "options_frame": options_frame,
            "buttons": buttons,
            "slider_var": slider_var,
        }

    def _should_use_slider(self, setting, options):
        """Determine if setting should use slider control"""
        # Only use sliders for real numeric ranges (e.g. "1-20") or known range settings.
        values_str = getattr(setting, "values", None)
        if isinstance(values_str, str):
            # Match things like "1-20" or "0 - 100"
            import re
            if re.search(r"\b\d+\s*-\s*\d+\b", values_str):
                return True

        # Known registry-backed ranges
        if str(setting.value_name).lower() in {"mousesensitivity"}:
            return True

        return False

    def _create_slider_control(self, parent, setting, current_val, options, setting_id):
        """Create slider control for range-based settings"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Adjust:", style="Description.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        # Determine slider range from setting.values when possible
        import re
        values_str = str(getattr(setting, "values", "") or "")
        m = re.search(r"\b(\d+)\s*-\s*(\d+)\b", values_str)
        if m:
            from_val = int(m.group(1))
            to_val = int(m.group(2))
        else:
            from_val = 0
            to_val = 100

        # Create slider
        try:
            current_num = float(current_val) if current_val is not None else float(from_val)
        except (TypeError, ValueError):
            current_num = float(from_val)

        slider_var = tk.DoubleVar(value=current_num)
        slider = ttk.Scale(
            control_frame,
            from_=from_val,
            to=to_val,
            variable=slider_var,
            orient=tk.HORIZONTAL,
            length=300,
        )

        if from_val == 1 and to_val == 20 and str(setting.value_name).lower() in {"mousesensitivity"}:
            ttk.Label(control_frame, text="(Low ← → High)", style="Description.TLabel").pack(side=tk.LEFT, padx=(10, 0))
        
        slider.pack(side=tk.LEFT, padx=(0, 10))
        
        slider.bind("<ButtonRelease-1>", lambda e, sid=setting_id, s=setting, v=slider_var: self._apply_slider_value(sid, s, v))

        return slider_var

    def _create_button_controls(self, parent, setting, current_val, options, setting_id):
        """Create button controls for multi-option settings"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Select:", style="Description.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(side=tk.LEFT)
        
        buttons = []
        for option_name, option_value in options.items():
            is_selected = str(current_val) == str(option_value)
            
            option_btn = ttk.Button(buttons_frame, text=option_name,
                                style=("Accent.TButton" if is_selected else "TButton"),
                                width=12)
            option_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            option_btn.bind("<Button-1>", lambda e, sid=setting_id, s=setting, v=option_value: self._apply_setting_value(sid, s, v))
            buttons.append((option_btn, option_value))

        return buttons

    def _create_simple_controls(self, parent, setting, current_val, options, setting_id):
        """Create simple controls for basic settings"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        buttons = []
        for option_name, option_value in options.items():
            is_selected = str(current_val) == str(option_value)
            
            option_btn = ttk.Button(control_frame, text=option_name,
                                style=("Accent.TButton" if is_selected else "TButton"),
                                width=15)
            option_btn.pack(side=tk.LEFT, padx=(0, 8))
            
            option_btn.bind("<Button-1>", lambda e, sid=setting_id, s=setting, v=option_value: self._apply_setting_value(sid, s, v))
            buttons.append((option_btn, option_value))

        return buttons

    def _parse_setting_options(self, setting, current_val):
        """Parse setting options from values field or create default options"""
        options = {}
        
        # Check if setting has explicit options defined
        if hasattr(setting, 'options') and setting.options:
            return setting.options
        
        # Parse from values field in settings.json
        if hasattr(setting, 'values') and setting.values:
            values_str = str(setting.values)

            # If it's a numeric range (e.g. "1-20"), it's a slider setting, not discrete options.
            import re
            if re.search(r"\b\d+\s*-\s*\d+\b", values_str):
                return {}

            # Split on common separators.
            # Example formats:
            # - "0 = Left, 1 = Center"
            # - "0 = Off; 1 = On"
            # - "0=Slow,1=Medium,2=Fast"
            parts_list = re.split(r"[,;]", values_str)
            for option in parts_list:
                if '=' not in option:
                    continue
                left, right = option.split('=', 1)
                value = left.strip()
                name = right.strip()
                if value and name:
                    options[name] = value
        else:
            # Default boolean options
            if setting.value_type == "REG_DWORD":
                options = {
                    "Enable": "1",
                    "Disable": "0"
                }
            elif setting.value_type == "REG_SZ":
                options = {
                    "Enable": "1",
                    "Disable": "0"
                }
        
        return options

    def _toggle_setting_expansion(self, setting_id):
        """Toggle expansion state of a setting"""
        if self.expanded_setting_id == setting_id:
            self._collapse_setting_row(setting_id)
            self.expanded_setting_id = None
            return

        if self.expanded_setting_id is not None:
            self._collapse_setting_row(self.expanded_setting_id)

        self.expanded_setting_id = setting_id
        self._expand_setting_row(setting_id)

    def _collapse_setting_row(self, setting_id):
        row = self.manual_row_widgets.get(setting_id)
        if not row:
            return
        row["triangle"].config(text="▶")
        row["options_frame"].pack_forget()

    def _expand_setting_row(self, setting_id):
        row = self.manual_row_widgets.get(setting_id)
        if not row:
            return
        row["triangle"].config(text="▼")
        row["options_frame"].pack(fill=tk.X, pady=(12, 0), padx=(25, 0))

    def _apply_slider_value(self, setting_id, setting, var):
        """Apply slider value to setting"""
        new_val_num = int(round(var.get()))

        if setting.value_type == "REG_SZ":
            new_val = str(new_val_num)
        elif setting.value_type == "REG_DWORD":
            new_val = int(new_val_num)
        else:
            new_val = new_val_num
        
        success = self.registry_handler.write_value(setting.hive, setting.key_path, setting.value_name, setting.value_type, new_val)
        if success:
            self.update_status(f"Updated: {setting.name}")
            self._update_row_selection_state(setting_id)
        else:
            messagebox.showerror("Error", f"Failed to update {setting.name}")

    def _apply_setting_value(self, setting_id, setting, value):
        """Apply a specific value to a setting"""
        # Convert value based on setting type
        if setting.value_type == "REG_SZ":
            new_val = str(value)
        elif setting.value_type == "REG_DWORD":
            new_val = int(value)
        else:
            new_val = value
        
        success = self.registry_handler.write_value(setting.hive, setting.key_path, setting.value_name, setting.value_type, new_val)
        if success:
            self.update_status(f"Updated: {setting.name}")
            self._update_row_selection_state(setting_id)
        else:
            messagebox.showerror("Error", f"Failed to update {setting.name}")

    def _update_row_selection_state(self, setting_id):
        row = self.manual_row_widgets.get(setting_id)
        if not row:
            return

        setting = row.get("setting")
        if not setting:
            return

        current_val = self.registry_handler.read_value(setting.hive, setting.key_path, setting.value_name)
        for btn, opt_val in row.get("buttons", []) or []:
            is_selected = str(current_val) == str(opt_val)
            btn.configure(style=("Accent.TButton" if is_selected else "TButton"))

    def update_status(self, text, progress=None):
        self.status_label.config(text=text)
        if progress is not None:
            self.progress_bar.pack(side=tk.RIGHT, padx=15, pady=8)
            self.progress_bar.config(value=progress * 100)
        else:
            self.progress_bar.pack_forget()
        self.root.update_idletasks()

    def run_async(self, func, *args, **kwargs):
        if self.is_busy: return
        self.is_busy = True
        
        def wrapper():
            try:
                func(*args, **kwargs)
            finally:
                self.is_busy = False
                self.update_status("Ready")
                
        threading.Thread(target=wrapper, daemon=True).start()

    def export_settings(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        def task():
            self.update_status("Preparing export...", 0.1)
            settings = []
            all_cats = self.setting_loader.get_categories()
            for i, cat in enumerate(all_cats):
                self.update_status(f"Reading {cat.value}...", 0.1 + (0.7 * (i/len(all_cats))))
                for s in self.setting_loader.get_settings_for_category(cat):
                    val = self.registry_handler.read_value(s.hive, s.key_path, s.value_name)
                    if val is not None:
                        s.value = val
                        settings.append(s)
            
            self.update_status("Saving...", 0.9)
            if self.exporter.export_profile(settings, file_path, "WinSet Export"):
                self.update_status("Export Complete", 1.0)
                messagebox.showinfo("Success", f"Profile saved to {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Export failed.")
        self.run_async(task)

    def import_settings(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        success, msg, profile = self.importer.load_profile(file_path)
        if not success:
            messagebox.showerror("Import Error", msg)
            return
            
        if messagebox.askyesno("Confirm", f"Apply '{profile.name}'?"):
            def task():
                self.update_status("Creating Restore Point...", 0.2)
                self.backup_manager.create_restore_point(f"WinSet Before Import: {profile.name}")
                self.update_status("Applying...", 0.5)
                results = self.importer.apply_profile(profile, safe_mode=False)
                self.update_status("Import Complete", 1.0)
                messagebox.showinfo("Success", f"Applied {sum(1 for v in results.values() if v)} settings.")
            self.run_async(task)

    def apply_preset(self, preset_id):
        if messagebox.askyesno("Confirm", f"Apply {preset_id.title()} preset?"):
            def task():
                self.update_status("Creating Restore Point...", 0.1)
                self.backup_manager.create_restore_point(f"WinSet Before Preset: {preset_id}")
                self.update_status(f"Applying {preset_id}...", 0.4)
                success, msg, results = self.preset_manager.apply_preset(preset_id)
                if success:
                    self.update_status("Preset Applied", 1.0)
                    messagebox.showinfo("Success", f"Applied {sum(1 for v in results.values() if v)} settings.")
                else:
                    messagebox.showerror("Error", msg)
            self.run_async(task)

    def create_restore_point(self):
        def task():
            self.update_status("Creating Restore Point...", 0.5)
            success = self.backup_manager.create_restore_point("WinSet Manual Restore Point")
            if success:
                self.update_status("Restore Point Created", 1.0)
                messagebox.showinfo("Success", "System restore point created successfully.")
            else:
                messagebox.showerror("Error", "Failed to create restore point.")
        self.run_async(task)
