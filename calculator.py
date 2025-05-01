from utils.solar_position import get_sun_position, vector_from_angles, dot_product_efficiency
from utils.radiation_model import calc_radiation_model
import numpy as np
from datetime import timedelta
import pytz

def calculate_forecast(data_timeline, ensemble_data, lat, lon, timezone, power, azimuth, tilt,
                       albedo, cell_coeff, power_inverter, inverter_efficiency, horizont=None,
                       debug=False, additional_fields=None):

    power = np.atleast_1d(power)
    results = []

    for i, p_val in enumerate(power):
        az = azimuth[i] if isinstance(azimuth, (list, np.ndarray)) else azimuth
        tl = tilt[i] if isinstance(tilt, (list, np.ndarray)) else tilt
        al = albedo[i] if isinstance(albedo, (list, np.ndarray)) else albedo
        cc = cell_coeff[i] if isinstance(cell_coeff, (list, np.ndarray)) else cell_coeff
        inv = power_inverter[i] if isinstance(power_inverter, (list, np.ndarray)) else power_inverter
        eff = inverter_efficiency[i] if isinstance(inverter_efficiency, (list, np.ndarray)) else inverter_efficiency
        hor = horizont[i] if isinstance(horizont, list) and isinstance(horizont[0], list) else horizont

        pv_vector = vector_from_angles(az, 90 - tl)

        for _, row in data_timeline.iterrows():
            t_utc = row["time"]
            if t_utc.tzinfo is None:
                t_utc = t_utc.tz_localize("UTC")
            else:
                t_utc = t_utc.astimezone(pytz.UTC)
    
            t_local = t_utc.astimezone(pytz.timezone(timezone))
            sun_time = t_utc + timedelta(minutes=30)

            dni = row["direct_normal_irradiance"]
            diffuse = row["diffuse_radiation"]
            shortwave = row["shortwave_radiation"]
            temp = row["temperature_2m"]

            sun_az, sun_alt = get_sun_position(lat, lon, sun_time)
            sun_vec = vector_from_angles(sun_az, sun_alt)

            eff_value = dot_product_efficiency(sun_vec, pv_vector)

            if hor and eff_value > 0:
                hor_val = next((h for h in hor if h["azimuthFrom"] <= sun_az < h["azimuthTo"]), None)
                if hor_val and hor_val["altitude"] > sun_alt:
                    eff_value *= hor_val.get("transparency", 0)

            ac, dc, total_rad, cell_temp = calc_radiation_model(
                dni, diffuse, shortwave, eff_value, al, cc, p_val, eff, inv, temp, tl
            )

            result = {
                "datetime": t_local.isoformat(),
                "power": ac,
                "dcPower": dc,
                "sunAzimuth": sun_az,
                "sunTilt": sun_alt,
                "temperature": temp
            }

            if debug:
                result.update({
                    "dni": dni,
                    "diffuse": diffuse,
                    "shortwave": shortwave,
                    "totalRadiation": total_rad,
                    "cellTemperature": cell_temp,
                    "efficiency": eff_value,
                    "sunVector": sun_vec.tolist(),
                    "pvVector": pv_vector.tolist()
                })

            if additional_fields:
                for field in additional_fields:
                    result[field] = row.get(field)

            results.append(result)

    return results
