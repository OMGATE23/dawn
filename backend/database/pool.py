import sqlite3
import threading
import queue
import os
import logging

logger = logging.getLogger(__name__)


class SQLiteConnectionPool:
    def __init__(self, db_path: str = None, pool_size: int = 5):
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", "director.db")
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()

        # Pre-fill the pool with connections
        for _ in range(pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._pool.put(conn)

        logger.info(f"Initialized SQLite pool with {pool_size} connections.")

    def acquire(self):
        """Get a connection from the pool."""
        conn = self._pool.get()
        return conn

    def release(self, conn):
        """Return a connection to the pool."""
        self._pool.put(conn)

    def closeall(self):
        """Close all pooled connections."""
        while not self._pool.empty():
            conn = self._pool.get_nowait()
            conn.close()
