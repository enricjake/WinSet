"""
HistoryManager for WinSet - logs all setting changes to a persistent database.
"""

import sqlite3  # Used to interface with the local SQLite database that stores change history
import os  # Used to resolve file system paths (e.g., LOCALAPPDATA) and check file existence
import threading  # Provides thread-safe locking so multiple threads can safely read/write the DB
from datetime import (
    datetime,
    timedelta,
)  # datetime for timestamps; timedelta for computing date offsets during pruning
from typing import (
    List,
    Tuple,
    Any,
    Optional,
    Dict,
)  # Type hints for clearer function signatures


class HistoryManager:
    """Handles logging and retrieving setting changes from a local SQLite DB."""

    # Maximum number of history entries to keep in the database. When the row count
    # exceeds this value, the oldest entries are pruned. This prevents the database
    # from growing indefinitely on machines that make frequent Registry changes.
    MAX_HISTORY_ENTRIES = 10000

    # Default number of days to retain history entries. Entries older than this are
    # removed when prune_old_history() is called without an explicit days_to_keep value.
    DEFAULT_RETENTION_DAYS = 90

    def __init__(self, db_path: Optional[str] = None):
        # db_path: Optional override for the database file location. When None (the
        #   typical case), the DB is stored under %LOCALAPPDATA%/WinSet/history.db so
        #   that each Windows user gets their own history. Passing a custom path is
        #   useful for unit tests or portable deployments.
        if db_path is None:
            # Resolve the user's LOCALAPPDATA folder (e.g., C:\Users\<user>\AppData\Local)
            app_data_path = os.getenv("LOCALAPPDATA")
            if not app_data_path:
                # Fallback to the user home directory if LOCALAPPDATA is unset
                app_data_path = os.path.expanduser("~")  # Fallback for safety
            # Build the WinSet data directory path and create it if missing
            db_dir = os.path.join(app_data_path, "WinSet")
            os.makedirs(db_dir, exist_ok=True)
            # Final path to the SQLite database file
            self.db_path = os.path.join(db_dir, "history.db")
        else:
            self.db_path = db_path  # Allow override for testing

        # _conn: The SQLite connection object shared across all operations.
        #   check_same_thread=False lets us use this connection from any thread
        #   (guarded by _lock below).
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # Set file permissions AFTER the database is created to ensure
        # the current user can access it. Use OWNER_SECURITY_INFORMATION
        # combined with DACL_SECURITY_INFORMATION to preserve access.
        if os.name == "nt" and os.path.exists(self.db_path):
            try:
                import win32security
                import win32api
                import ntsecuritycon

                sid = win32security.LookupAccountName(None, win32api.GetUserName())[0]
                sd = win32security.SECURITY_DESCRIPTOR()
                sd.SetSecurityDescriptorOwner(sid, False)
                dacl = win32security.ACL()
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS, sid
                )
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                # Use both OWNER and DACL to preserve owner while setting access
                win32security.SetFileSecurity(
                    self.db_path,
                    win32security.OWNER_SECURITY_INFORMATION
                    | win32security.DACL_SECURITY_INFORMATION,
                    sd
                )
            except Exception:
                # Permission setting failed - database should still work for this user
                pass

        # _lock: A reentrant lock that serializes all database access so that
        #   concurrent threads (e.g., a background sync and the UI) never corrupt
        #   the database.
        self._lock = threading.RLock()

        # Enable Write-Ahead Logging so that readers do not block writers and
        # vice versa, improving concurrency on the SQLite database.
        self._conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency

        # Create the 'changes' table if it does not yet exist.
        self._create_table()
        # Create performance indexes on commonly-queried columns.
        self._create_indexes()

    def __enter__(self):
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context."""
        # exc_type, exc_val, exc_tb: Standard context-manager exception parameters
        #   indicating whether an exception occurred inside the with-block.
        self.close()

    def _create_table(self):
        """Create the history table if it doesn't exist."""
        with self._lock:
            # cursor: SQLite cursor used to execute SQL statements against the connection.
            cursor = self._conn.cursor()
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique row ID, auto-generated
                timestamp TEXT NOT NULL,               -- ISO-8601 date/time the change occurred
                setting_id TEXT NOT NULL,              -- Identifier of the WinSet setting that was changed
                setting_name TEXT NOT NULL,            -- Human-readable name of the setting
                old_value TEXT,                        -- Previous value before the change (serialized as string)
                new_value TEXT,                        -- New value after the change (serialized as string)
                value_type TEXT NOT NULL,              -- Registry value type (e.g., REG_DWORD, REG_SZ)
                hive TEXT NOT NULL,                    -- Registry hive (e.g., HKLM, HKCU)
                key_path TEXT NOT NULL,                -- Full Registry key path (e.g., SOFTWARE\\Microsoft\\Windows)
                value_name TEXT NOT NULL,              -- Name of the Registry value within the key
                success INTEGER DEFAULT 1,             -- 1 if the write succeeded, 0 if it failed
                reverted INTEGER DEFAULT 0             -- 1 if this change was later reverted
            )
            """
            )

            # Migration: ensure the 'success' column exists for databases that were
            # created before this column was introduced.
            try:
                cursor.execute("SELECT success FROM changes LIMIT 1")
            except sqlite3.OperationalError:
                # Column missing -- add it with a default of 1 (assumed successful).
                cursor.execute(
                    "ALTER TABLE changes ADD COLUMN success INTEGER DEFAULT 1"
                )
            self._conn.commit()

    def _create_indexes(self):
        """Create indexes for better query performance."""
        with self._lock:
            # cursor: Reused cursor for executing index-creation statements.
            cursor = self._conn.cursor()

            # Index on timestamp (descending) speeds up queries that fetch the most
            # recent changes (e.g., get_history).
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON changes(timestamp DESC)
        """)

            # Index on setting_id speeds up queries that filter history by a specific
            # WinSet setting (e.g., get_history_by_setting).
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_setting_id
            ON changes(setting_id)
        """)

            # Index on success speeds up queries that filter to only successful
            # or failed changes.
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_success
            ON changes(success)
        """)
            self._conn.commit()

    def log_change(
        self, setting: Any, old_value: Any, new_value: Any, success: bool = True
    ):
        """
        Log a single setting change to the database.

        Args:
            setting: The Setting object being changed (must expose id, name, value_type, hive, key_path, value_name attributes)
            old_value: Previous value of the setting before the change
            new_value: New value applied to the setting
            success: Whether the Registry write operation succeeded
        """
        # Sanitize values to prevent SQL injection (though parameterized queries handle this)
        # old_val_str / new_val_str: String representations of the old and new values,
        #   converted safely via _sanitize_value so that None, binary data, dicts, and
        #   lists are handled gracefully.
        old_val_str = self._sanitize_value(old_value)
        new_val_str = self._sanitize_value(new_value)

        # Limit string lengths to 64KB characters to prevent excessive storage usage
        # while still allowing most registry values to be stored and reverted.
        # Windows Registry string values are typically capped at 32KB.
        limit = 65536
        old_val_str = old_val_str[:limit] if old_val_str else "N/A"
        new_val_str = new_val_str[:limit] if new_val_str else "N/A"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
            INSERT INTO changes (
                timestamp, setting_id, setting_name, old_value, new_value,
                value_type, hive, key_path, value_name, success
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
                (
                    # timestamp: Current date/time formatted as "YYYY-MM-DD HH:MM:SS" for readability.
                    datetime.now().isoformat(sep=" ", timespec="seconds"),
                    # setting.id truncated to 100 chars to match column expectations.
                    getattr(setting, "id", "unknown")[:100],
                    # setting.name truncated to 200 chars.
                    getattr(setting, "name", "unknown")[:200],
                    # old / new values already sanitized and truncated above.
                    old_val_str,
                    new_val_str,
                    # Registry value type string (e.g., "REG_DWORD"), truncated to 50 chars.
                    getattr(setting, "value_type", "unknown")[:50],
                    # Registry hive string (e.g., "HKEY_LOCAL_MACHINE"), truncated to 50 chars.
                    getattr(setting, "hive", "unknown")[:50],
                    # Full Registry key path, truncated to 512 chars.
                    getattr(setting, "key_path", "unknown")[:512],
                    # Name of the value within the Registry key, truncated to 255 chars.
                    getattr(setting, "value_name", "unknown")[:255],
                    # Store 1 for success, 0 for failure.
                    1 if success else 0,
                ),
            )
            self._conn.commit()

        # After logging, check if the table has grown beyond the limit and prune if necessary.
        self._prune_if_needed()

    def _sanitize_value(self, value: Any) -> str:
        """Safely convert a value to string for storage."""
        import json
        import base64

        if value is None:
            return "N/A"
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, (bytes, bytearray)):
            # Store binary data as base64 so it can be reverted
            return f"base64:{base64.b64encode(value).decode('ascii')}"
        if isinstance(value, list):
            # Store lists as JSON so they can be reverted
            try:
                return f"json:{json.dumps(value)}"
            except Exception:
                return str(value)[:1000]
        # For strings, store as is but avoid the prefix 'base64:' or 'json:' to avoid confusion
        # (Though those types won't match anyway)
        return str(value)

    def _convert_string_to_value(self, value_str: str, value_type: str) -> Any:
        """Convert string value back to proper type."""
        import json
        import base64

        if value_str == "N/A":
            return None

        try:
            if value_type == "REG_DWORD" or value_type == "REG_QWORD":
                return int(value_str)
            elif value_type in ["REG_SZ", "REG_EXPAND_SZ"]:
                return value_str
            elif value_type == "REG_BINARY":
                if value_str.startswith("base64:"):
                    return base64.b64decode(value_str[7:])
                return value_str
            elif value_type == "REG_MULTI_SZ":
                if value_str.startswith("json:"):
                    return json.loads(value_str[5:])
                return value_str
            else:
                return value_str
        except (ValueError, TypeError, Exception):
            return value_str

    def get_changes_by_setting(self, setting_id: str) -> List[Tuple[Any, ...]]:
        """
        Get all changes for a specific setting.

        Args:
            setting_id: The setting ID to filter by (truncated to 100 chars)

        Returns:
            List of changes, each as (id, timestamp, old_value, new_value, reverted)
        """
        # setting_id: Unique WinSet identifier used to filter the changes table.
        with self._lock:
            # cursor: Used to SELECT changes matching the given setting_id.
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, old_value, new_value, reverted "
                "FROM changes WHERE setting_id = ? ORDER BY timestamp DESC",
                (setting_id[:100],),
            )
            return cursor.fetchall()

    def close(self):
        """Close the database connection."""
        with self._lock:
            # Guard against calling close() more than once.
            if self._conn:
                # Close the underlying SQLite connection and release file handles.
                self._conn.close()
                # Set to None so subsequent calls to close() are safe no-ops.
                self._conn = None
