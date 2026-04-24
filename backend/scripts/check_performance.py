#!/usr/bin/env python3
"""
Check Model Performance
Run with: python check_performance.py [city]
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3

sys.path.append(str(Path(__file__).parent.parent))

def main():
    parser = argparse.ArgumentParser(description='Check model performance')
    parser.add_argument('city', nargs='?', help='City to check (empty = all)')
    parser.add_argument('--history', type=int, default=5, help='Show version history')
    
    args = parser.parse_args()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(current_dir, '..', 'weather_anomaly_users.db')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    if args.city:
        # Show specific city
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM model_registry 
            WHERE city = ? 
            ORDER BY version DESC LIMIT ?
        """, (args.city, args.history))
        
        models = cursor.fetchall()
        
        if models:
            print(f"\n📊 Model History for {args.city}:")
            print("-" * 80)
            print(f"{'Version':<8} {'Type':<20} {'Accuracy':<10} {'Data':<10} {'Date':<12} {'Active'}")
            print("-" * 80)
            for m in models:
                active = "✅" if m['is_active'] else "❌"
                print(f"{m['version']:<8} {m['model_type']:<20} {m['accuracy']:.1f}%{'':<6} {m['data_points']:<10} {m['trained_on']:<12} {active}")
        else:
            print(f"No models found for {args.city}")
    
    else:
        # Show all cities
        cursor = conn.cursor()
        cursor.execute("""
            SELECT city, 
                   COUNT(*) as versions,
                   MAX(accuracy) as best_accuracy,
                   SUM(data_points) as total_data
            FROM model_registry 
            GROUP BY city
            ORDER BY best_accuracy DESC
        """)
        
        cities = cursor.fetchall()
        
        if cities:
            print("\n🌍 Model Summary by City:")
            print("-" * 60)
            print(f"{'City':<15} {'Versions':<10} {'Best Accuracy':<15} {'Total Data'}")
            print("-" * 60)
            for c in cities:
                print(f"{c['city']:<15} {c['versions']:<10} {c['best_accuracy']:.1f}%{'':<8} {c['total_data']}")
        else:
            print("No models found")
    
    conn.close()

if __name__ == "__main__":
    main()