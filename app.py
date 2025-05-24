import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
import yaml
import json

from flask import Flask, request, jsonify
from meteo_api import fetch_dwd_icon, fetch_ensemble
from processor import process_hourly_data
from calculator import calculate_forecast
from utils.config_utils import validate_config
from utils.open_meteo_utils import call_api
from utils.radiation_model import aggregate_results
from utils.solar_position import deg_to_rad, get_sun_position, vector_from_angles, dot_product_efficiency
from openmeteo_sdk.Variable import Variable
from openmeteo_sdk.Aggregation import Aggregation
from collections import defaultdict
from retry_requests import retry

app = Flask(__name__)

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Invalid path or parameter types'}), 404

@app.route('/forecast', methods=['POST'])
def forecast_post():

    config = request.get_json()
    if not config:
        return jsonify({'error': 'No configuration provided'}), 400
    
    errors = validate_config(config)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        inverters = config["inverters"]
        all_results = []
        for inverter in inverters:
            for pvstring in inverter["pv_strings"]:
                latitude = config["latitude"]
                longitude = config["longitude"]
                inverter_size = inverter["size"]
                inverter_max_ac = inverter["max_ac"]
                inverter_eff = inverter.get("inverter_eff", 0.98)
                pvstring_azimuth = pvstring["azimuth"]
                pvstring_tilt = pvstring["tilt"]
                pvstring_wp = pvstring["wp"]
                pvstring_albedo = pvstring.get("albedo", 0.2)
                pvstring_cell_coeff = pvstring.get("cell_coeff", 0.0382)

                data = call_api(lat=latitude, lon=longitude, inverter_size=inverter_size, inverter_eff=inverter_eff, pvstring_azimuth=pvstring_azimuth, pvstring_wp=pvstring_wp, pvstring_tilt=pvstring_tilt, pvstring_albedo=pvstring_albedo, pvstring_cell_coeff=pvstring_cell_coeff, openmeteo_session=openmeteo)
                if not data or "error" in data:
                    return jsonify({'error': 'Failed to fetch weather data'}), 500
                all_results.extend(data)

        combined = aggregate_results(all_results)
        for entry in combined:
            if isinstance(entry.get("datetime"), pd.Timestamp):
                entry["datetime"] = entry["datetime"].isoformat()

        return jsonify({"values": combined})

    except Exception as e:
        return jsonify({'error': f'Failed to initialize API clients: {str(e)}'}), 500

@app.route('/')
def home():
    return jsonify({'message': 'Hello from PySolAPI! API is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)