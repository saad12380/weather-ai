import requests
import os
from datetime import datetime, timedelta
import random

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, city: str, country: str = "US"):
        """Get current weather data - using mock data for demo"""
        
        # Mock weather data (in real implementation, use OpenWeatherMap API)
        mock_weather_data = {
            'New York': {'temp': 22, 'humidity': 65, 'pressure': 1013, 'wind_speed': 12, 'description': 'Clear sky'},
            'London': {'temp': 15, 'humidity': 75, 'pressure': 1015, 'wind_speed': 8, 'description': 'Cloudy'},
            'Tokyo': {'temp': 18, 'humidity': 70, 'pressure': 1012, 'wind_speed': 10, 'description': 'Partly cloudy'},
            'Mumbai': {'temp': 32, 'humidity': 80, 'pressure': 1008, 'wind_speed': 6, 'description': 'Hot'},
            'Sydney': {'temp': 25, 'humidity': 60, 'pressure': 1018, 'wind_speed': 15, 'description': 'Sunny'}
        }
        
        if city in mock_weather_data:
            data = mock_weather_data[city]
        else:
            # Generate random weather data for unknown cities
            data = {
                'temp': random.randint(-10, 40),
                'humidity': random.randint(30, 95),
                'pressure': random.randint(980, 1030),
                'wind_speed': random.randint(0, 30),
                'description': random.choice(['Clear', 'Cloudy', 'Rainy', 'Snowy'])
            }
        
        return {
            'city': city,
            'country': country,
            'temperature': data['temp'],
            'humidity': data['humidity'],
            'pressure': data['pressure'],
            'wind_speed': data['wind_speed'],
            'description': data['description'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_historical_weather(self, city: str, days: int = 7):
        """Get historical weather data - mock implementation"""
        history_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            
            # Generate realistic historical data with some variations
            base_temp = 20 + random.uniform(-10, 10)
            
            history_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'temperature': round(base_temp, 1),
                'humidity': random.randint(40, 90),
                'pressure': random.randint(1000, 1020),
                'wind_speed': random.randint(5, 20),
                'was_anomaly': random.random() < 0.1  # 10% chance of historical anomaly
            })
        
        return {
            'city': city,
            'days': days,
            'history': history_data[::-1]  # Reverse to show oldest first
        }