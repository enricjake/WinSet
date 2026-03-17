import tkinter as tk
from unittest.mock import Mock, patch
import pytest
from src.gui.main_window import MainWindow

@pytest.fixture
def app():
    """Fixture to create a MainWindow instance for testing."""
    root = tk.Tk()
    # Prevent the window from showing up during tests
    root.withdraw()
    app = MainWindow(root)
    yield app
    # Clean up after tests
    root.destroy()

def test_manual_tab_refresh(app):
    """Test that refresh_manual_config is called when the manual tab is selected."""
    with patch.object(app, 'refresh_manual_config', wraps=app.refresh_manual_config) as mock_refresh:
        # Simulate selecting the "Manual Config" tab
        # The tab text is " ⚙️ Manual Config "
        app.notebook.select(2)
        app.notebook.event_generate("<<NotebookTabChanged>>")
        
        # Check if refresh_manual_config was called
        mock_refresh.assert_called_once()
