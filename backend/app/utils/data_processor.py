import pandas as pd

def load_weather_data(path):
    return pd.read_csv(path)