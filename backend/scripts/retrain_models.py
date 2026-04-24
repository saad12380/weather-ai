#!/usr/bin/env python3
"""
Manual Model Retraining Script
Run with: python retrain_models.py [city1 city2 ...]
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from training.trainer import ProfessionalTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Retrain ML models')
    parser.add_argument('cities', nargs='*', help='Cities to train (empty = all)')
    parser.add_argument('--force', action='store_true', help='Force retrain even if not needed')
    
    args = parser.parse_args()
    
    # Configuration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(current_dir, '..', 'weather_anomaly_users.db')
    MODELS_DIR = os.path.join(current_dir, '..', 'models')
    API_KEY = "1731d1e3228cecf7bcab17127f298d98"  # Your API key
    
    # Initialize trainer
    trainer = ProfessionalTrainer(DB_PATH, MODELS_DIR, API_KEY)
    
    if args.cities:
        logger.info(f"🎯 Training specific cities: {args.cities}")
        for city in args.cities:
            trainer.train_ensemble(city)
    else:
        logger.info("🌍 Training all cities with sufficient data")
        trainer.train_all_cities()
    
    logger.info("✅ Training completed!")

if __name__ == "__main__":
    main()