#!/usr/bin/env python3
"""
Test script to verify icon loading works correctly
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

def test_icon_loading():
    """Test that icon loading works"""
    print("Testing icon loading...")

    # Create root window
    root = tk.Tk()
    root.title("Icon Test")

    # Try to load our icon
    icon_path = os.path.join(os.path.dirname(__file__), "docs", "icon.ico")
    print(f"Looking for icon at: {icon_path}")
    print(f"Icon exists: {os.path.exists(icon_path)}")

    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
            print("Successfully set icon using iconbitmap()")
        except Exception as e:
            print(f"Failed to set icon with iconbitmap(): {e}")
    else:
        print("Icon file not found!")

    # Show window briefly
    root.geometry("300x200")
    label = tk.Label(root, text="Icon Test Window\nCheck taskbar for icon")
    label.pack(expand=True)

    def on_close():
        print("Window closed")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(3000, on_close)  # Auto-close after 3 seconds

    root.mainloop()
    print("Test completed")

if __name__ == "__main__":
    test_icon_loading()
