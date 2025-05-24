import numpy as np
from utils.solar_position import deg_to_rad
from utils.solar_position import get_sun_position, vector_from_angles, dot_product_efficiency
from collections import defaultdict

def calc_radiation_model(dni, diffuse, shortwave, efficiency, albedo, cell_coeff, power, inverter_eff, inverter_size, temperature, tilt):
    """
    Estimates DC and AC power output for a PV system based on solar input and system parameters.

    Args:
        dni (float): Direct Normal Irradiance (W/m²)
        diffuse (float): Diffuse radiation (W/m²)
        shortwave (float): Global horizontal radiation (W/m²)
        efficiency (float): Geometric efficiency (0-1) from sun/panel alignment
        albedo (float): Ground reflectivity (0.0–1.0)
        cell_coeff (float): Temperature coefficient per W/m² for the module
        power (float): Nominal power output (kW DC)
        inverter_eff (float): Inverter efficiency (0-1)
        inverter_size (float): Max output of inverter (kW AC)
        temperature (float): Air temperature (°C)
        tilt (float): Panel tilt in degrees

    Returns:
        ac_power, dc_power, total_radiation_on_cell, cell_temperature
    """
    # Calculate total irradiance on panel (rough estimate)
    total_radiation = efficiency * (dni + diffuse) + albedo * shortwave * np.cos(deg_to_rad(tilt))

    # Estimate cell temperature using nominal operating cell temperature model
    cell_temperature = temperature + total_radiation * cell_coeff

    # Estimate DC power output
    dc_power = power * total_radiation / 1000  # convert W/m² to kW per kWp

    # Estimate AC output with inverter efficiency and limit
    ac_power = min(dc_power * inverter_eff, inverter_size)

    return ac_power, dc_power, total_radiation, cell_temperature


def compute_radiance(row, latitude, longitude, inverter_size, inverter_eff, pvstring_azimuth, pvstring_wp, pvstring_tilt, pvstring_albedo, pvstring_cell_coeff):

    # Calculate the efficiency of the solar panel based on the sun position and panel orientation
    sun_az, sun_alt = get_sun_position(latitude, longitude, row["date"])
    sun_vec = vector_from_angles(sun_az, sun_alt)
    panel_vec = vector_from_angles(pvstring_azimuth, 90 - pvstring_tilt)
    geom_efficiency = dot_product_efficiency(sun_vec, panel_vec)

    radiation = geom_efficiency *  (row["direct_normal_irradiance"] + row["diffuse_radiation"]) + pvstring_albedo * row["shortwave_radiation"] * np.cos(deg_to_rad(pvstring_tilt))
    max_radiation = geom_efficiency *  (row["max_direct_normal_irradiance"] + row["max_diffuse_radiation"]) + pvstring_albedo * row["max_shortwave_radiation"] * np.cos(deg_to_rad(pvstring_tilt))
    min_radiation = geom_efficiency *  (row["min_direct_normal_irradiance"] + row["min_diffuse_radiation"]) + pvstring_albedo * row["min_shortwave_radiation"] * np.cos(deg_to_rad(pvstring_tilt))
    panel_temp = row["temperature_2m"] + radiation * pvstring_cell_coeff
    dc_power = pvstring_wp * radiation / 1000
    max_dc_power = pvstring_wp * max_radiation / 1000
    min_dc_power = pvstring_wp * min_radiation / 1000
    ac_power = min(dc_power * inverter_eff, inverter_size)
    max_ac_power = min(max_dc_power * inverter_eff, inverter_size)
    min_ac_power = min(min_dc_power * inverter_eff, inverter_size)
    return (dc_power, max_dc_power, min_dc_power, ac_power, max_ac_power, min_ac_power)

def aggregate_results(result):
    hourly = defaultdict(lambda: {"ac_power": 0, "min_ac_power": 0, "max_ac_power": 0})
    for entry in result:
        dt = entry["date"]
        ac_power = round(entry["ac_power"], 0)
        min_ac_power = round(entry["min_ac_power"], 0)
        max_ac_power = round(entry["max_ac_power"], 0)
        hourly[dt]["ac_power"] += ac_power
        hourly[dt]["min_ac_power"] += min(min_ac_power, ac_power)
        hourly[dt]["max_ac_power"] += max(max_ac_power, ac_power)
    # Convert inf/-inf to 0 if no data
    for v in hourly.values():
        if v["min_ac_power"] == float('inf'):
            v["min_ac_power"] = 0
        if v["max_ac_power"] == float('-inf'):
            v["max_ac_power"] = 0
    return [{"datetime": k, **v} for k, v in sorted(hourly.items())]