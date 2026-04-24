-- Training data table for ML models
CREATE TABLE IF NOT EXISTS training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    country TEXT,
    temperature REAL,
    humidity INTEGER,
    pressure INTEGER,
    wind_speed REAL,
    condition TEXT,
    source TEXT DEFAULT 'api',
    is_anomaly BOOLEAN DEFAULT 0,
    verified BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model registry to track versions
CREATE TABLE IF NOT EXISTS model_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    model_type TEXT,
    version INTEGER,
    file_path TEXT,
    accuracy REAL,
    precision REAL,
    recall REAL,
    f1_score REAL,
    trained_on DATE,
    data_points INTEGER,
    training_duration REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, version)
);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    model_version INTEGER,
    prediction_date DATE,
    actual_temperature REAL,
    predicted_temperature REAL,
    was_correct BOOLEAN,
    confidence REAL,
    anomaly_detected BOOLEAN,
    actual_anomaly BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city, model_version) REFERENCES model_registry(city, version)
);

-- Training jobs log
CREATE TABLE IF NOT EXISTS training_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT,
    cities_trained TEXT,
    models_updated INTEGER,
    accuracy_improvement REAL,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);