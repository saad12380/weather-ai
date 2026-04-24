"""
Professional Data Collector for ML Training
Collects data from multiple sources: API, Database, User Feedback
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import logging
import json
from typing import List, Dict, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingDataCollector:
    def __init__(self, db_path: str, api_key: str):
        self.db_path = db_path
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def collect_from_api(self, city: str, days: int = 90) -> pd.DataFrame:
        """Collect historical data from OpenWeatherMap API"""
        logger.info(f"📡 Collecting API data for {city} (last {days} days)")
        
        try:
            # Get coordinates first
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={self.api_key}"
            geo_response = requests.get(geo_url)
            
            if geo_response.status_code != 200:
                logger.error(f"Failed to get coordinates for {city}")
                return pd.DataFrame()
            
            location = geo_response.json()[0]
            lat, lon = location['lat'], location['lon']
            
            # Collect historical data
            data = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                
                # Get weather for this date
                weather_url = f"{self.base_url}/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                response = requests.get(weather_url)
                
                if response.status_code == 200:
                    weather = response.json()
                    data.append({
                        'city': city,
                        'country': location.get('country', ''),
                        'temperature': weather['main']['temp'],
                        'humidity': weather['main']['humidity'],
                        'pressure': weather['main']['pressure'],
                        'wind_speed': weather['wind']['speed'],
                        'condition': weather['weather'][0]['description'],
                        'source': 'api',
                        'timestamp': date.isoformat()
                    })
            
            df = pd.DataFrame(data)
            logger.info(f"✅ Collected {len(df)} API records for {city}")
            return df
            
        except Exception as e:
            logger.error(f"❌ API collection failed for {city}: {e}")
            return pd.DataFrame()
    
    def collect_from_database(self, city: str, days: int = 365) -> pd.DataFrame:
        """Collect user-requested weather data from database"""
        logger.info(f"📊 Collecting database data for {city} (last {days} days)")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get data from activity_log
        query = """
            SELECT 
                city,
                temperature,
                humidity,
                pressure,
                wind_speed,
                'user' as source,
                timestamp
            FROM activity_log 
            WHERE city = ? AND activity_type = 'Weather Check'
            AND timestamp >= datetime('now', '-' || ? || ' days')
        """
        
        try:
            df = pd.read_sql_query(query, conn, params=[city, days])
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            df = pd.DataFrame()
        
        conn.close()
        
        logger.info(f"✅ Collected {len(df)} database records for {city}")
        return df
    
    def collect_user_feedback(self, city: str, days: int = 30) -> pd.DataFrame:
        """Collect user feedback on anomaly predictions"""
        logger.info(f"💬 Collecting user feedback for {city}")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get anomaly predictions
        query = """
            SELECT 
                city,
                temperature,
                humidity,
                pressure,
                wind_speed,
                is_anomaly,
                timestamp
            FROM activity_log 
            WHERE city = ? AND activity_type = 'Anomaly Detection'
            AND timestamp >= datetime('now', '-' || ? || ' days')
        """
        
        try:
            df = pd.read_sql_query(query, conn, params=[city, days])
        except Exception as e:
            logger.error(f"Error querying feedback: {e}")
            df = pd.DataFrame()
        
        conn.close()
        
        logger.info(f"✅ Collected {len(df)} feedback records for {city}")
        return df
    
    def prepare_training_data(self, city: str, days: int = 365) -> pd.DataFrame:
        """Prepare combined training data from all sources"""
        logger.info(f"🔄 Preparing training data for {city}")
        
        # Collect from all sources
        api_data = self.collect_from_api(city, min(days, 90))
        db_data = self.collect_from_database(city, days)
        feedback_data = self.collect_user_feedback(city, min(days, 30))
        
        # Combine all data
        all_data = pd.concat([api_data, db_data], ignore_index=True)
        
        if len(all_data) == 0:
            logger.warning(f"⚠️ No training data for {city}")
            return pd.DataFrame()
        
        # Remove duplicates based on timestamp
        all_data = all_data.drop_duplicates(subset=['timestamp'])
        
        # Sort by timestamp
        all_data = all_data.sort_values('timestamp')
        
        # Add derived features
        all_data['timestamp'] = pd.to_datetime(all_data['timestamp'])
        all_data['hour'] = all_data['timestamp'].dt.hour
        all_data['day'] = all_data['timestamp'].dt.day
        all_data['month'] = all_data['timestamp'].dt.month
        all_data['day_of_year'] = all_data['timestamp'].dt.dayofyear
        all_data['day_of_week'] = all_data['timestamp'].dt.dayofweek
        
        # Add rolling statistics
        all_data['temp_rolling_mean_7'] = all_data['temperature'].rolling(7, min_periods=1).mean()
        all_data['temp_rolling_std_7'] = all_data['temperature'].rolling(7, min_periods=1).std()
        
        logger.info(f"✅ Final training data: {len(all_data)} records for {city}")
        return all_data
    
    def save_to_training_table(self, df: pd.DataFrame):
        """Save collected data to training_data table"""
        if df.empty:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO training_data 
                    (city, country, temperature, humidity, pressure, wind_speed, 
                     condition, source, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('city'),
                    row.get('country', ''),
                    row.get('temperature'),
                    row.get('humidity'),
                    row.get('pressure'),
                    row.get('wind_speed'),
                    row.get('condition', 'Unknown'),
                    row.get('source', 'api'),
                    row.get('timestamp')
                ))
            except Exception as e:
                logger.error(f"Error saving row: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Saved {len(df)} records to training_data table")