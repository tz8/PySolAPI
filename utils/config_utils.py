import json

def is_float(val):
    try:
        return isinstance(val, float) or (isinstance(val, int) and not isinstance(val, bool))
    except:
        return False

def is_int(val):
    try:
        return isinstance(val, int) and not isinstance(val, bool)
    except:
        return False

def validate_config(config):
    errors = []

    # Check latitude and longitude
    if "latitude" not in config or not is_float(config["latitude"]):
        errors.append("Missing or invalid latitude (must be float)")
    if "longitude" not in config or not is_float(config["longitude"]):
        errors.append("Missing or invalid longitude (must be float)")

    inverters = config.get("inverters", [])
    if not isinstance(inverters, list) or not inverters:
        errors.append("No inverters defined or inverters is not a list")
    for i, inverter in enumerate(inverters):
        if "size" not in inverter or not is_int(inverter["size"]):
            errors.append(f"Missing or invalid size for inverter {i} (must be int)")
        if "max_ac" in inverter and not is_int(inverter["max_ac"]):
            errors.append(f"Invalid max_ac for inverter {i} (must be int)")
        if "inverter_eff" in inverter and not is_float(inverter["inverter_eff"]):
            errors.append(f"Invalid inverter_eff for inverter {i} (must be float)")
        pv_strings = inverter.get("pv_strings", [])
        if not isinstance(pv_strings, list) or not pv_strings:
            errors.append(f"No pv_strings for inverter {i} or pv_strings is not a list")
        for j, pv in enumerate(pv_strings):
            if "azimuth" not in pv or not is_int(pv["azimuth"]):
                errors.append(f"Missing or invalid azimuth for inverter {i} pv_string {j} (must be int)")
            if "tilt" not in pv or not is_int(pv["tilt"]):
                errors.append(f"Missing or invalid tilt for inverter {i} pv_string {j} (must be int)")
            if "wp" not in pv or not is_int(pv["wp"]):
                errors.append(f"Missing or invalid wp for inverter {i} pv_string {j} (must be int)")
            if "albedo" in pv and not is_float(pv["albedo"]):
                errors.append(f"Invalid albedo for inverter {i} pv_string {j} (must be float)")
            if "cell_coeff" in pv and not is_float(pv["cell_coeff"]):
                errors.append(f"Invalid cell_coeff for inverter {i} pv_string {j} (must be float)")
    return errors
