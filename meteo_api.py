import requests

def fetch_dwd_icon(latitude, longitude, timezone="Europe/Berlin", past_days=0):
    url = "https://api.open-meteo.com/v1/dwd-icon"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,shortwave_radiation,diffuse_radiation,direct_normal_irradiance",
        "timezone": timezone,
        "past_days": past_days
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_ensemble(latitude, longitude, timezone="Europe/Berlin", forecast_days=2, past_days=0):
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,shortwave_radiation,diffuse_radiation,direct_normal_irradiance",
        "timezone": timezone,
        "models": "icon_d2",
        "forecast_days": forecast_days,
        "past_days": past_days
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
