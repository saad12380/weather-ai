"""
Model Registry - Tracks all model versions and their performance
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import joblib
import os

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self, db_path: str, models_dir: str):
        self.db_path = db_path
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
    
    def register_model(self, city: str, model_type: str, version: int, 
                      metrics: Dict, file_path: str) -> int:
        """Register a new model version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Deactivate previous version
        cursor.execute("""
            UPDATE model_registry 
            SET is_active = 0 
            WHERE city = ? AND model_type = ?
        """, (city, model_type))
        
        # Insert new version
        cursor.execute("""
            INSERT INTO model_registry 
            (city, model_type, version, file_path, accuracy, 
             data_points, training_duration, is_active, trained_on)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            city,
            model_type,
            version,
            file_path,
            metrics.get('accuracy', 0),
            metrics.get('data_points', 0),
            metrics.get('training_time', 0),
            1,
            datetime.now().date().isoformat()
        ))
        
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Registered {city} {model_type} v{version} (ID: {model_id})")
        return model_id
    
    def get_active_model(self, city: str, model_type: str = 'ensemble') -> Optional[Dict]:
        """Get the active model for a city"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM model_registry 
            WHERE city = ? AND model_type = ? AND is_active = 1
            ORDER BY version DESC LIMIT 1
        """, (city, model_type))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_model_history(self, city: str, model_type: str = 'ensemble', limit: int = 10) -> List[Dict]:
        """Get version history for a city's model"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM model_registry 
            WHERE city = ? AND model_type = ?
            ORDER BY version DESC LIMIT ?
        """, (city, model_type, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_next_version(self, city: str, model_type: str) -> int:
        """Get the next version number for a city's model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(version) FROM model_registry 
            WHERE city = ? AND model_type = ?
        """, (city, model_type))
        
        max_version = cursor.fetchone()[0]
        conn.close()
        
        return (max_version or 0) + 1
    
    def save_model(self, model_data: dict, city: str, model_type: str, metrics: Dict) -> str:
        """Save model to disk and register it"""
        version = self.get_next_version(city, model_type)
        filename = f"{city}_{model_type}_v{version}.joblib"
        filepath = os.path.join(self.models_dir, filename)
        
        # Save model
        joblib.dump(model_data, filepath)
        
        # Register in database
        self.register_model(city, model_type, version, metrics, filepath)
        
        return filepath