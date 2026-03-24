import codecs

# Read the file
with codecs.open('src/gui/main_window.py', 'r', 'utf-8') as f:
    content = f.read()

# The current state shows:
# - _create_home_tab was removed completely  
# - The calls to _create_*_tab() were removed

# We need to add back:
# 1. The method calls in _setup_ui
# 2. The _create_home_tab method definition

# First, add the method calls in _setup_ui
old_section = '''        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)



        # Status bar removed

    def _create_presets_tab(self):'''

new_section = '''        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._create_home_tab()
        self._create_presets_tab()
        self._create_manual_tab()
        self._create_history_tab()

    def _create_home_tab(self):
        """Create home tab content with scrolling support"""
        container = ttk.Frame(self.home_frame)
        container.pack(fill=tk.BOTH, expand=True)

        # Scrollable content area
        scroll_frame = ttk.Frame(container)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.home_canvas = tk.Canvas(scroll_frame, highlightthickness=0, bg=self.bg_color)
        home_scroll = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.home_canvas.yview)
        self.home_scrollable = ttk.Frame(self.home_canvas)

        self.home_scrollable.bind("<Configure>", lambda e: self.home_canvas.configure(scrollregion=self.home_canvas.bbox("all")))
        self.home_window_id = self.home_canvas.create_window((0, 0), window=self.home_scrollable, anchor="nw")
        self.home_canvas.configure(yscrollcommand=home_scroll.set)

        self.home_canvas.bind(
            "<Configure>",
            lambda e: self.home_canvas.itemconfigure(self.home_window_id, width=e.width),
        )
        
        self.home_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        home_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind scroll events FIRST
        self._bind_home_scroll_events()
        
        # Content
        welcome_frame = ttk.LabelFrame(self.home_scrollable, text="Welcome", padding=20)
        welcome_frame.pack(fill=tk.X, padx=25, pady=(10, 15))
        
        welcome_label = ttk.Label(welcome_frame, text="WinSet", style="Header.TLabel")
        welcome_label.pack(anchor="w", pady=(0, 10))
        
        desc_label = ttk.Label(welcome_frame, 
                            text="Windows Configuration Toolkit\\nEasily backup, restore, and optimize your Windows experience.", 
                            font=("Segoe UI", 12))
        desc_label.pack(anchor="w", pady=(0, 15))
        
        actions_frame = ttk.LabelFrame(self.home_scrollable, text="Quick Actions", padding=20)
        actions_frame.pack(fill=tk.X, padx=25, pady=(0, 15))
        
        ttk.Button(actions_frame, text="Export Settings", command=self.export_settings, width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="Import Settings", command=self.import_settings, width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="Create Restore Point", command=self.create_restore_point, width=20).pack(fill=tk.X, pady=(0, 10))
        
        tools_frame = ttk.LabelFrame(self.home_scrollable, text="System Tools", padding=20)
        tools_frame.pack(fill=tk.X, padx=25, pady=(0, 25))
        
        ttk.Button(tools_frame, text="Control Panel", command=lambda: self.open_system_tool("control"), width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(tools_frame, text="Services", command=lambda: self.open_system_tool("services.msc"), width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(tools_frame, text="MSConfig", command=lambda: self.open_system_tool("msconfig.exe")).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(tools_frame, text="Task Manager", command=lambda: self.open_system_tool("taskmgr"), width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(tools_frame, text="Programs & Features", command=lambda: self.open_system_tool("appwiz.cpl"), width=20).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(tools_frame, text="Network Settings", command=lambda: self.open_system_tool("ncpa.cpl"), width=20).pack(fill=tk.X, pady=(0, 10))

    def _create_presets_tab(self):'''

content = content.replace(old_section, new_section)

# Write back
with codecs.open('src/gui/main_window.py', 'w', 'utf-8') as f:
    f.write(content)

print("Fixed - added method calls and _create_home_tab method")
