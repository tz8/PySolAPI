from flask import Flask, request, jsonify
from meteo_api import fetch_dwd_icon, fetch_ensemble
from processor import process_hourly_data
from calculator import calculate_forecast

app = Flask(__name__)

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Invalid path or parameter types'}), 404

@app.route('/forecast/<lat>/<lon>/<power>/<azimuth>/<tilt>', methods=['GET'])
def forecast(lat, lon, power, azimuth, tilt):

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({'error': 'lat and lon must be float values like "11.111"'}), 400

    try:
        power = int(power)
        azimuth = int(azimuth)
        tilt = int(tilt)
    except ValueError:
        return jsonify({'error': 'power, azimuth, and tilt must be integers'}), 400


    # hier müssen nun die Berechnungen rein:
    # 1. Daten vom der open-meteo.com API abfragen
    # https://ensemble-api.open-meteo.com/v1/ensemble?latitude=50.76&longitude=9.497&tilt=30&hourly=temperature_2m,shortwave_radiation,diffuse_radiation,direct_normal_irradiance&timezone=UTC&forecast_days=3&models=icon_d2
    # 2. weitere Daten abfragen:
    # https://api.open-meteo.com/v1/dwd-icon?latitude=50.76&longitude=9.497&hourly=temperature_2m,shortwave_radiation,diffuse_radiation,direct_normal_irradiance&timezone=UTC&past_days=0

    # zum Abholen der Daten wird nur lat, lon und tilt benötigt

    try:
        # Optional query params
        albedo = float(request.args.get('albedo', 0.2))
        cell_coeff = float(request.args.get('cellCoeff', 0.04))
        inverter_eff = float(request.args.get('inverterEff', 0.96))
        inverter_size = float(request.args.get('inverterSize', power))
        timezone = request.args.get('timezone', 'Europe/Berlin')
        debug = request.args.get('debug', 'false').lower() == 'true'

        # Fetch weather data
        dwd_data = fetch_dwd_icon(lat, lon, timezone)
        ensemble_data = fetch_ensemble(lat, lon, timezone)

        # Convert to pandas DataFrame
        df_dwd = process_hourly_data(dwd_data)
        df_ensemble = process_hourly_data(ensemble_data)  # Not used yet — future: min/max stats

        # Run forecast calculation
        forecast_result = calculate_forecast(
            df_dwd,
            ensemble_data,
            lat,
            lon,
            timezone,
            power,
            azimuth,
            tilt,
            albedo,
            cell_coeff,
            inverter_size,
            inverter_eff,
            debug=debug
        )

        return jsonify({"values": forecast_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({'message': 'Hello from PySolAPI! API is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)