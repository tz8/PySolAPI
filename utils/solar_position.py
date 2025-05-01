from astral import LocationInfo, Observer
from astral.sun import azimuth, elevation
import numpy as np

def deg_to_rad(deg):
    return deg * np.pi / 180

def get_sun_position(lat, lon, dt):
    observer = Observer(latitude=lat, longitude=lon)
    az = azimuth(observer, dateandtime=dt)
    alt = elevation(observer, dateandtime=dt)
    return az, alt

def vector_from_angles(azimuth_deg, tilt_deg):
    az = deg_to_rad(azimuth_deg)
    tilt = deg_to_rad(tilt_deg)
    return np.array([
        np.sin(az) * np.cos(tilt),
        np.cos(az) * np.cos(tilt),
        np.sin(tilt)
    ])

def dot_product_efficiency(sun_vec, panel_vec):
    return max(0.0, np.dot(sun_vec, panel_vec))
