import openmeteo_requests
from openmeteo_sdk.Variable import Variable
from openmeteo_sdk.Aggregation import Aggregation
import numpy as np
import pandas as pd
from utils.radiation_model import compute_radiance

def call_api(lat, lon, inverter_size, inverter_eff, pvstring_azimuth, pvstring_wp, pvstring_tilt, pvstring_albedo, pvstring_cell_coeff, openmeteo_session):

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "shortwave_radiation", "diffuse_radiation", "direct_normal_irradiance"],
        "models": "icon_d2",
        "tilt": pvstring_tilt,
        "azimuth": pvstring_azimuth,
        "forecast_days": 2,
        "past_days": 0
    }
    responses = openmeteo_session.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_time = range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))

    hourly_temperature_2m = next(filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, hourly_variables)).ValuesAsNumpy()
    temperature_vars = list(filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, hourly_variables))
    temperature_values = np.array([v.ValuesAsNumpy() for v in temperature_vars])

    hourly_shortwave_radiation = next(filter(lambda x: x.Variable() == Variable.shortwave_radiation, hourly_variables)).ValuesAsNumpy()
    shortwave_radiation_vars = list(filter(lambda x: x.Variable() == Variable.shortwave_radiation, hourly_variables))
    shortwave_radiation_values = np.array([v.ValuesAsNumpy() for v in shortwave_radiation_vars])

    hourly_diffuse_radiation = next(filter(lambda x: x.Variable() == Variable.diffuse_radiation, hourly_variables)).ValuesAsNumpy()
    diffuse_radiation_vars = list(filter(lambda x: x.Variable() == Variable.diffuse_radiation, hourly_variables))
    diffuse_radiation_values = np.array([v.ValuesAsNumpy() for v in diffuse_radiation_vars])

    hourly_direct_normal_irradiance = next(filter(lambda x: x.Variable() == Variable.direct_normal_irradiance, hourly_variables)).ValuesAsNumpy()
    direct_normal_irradiance_vars = list(filter(lambda x: x.Variable() == Variable.direct_normal_irradiance, hourly_variables))
    direct_normal_irradiance_values = np.array([v.ValuesAsNumpy() for v in direct_normal_irradiance_vars])


    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s"),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["max_temperature_2m"] = np.nanmax(temperature_values, axis=0)
    hourly_data["min_temperature_2m"] = np.nanmin(temperature_values, axis=0)
    hourly_data["shortwave_radiation"] = hourly_shortwave_radiation
    hourly_data["max_shortwave_radiation"] = np.nanmax(shortwave_radiation_values, axis=0)
    hourly_data["min_shortwave_radiation"] = np.nanmin(shortwave_radiation_values, axis=0)
    hourly_data["diffuse_radiation"] = hourly_diffuse_radiation
    hourly_data["max_diffuse_radiation"] = np.nanmax(diffuse_radiation_values, axis=0)
    hourly_data["min_diffuse_radiation"] = np.nanmin(diffuse_radiation_values, axis=0)
    hourly_data["direct_normal_irradiance"] = hourly_direct_normal_irradiance
    hourly_data["max_direct_normal_irradiance"] = np.nanmax(direct_normal_irradiance_values, axis=0)
    hourly_data["min_direct_normal_irradiance"] = np.nanmin(direct_normal_irradiance_values, axis=0)
    hourly_dataframe_pd = pd.DataFrame(data = hourly_data)
    hourly_dataframe_pd[["dc_power", "max_dc_power", "min_dc_power", "ac_power", "max_ac_power", "min_ac_power"]] = \
    hourly_dataframe_pd.apply(
        lambda row: compute_radiance(
            row,
            latitude=lat,
            longitude=lon,
            inverter_size=inverter_size,
            inverter_eff=inverter_eff,
            pvstring_azimuth=pvstring_azimuth,
            pvstring_wp=pvstring_wp,
            pvstring_tilt=pvstring_tilt,
            pvstring_albedo=pvstring_albedo,
            pvstring_cell_coeff=pvstring_cell_coeff
        ),
        axis=1,
        result_type="expand"
    )

    return hourly_dataframe_pd.to_dict(orient="records")