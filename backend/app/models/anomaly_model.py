import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

class WeatherAnomalyPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def generate_sample_data(self):
        """Generate sample weather data for training"""
        np.random.seed(42)
        n_samples = 1000
        
        # Normal weather data
        temp_normal = np.random.normal(20, 5, n_samples)
        humidity_normal = np.random.normal(60, 15, n_samples)
        pressure_normal = np.random.normal(1013, 10, n_samples)
        wind_speed_normal = np.random.normal(10, 4, n_samples)
        
        # Anomalous weather data (5% anomalies)
        n_anomalies = 50
        temp_anomaly = np.random.normal(40, 8, n_anomalies)  # Very high temp
        humidity_anomaly = np.random.normal(90, 5, n_anomalies)  # Very high humidity
        pressure_anomaly = np.random.normal(980, 15, n_anomalies)  # Very low pressure
        wind_speed_anomaly = np.random.normal(25, 8, n_anomalies)  # Very high wind
        
        # Combine data
        temperatures = np.concatenate([temp_normal, temp_anomaly])
        humidities = np.concatenate([humidity_normal, humidity_anomaly])
        pressures = np.concatenate([pressure_normal, pressure_anomaly])
        wind_speeds = np.concatenate([wind_speed_normal, wind_speed_anomaly])
        
        data = pd.DataFrame({
            'temperature': temperatures,
            'humidity': humidities,
            'pressure': pressures,
            'wind_speed': wind_speeds
        })
        
        return data
    
    def train(self):
        """Train the anomaly detection model"""
        print("Training anomaly detection model...")
        
        # Generate sample data
        data = self.generate_sample_data()
        
        # Scale the features
        X_scaled = self.scaler.fit_transform(data)
        
        # Train Isolation Forest model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,  # 5% anomalies expected
            random_state=42
        )
        
        self.model.fit(X_scaled)
        self.is_trained = True
        
        print("Model training completed!")
        
        # Save the model
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/anomaly_model.joblib')
        joblib.dump(self.scaler, 'models/scaler.joblib')
    
    def load_model(self):
        """Load pre-trained model"""
        try:
            self.model = joblib.load('models/anomaly_model.joblib')
            self.scaler = joblib.load('models/scaler.joblib')
            self.is_trained = True
            print("Model loaded successfully!")
        except:
            print("No pre-trained model found. Training new model...")
            self.train()
    
    def predict(self, features):
        """Predict if weather data is anomalous"""
        if not self.is_trained:
            self.load_model()
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict (-1 for anomalies, 1 for normal)
        predictions = self.model.predict(features_scaled)
        
        # Convert to binary (1 for anomaly, 0 for normal)
        return (predictions == -1).astype(int)
    
    def predict_proba(self, features):
        """Get anomaly probability"""
        if not self.is_trained:
            self.load_model()
        
        features_scaled = self.scaler.transform(features)
        scores = self.model.decision_function(features_scaled)
        
        # Convert to probability (higher score = more normal)
        prob_normal = 1 / (1 + np.exp(-scores))
        prob_anomaly = 1 - prob_normal
        
        return np.column_stack([prob_normal, prob_anomaly])