import requests, math
import pandas as pd

LAT, LON = 55.7353, 12.1481          # Gundsømagle Kirke
START, END = "2015-01-01", "2024-12-31"

url = "https://opendataapi.dmi.dk/v2/climateData/collections/station/items"
params = {"bbox": "11.85,55.55,12.45,55.92", "limit": 1000}
feats = requests.get(url, params=params).json()["features"]

def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2-lat1)*p/2)**2 +
         math.cos(lat1*p)*math.cos(lat2*p)*math.sin((lon2-lon1)*p/2)**2)
    return 12742 * math.asin(math.sqrt(a))

rows = []
for f in feats:
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"][:2]
    rows.append({
        "stationId": p.get("stationId"),
        "name": p.get("name"),
        "type": p.get("type"),
        "status": p.get("status"),
        "from": p.get("operationFrom"),
        "to": p.get("operationTo"),
        "km": round(km(LAT, LON, lat, lon), 1),
    })

df = pd.DataFrame(rows).sort_values(["km", "from"])
# Keep stations that started before START and either are still running or ended after END
df["from"] = pd.to_datetime(df["from"], errors="coerce", utc=True)
df["to"] = pd.to_datetime(df["to"], errors="coerce", utc=True)
ok = (df["from"] <= pd.Timestamp(START, tz="UTC")) & \
     (df["to"].isna() | (df["to"] >= pd.Timestamp(END, tz="UTC")))
print(df[ok].drop_duplicates("stationId").to_string(index=False))