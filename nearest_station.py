import requests, math
import pandas as pd

LAT, LON = 55.7353, 12.1481          # Gundsømagle Kirke
RADIUS_KM = 25                       # search radius
START, END = "2015-01-01", "2024-12-31"

# Search area calculated from the coordinates (1° latitude ≈ 111 km)
dlat = RADIUS_KM / 111
dlon = RADIUS_KM / (111 * math.cos(math.radians(LAT)))
bbox = f"{LON - dlon:.4f},{LAT - dlat:.4f},{LON + dlon:.4f},{LAT + dlat:.4f}"

url = "https://opendataapi.dmi.dk/v2/climateData/collections/station/items"
r = requests.get(url, params={"bbox": bbox, "limit": 1000})
r.raise_for_status()
feats = r.json()["features"]

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

df = pd.DataFrame(rows)
df["from"] = pd.to_datetime(df["from"], errors="coerce", utc=True)
df["to"] = pd.to_datetime(df["to"], errors="coerce", utc=True)
df = df.sort_values(["km", "from"])

# Keep stations within the radius that started before START
# and either are still running or ended after END
ok = (df["km"] <= RADIUS_KM) & \
     (df["from"] <= pd.Timestamp(START, tz="UTC")) & \
     (df["to"].isna() | (df["to"] >= pd.Timestamp(END, tz="UTC")))
print(df[ok].drop_duplicates("stationId").to_string(index=False))