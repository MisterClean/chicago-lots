import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger('chicago_lots.database')

class PINDatabase:
    def __init__(self, db_path: str):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
        
    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
            
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Main PIN data table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS pins (
                    pin TEXT PRIMARY KEY,
                    address TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    posted INTEGER DEFAULT 0,
                    post_date TIMESTAMP,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            ''')
            
            # Table for tracking posting history
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pin TEXT NOT NULL,
                    post_date TIMESTAMP NOT NULL,
                    post_id TEXT,
                    image_path TEXT,
                    FOREIGN KEY (pin) REFERENCES pins(pin)
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
            
    def add_pin(self, pin: str, address: str, lat: float = None, lon: float = None) -> bool:
        """Add a new PIN record to the database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO pins (pin, address, latitude, longitude)
                VALUES (?, ?, ?, ?)
            ''', (pin, address, lat, lon))
            self.conn.commit()
            logger.info(f"Added PIN record: {pin}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding PIN {pin}: {e}")
            return False
            
    def get_next_unposted(self, batch_size: int = 1) -> List[Dict]:
        """Get the next batch of unposted PINs."""
        try:
            self.cursor.execute('''
                SELECT pin, address, latitude, longitude
                FROM pins
                WHERE posted = 0 AND error_count < 3
                ORDER BY pin
                LIMIT ?
            ''', (batch_size,))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'pin': row[0],
                    'address': row[1],
                    'latitude': row[2],
                    'longitude': row[3]
                })
            return results
        except sqlite3.Error as e:
            logger.error(f"Error getting unposted PINs: {e}")
            return []
            
    def mark_posted(self, pin: str, post_id: str, image_path: str):
        """Mark a PIN as posted and record the post details."""
        try:
            now = datetime.now()
            
            # Update pins table
            self.cursor.execute('''
                UPDATE pins
                SET posted = 1, post_date = ?
                WHERE pin = ?
            ''', (now, pin))
            
            # Add to post history
            self.cursor.execute('''
                INSERT INTO post_history (pin, post_date, post_id, image_path)
                VALUES (?, ?, ?, ?)
            ''', (pin, now, post_id, image_path))
            
            self.conn.commit()
            logger.info(f"Marked PIN {pin} as posted")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error marking PIN {pin} as posted: {e}")
            return False
            
    def record_error(self, pin: str, error_message: str):
        """Record an error for a PIN."""
        try:
            self.cursor.execute('''
                UPDATE pins
                SET error_count = error_count + 1,
                    last_error = ?
                WHERE pin = ?
            ''', (error_message, pin))
            self.conn.commit()
            logger.warning(f"Recorded error for PIN {pin}: {error_message}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording error for PIN {pin}: {e}")
            return False
            
    def get_statistics(self) -> Dict:
        """Get posting statistics."""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN posted = 1 THEN 1 ELSE 0 END) as posted,
                    SUM(CASE WHEN error_count >= 3 THEN 1 ELSE 0 END) as failed
                FROM pins
            ''')
            row = self.cursor.fetchone()
            return {
                'total_pins': row[0],
                'posted_count': row[1],
                'failed_count': row[2],
                'remaining': row[0] - row[1] - row[2]
            }
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
