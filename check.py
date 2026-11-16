"""
check.py – verifies dmi_gundsoemagle_2015-2024.csv against DMI's API.
Run after download.py. Ends with a summary of passed/failed checks.
"""
import requests
import pandas as pd

CSV = "dmi_gundsoemagle_2015-2024.csv"
URL = "https://opendataapi.dmi.dk/v2/climateData/collections/stationValue/items"
START, END = "2015-01-01", "2024-12-31"
WINDOW = "2014-12-31T23:00:00Z/2024-12-31T22:59:59Z"  # Danish local days, see README

results = []

def report(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def fetch(station, parameter, res, window):
    params = {"stationId": station, "parameterId": parameter, "timeResolution": res,
              "datetime": window, "limit": 10000}
    rows, url = [], URL
    while url:
        r = requests.get(url, params=params)
        r.raise_for_status()
        d = r.json()
        rows += [f["properties"] for f in d["features"]]
        url = next((l["href"] for l in d.get("links", []) if l["rel"] == "next"), None)
        params = None
    return pd.DataFrame(rows)

wide = pd.read_csv(CSV, index_col="date", parse_dates=["date"])

# --- 1. Dates -----------------------------------------------------------
print("== 1. Dates ==")
expected = pd.date_range(START, END, freq="D")
missing = expected.difference(wide.index)
extra = wide.index.difference(expected)
dups = int(wide.index.duplicated().sum())
report("All days present", len(missing) == 0, f"{len(missing)} missing" if len(missing) else "")
report("No days outside period", len(extra) == 0, f"{len(extra)} extra" if len(extra) else "")
report("No duplicate dates", dups == 0, f"{dups} duplicates" if dups else "")

# --- 2. Columns and gaps ------------------------------------------------
print("\n== 2. Columns ==")
main = ["mean_temp", "min_temp", "max_temp_w_date", "acc_precip",
        "mean_wind_speed", "mean_relative_hum", "bright_sunshine_06188"]
absent = [c for c in main if c not in wide]
report("Main columns present", not absent, ", ".join(absent))
leftover = [c for c in ["max_relative_hum", "min_relative_hum"] if c in wide]
report("Max/min humidity removed", not leftover, ", ".join(leftover))
gaps = {c: int(n) for c, n in wide[[c for c in main if c in wide]].isna().sum().items() if n}
report("No gaps in main columns", not gaps, str(gaps) if gaps else "")
other = wide.drop(columns=main, errors="ignore").isna().sum()
other = other[other > 0]
if not other.empty:
    print("  info: gaps in other columns:", other.to_dict())

# --- 3. Plausibility ----------------------------------------------------
print("\n== 3. Plausibility ==")
limits = {"mean_temp": (-30, 35), "min_temp": (-35, 30), "max_temp_w_date": (-25, 40),
          "acc_precip": (0, 150), "mean_wind_speed": (0, 40),
          "mean_relative_hum": (0, 100), "bright_sunshine_06188": (0, 17.5)}
for c, (lo, hi) in limits.items():
    if c in wide:
        s = wide[c].dropna()
        bad = int(((s < lo) | (s > hi)).sum())
        report(f"{c} within {lo} to {hi}", bad == 0,
               f"range {s.min()} to {s.max()}" + (f", {bad} outside" if bad else ""))

if {"min_temp", "mean_temp", "max_temp_w_date"} <= set(wide.columns):
    t = wide[["min_temp", "mean_temp", "max_temp_w_date"]].dropna()
    bad = int(((t.min_temp > t.mean_temp) | (t.mean_temp > t.max_temp_w_date)).sum())
    report("min <= mean <= max temperature", bad == 0, f"{bad} days" if bad else "")

m = wide["mean_temp"].groupby(wide.index.month).mean()
report("Seasonal cycle", m[7] > m[1] + 10, f"Jan {m[1]:.1f} °C, Jul {m[7]:.1f} °C")

# --- 4. Day boundaries (daily vs. summed hourly precipitation, 2023) ----
print("\n== 4. Day boundaries ==")
h = fetch("06170", "acc_precip", "hour", "2022-12-31T23:00:00Z/2023-12-31T22:59:59Z")
if h.empty:
    report("Daily values match hourly sums", False, "no hourly data returned")
else:
    t = pd.to_datetime(h["from"], format="ISO8601", utc=True)
    local_day = t.dt.tz_convert("Europe/Copenhagen").dt.tz_localize(None).dt.normalize()
    hourly = h["value"].groupby(local_day).sum()
    daily = wide.loc["2023", "acc_precip"]
    devs = {s: (daily - hourly.reindex(daily.index).shift(s)).abs().mean() for s in (-1, 0, 1)}
    best = min(devs, key=devs.get)
    report("Daily values match hourly sums on the same local day",
           best == 0 and devs[0] < 0.05,
           ", ".join(f"offset {s:+d}: {v:.2f} mm" for s, v in devs.items()))

# --- 5. Monthly values vs. DMI's own monthly figures --------------------
print("\n== 5. Monthly values ==")
for par, col, station, agg, tol in [
    ("mean_temp", "mean_temp", "06170", "mean", 0.1),
    ("acc_precip", "acc_precip", "06170", "sum", 1.0),
    ("bright_sunshine", "bright_sunshine_06188", "06188", "sum", 1.0),
]:
    mm = fetch(station, par, "month", WINDOW)
    if mm.empty:
        report(f"{col}: monthly values match DMI", False, "no monthly data returned")
        continue
    dmi = mm.assign(month=mm["from"].str[:7]).groupby("month")["value"].first()
    own = wide[col].groupby(wide.index.strftime("%Y-%m")).agg(agg)
    cmp = pd.DataFrame({"dmi": dmi, "own": own}).dropna()
    diff = (cmp["own"] - cmp["dmi"]).abs()
    known = {"bright_sunshine_06188": ["2023-04"]}   # see README
    off = cmp[(diff > tol) & ~cmp.index.isin(known.get(col, []))]
    report(f"{col}: monthly values match DMI", len(cmp) == 120 and off.empty,
           f"{len(cmp)} months, max deviation {diff.max():.2f}")
    if not off.empty:
        print(off.round(2))

# --- Summary ------------------------------------------------------------
failed = results.count(False)
print(f"\n{len(results) - failed} of {len(results)} checks passed"
      + ("" if failed == 0 else f", {failed} FAILED"))