import requests
import pandas as pd

START, END = "2015-01-01", "2024-12-31"
URL = "https://opendataapi.dmi.dk/v2/climateData/collections/stationValue/items"

def fetch(station, parameter=None):
    params = {
        "stationId": station,
        "timeResolution": "day",
        "datetime": "2014-12-31T23:00:00Z/2024-12-31T22:59:59Z",
        "limit": 10000,
    }
    if parameter:
        params["parameterId"] = parameter
    rows, url = [], URL
    while url:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        rows += [f["properties"] for f in data["features"]]
        url = next((l["href"] for l in data.get("links", []) if l["rel"] == "next"), None)
        params = None  # the next link already includes the parameters
    return pd.DataFrame(rows)

# All parameters from Roskilde Lufthavn + sunshine from Sjælsmark
df = pd.concat([
    fetch("06170"),
    fetch("06188", "bright_sunshine").assign(parameterId="bright_sunshine_06188"),
])

df["date"] = pd.to_datetime(df["from"].str[:10])
wide = df.pivot_table(index="date", columns="parameterId", values="value", aggfunc="first")

wide.to_csv("dmi_gundsoemagle_2015-2024.csv")                          # standard CSV
wide.to_csv("dmi_gundsoemagle_2015-2024_excel.csv", sep=";", decimal=",")  # Danish Excel
print(wide.shape)
print(wide.head())
