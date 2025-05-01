import numpy as np
from utils.solar_position import deg_to_rad

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