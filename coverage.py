import requests

START, END = "2015-01-01", "2024-12-31"
URL = "https://opendataapi.dmi.dk/v2/climateData/collections/stationValue/items"

stations = ["06170", "06188"]                      # Roskilde Lufthavn, Sjælsmark
parameters = ["mean_temp", "acc_precip", "mean_wind_speed", "bright_sunshine"]

for st in stations:
    for par in parameters:
        r = requests.get(URL, params={
            "stationId": st,
            "parameterId": par,
            "timeResolution": "day",
            "datetime": f"{START}T00:00:00Z/{END}T23:59:59Z",
            "limit": 10000,
        })
        r.raise_for_status()
        n = len(r.json()["features"])
        print(f"{st}  {par:<16} {n:>5} of ~3653 days")