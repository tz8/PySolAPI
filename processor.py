import pandas as pd

def process_hourly_data(json_data):
    hourly = json_data.get("hourly", {})
    df = pd.DataFrame(hourly)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    return df
