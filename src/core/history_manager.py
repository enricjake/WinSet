"""
HistoryManager for WinSet - logs all setting changes to a persistent database.
"""

import sqlite3
import os
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Optional, Dict


class HistoryManager:
    """Handles logging and retrieving setting changes from a local SQLite DB."""

    # Maximum number of history entries to keep (prevents database bloat)
    MAX_HISTORY_ENTRIES = 10000
    
    # Days to keep history by default
    DEFAULT_RETENTION_DAYS = 90

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            app_data_path = os.getenv("LOCALAPPDATA")
            if not app_data_path:
                app_data_path = os.path.expanduser("~")  # Fallback for safety
            db_dir = os.path.join(app_data_path, "WinSet")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "history.db")
        else:
            self.db_path = db_path  # Allow override for testing

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._lock = threading.RLock()
        self._conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        self._create_table()
        self._create_indexes()

    def __enter__(self):
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context."""
        self.close()

    def _create_table(self):
        """Create the history table if it doesn't exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                setting_id TEXT NOT NULL,
                setting_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                value_type TEXT NOT NULL,
                hive TEXT NOT NULL,
                key_path TEXT NOT NULL,
                value_name TEXT NOT NULL,
                success INTEGER DEFAULT 1,
                reverted INTEGER DEFAULT 0
            )
            """
            )
        
        # Ensure 'success' column exists (for databases created before this column was added)
            try:
                cursor.execute("SELECT success FROM changes LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE changes ADD COLUMN success INTEGER DEFAULT 1")
            self._conn.commit()

    def _create_indexes(self):
        """Create indexes for better query performance."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON changes(timestamp DESC)
        """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_setting_id 
            ON changes(setting_id)
        """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_success 
            ON changes(success)
        """)
            self._conn.commit()

    def log_change(self, setting: Any, old_value: Any, new_value: Any, success: bool = True):
        """
        Log a single setting change to the database.
        
        Args:
            setting: The Setting object being changed
            old_value: Previous value
            new_value: New value
            success: Whether the operation succeeded
        """
        # Sanitize values to prevent SQL injection (though parameterized queries handle this)
        old_val_str = self._sanitize_value(old_value)
        new_val_str = self._sanitize_value(new_value)
        
        # Limit string lengths to prevent excessive storage
        old_val_str = old_val_str[:1000] if old_val_str else "N/A"
        new_val_str = new_val_str[:1000] if new_val_str else "N/A"

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
                datetime.now().isoformat(sep=" ", timespec="seconds"),
                getattr(setting, 'id', 'unknown')[:100],
                getattr(setting, 'name', 'unknown')[:200],
                old_val_str,
                new_val_str,
                getattr(setting, 'value_type', 'unknown')[:50],
                getattr(setting, 'hive', 'unknown')[:50],
                getattr(setting, 'key_path', 'unknown')[:512],
                getattr(setting, 'value_name', 'unknown')[:255],
                1 if success else 0,
            ),
            )
            self._conn.commit()
        
        # Prune old entries if we have too many
        self._prune_if_needed()

    def _sanitize_value(self, value: Any) -> str:
        """Safely convert a value to string for storage."""
        if value is None:
            return "N/A"
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, (bytes, bytearray)):
            return f"<binary data: {len(value)} bytes>"
        if isinstance(value, dict):
            # Limit dictionary representation
            return str({k: str(v)[:100] for k, v in list(value.items())[:10]})[:500]
        if isinstance(value, list):
            # Limit list representation
            return str([str(v)[:100] for v in value[:10]])[:500]
        return str(value)[:1000]

    def _prune_if_needed(self):
        """Check if we need to prune old entries and do so."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM changes")
            count = cursor.fetchone()[0]
        
        if count > self.MAX_HISTORY_ENTRIES:
            # Delete oldest entries to get back to 80% of max
            to_delete = count - int(self.MAX_HISTORY_ENTRIES * 0.8)
            cursor.execute(
                "DELETE FROM changes WHERE id IN (SELECT id FROM changes ORDER BY timestamp ASC LIMIT ?)",
                (to_delete,)
            )
            self._conn.commit()
            # Lightweight index/statistics refresh without long VACUUM blocking.
            self._conn.execute("PRAGMA optimize")

    def prune_old_history(self, days_to_keep: int = None):
        """
        Delete history entries older than specified days.
        
        Args:
            days_to_keep: Number of days to keep (default: DEFAULT_RETENTION_DAYS)
        """
        if days_to_keep is None:
            days_to_keep = self.DEFAULT_RETENTION_DAYS
            
        with self._lock:
            cursor = self._conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            cursor.execute(
                "DELETE FROM changes WHERE timestamp < ?",
                (cutoff_date,)
            )
            deleted = cursor.rowcount
            self._conn.commit()
            if deleted > 0:
                self._conn.execute("PRAGMA optimize")
            return deleted

    def get_history(self, limit: int = 100, success_only: bool = False) -> List[Tuple[Any, ...]]:
        """
        Retrieve recent changes, sorted by most recent first.
        
        Args:
            limit: Maximum number of entries to return
            success_only: Only return successful changes
            
        Returns:
            List of history entries
        """
        with self._lock:
            cursor = self._conn.cursor()
            if success_only:
                cursor.execute(
                    "SELECT id, timestamp, setting_name, old_value, new_value, success "
                    "FROM changes WHERE success = 1 ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            else:
                cursor.execute(
                    "SELECT id, timestamp, setting_name, old_value, new_value, success "
                    "FROM changes ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            return cursor.fetchall()

    def get_history_by_setting(self, setting_id: str, limit: int = 50) -> List[Tuple[Any, ...]]:
        """
        Retrieve history for a specific setting.
        
        Args:
            setting_id: The ID of the setting
            limit: Maximum number of entries
            
        Returns:
            List of history entries for that setting
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, old_value, new_value, success "
                "FROM changes WHERE setting_id = ? ORDER BY timestamp DESC LIMIT ?",
                (setting_id[:100], limit)
            )
            return cursor.fetchall()

    def get_change_details(self, change_id: int) -> Optional[Tuple[Any, ...]]:
        """
        Get the details needed to revert a specific change by its ID.
        
        Args:
            change_id: The ID of the change to retrieve
            
        Returns:
            Tuple of (hive, key_path, value_name, value_type, old_value) or None
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT hive, key_path, value_name, value_type, old_value FROM changes WHERE id = ?",
                (change_id,),
            )
            return cursor.fetchone()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the history database.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM changes")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM changes WHERE success = 1")
            successful = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT setting_id) FROM changes")
            unique_settings = cursor.fetchone()[0]
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM changes")
            first, last = cursor.fetchone()
        
        # Get database size
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        
        return {
            "total_entries": total,
            "successful_changes": successful,
            "failed_changes": total - successful,
            "unique_settings": unique_settings,
            "first_entry": first,
            "last_entry": last,
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2)
        }

    def export_history(self, filepath: str, format: str = "json") -> bool:
        """
        Export history to a file for backup or analysis.
        
        Args:
            filepath: Path to export file
            format: Export format ('json' or 'csv')
            
        Returns:
            True if successful, False otherwise
        """
        import csv
        import json
        
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, setting_name, old_value, new_value, success FROM changes "
                "ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()
        
        try:
            if format == "json":
                data = [
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "setting_name": row[2],
                        "old_value": row[3],
                        "new_value": row[4],
                        "success": bool(row[5])
                    }
                    for row in rows
                ]
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format == "csv":
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Timestamp", "Setting", "Old Value", "New Value", "Success"])
                    writer.writerows(rows)
            else:
                return False
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
        
        # src/history/history_manager.py

    def clear_history(self) -> bool:
        """
        Clear all history.
        
        Returns:
            True if clear was successful, False otherwise
        """
        try:
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute("DELETE FROM changes")
                self._conn.commit()
            return True
        except Exception:
            return False
        
    def revert_change(self, change_id: int) -> bool:
        """
        Revert a specific change by ID.
        
        Args:
            change_id: The ID of the change to revert
        
        Returns:
            True if revert was successful, False otherwise
        """
        try:
            # Get change details
            details = self.get_change_details(change_id)
            if not details:
                return False
            
            hive, key_path, value_name, value_type, old_value = details
            
            # Import here to avoid circular imports
            from .registry_handler import RegistryHandler
            handler = RegistryHandler()
            
            # Convert old_value back to proper type
            converted_value = self._convert_string_to_value(old_value, value_type)
            
            # Revert the change
            success = handler.write_value(hive, key_path, value_name, value_type, converted_value)
            
            if success:
                # Mark the change as reverted in database
                with self._lock:
                    cursor = self._conn.cursor()
                    cursor.execute("UPDATE changes SET reverted = 1 WHERE id = ?", (change_id,))
                    self._conn.commit()
            
            return success
        except Exception:
            return False
    
    def _convert_string_to_value(self, value_str: str, value_type: str) -> Any:
        """Convert string value back to proper type."""
        if value_str == "N/A":
            return None
        
        try:
            if value_type == "REG_DWORD":
                return int(value_str)
            elif value_type == "REG_QWORD":
                return int(value_str)
            elif value_type in ["REG_SZ", "REG_EXPAND_SZ"]:
                return value_str
            else:
                return value_str
        except (ValueError, TypeError):
            return value_str

    def get_changes_by_setting(self, setting_id: str) -> List[Tuple[Any, ...]]:
        """
        Get all changes for a specific setting.
        
        Args:
            setting_id: The setting ID to filter by
        
        Returns:
            List of changes for the specified setting
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, old_value, new_value, reverted "
                "FROM changes WHERE setting_id = ? ORDER BY timestamp DESC",
                (setting_id[:100],)
            )
            return cursor.fetchall()

    def close(self):
        """Close the database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None