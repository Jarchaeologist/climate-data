# DMI climate data – Gundsømagle Kirke

Downloads 10 years (2015–2024) of daily, quality-controlled climate data from
DMI's Climate Data API for the area around Gundsømagle Kirke (55.735°N, 12.148°E).
Only station data is used, no interpolated values.
See also
https://wetterdienst.readthedocs.io/en/latest/data/provider/dmi/observation/index.html
and URL
https://opendataapi.dmi.dk/v2/climateData/

## Requirements

- Python 3 with `requests` and `pandas`
- No API key needed

## Scripts

Run them in this order:

1. **`nearest_station.py`** – lists DMI stations within `RADIUS_KM` (default
   25 km) of the location that were in operation for the whole period, sorted
   by distance. For another location: change `LAT, LON`.
2. **`coverage.py`** – checks how many days of data each candidate station has
   for selected parameters (complete = 3,653 days for 2015–2024).
   For other stations: change the station IDs in `stations`.
3. **`download.py`** – downloads the daily data and saves it as CSV.
   For other stations: change the station IDs in the `fetch(...)` calls and the
   CSV filenames.
4. **`check.py`** (optional) – verifies the downloaded file: dates, gaps,
   plausible values, day boundaries, and monthly values against DMI's own
   figures. Should end with all checks passed. Only needed after a new
   download. It is written for the stations below and needs adapting for others.

## Stations used

| Station | Name              | Distance | Used for            |
|---------|-------------------|----------|---------------------|
| 06170   | Roskilde Lufthavn | 16.5 km  | All parameters      |
| 06188   | Sjælsmark         | 22.8 km  | Sunshine hours only |

Roskilde Lufthavn does not measure sunshine hours, so `bright_sunshine` is taken
from Sjælsmark and stored in a separate column, `bright_sunshine_06188`.

## Output

- `dmi_gundsoemagle_2015-2024.csv` – standard CSV (comma-separated, decimal point)
- `dmi_gundsoemagle_2015-2024_excel.csv` – for Danish Excel (semicolon, decimal comma)

One row per day (3,653 days), one column per parameter (15 columns).

## Dates – read this before changing the period

DMI labels daily values by **Danish local time** (a day runs midnight to
midnight Danish time), but the `datetime` filter in the API request is in
**UTC**. Midnight in Danish winter time is 23:00 UTC the day before.

So `download.py` and `check.py` use this window to get 1 Jan 2015 – 31 Dec 2024:

    "datetime": "2014-12-31T23:00:00Z/2024-12-31T22:59:59Z"

A plain UTC window (`2015-01-01T00:00:00Z/2024-12-31T23:59:59Z`) silently
shifts the period by one day: 1 Jan 2015 is missing and 1 Jan 2025 is included,
while the row count is still 3,653.

If you change the period:

- Start/end in winter (CET): subtract 1 hour → `T23:00:00Z` the day before.
- Start/end in summer (CEST): subtract 2 hours → `T22:00:00Z` the day before.
- The dates in the file are taken from the first 10 characters of DMI's `from`
  field. Do not convert to UTC, as that moves every value one day back.
- In `check.py`, also update `START`, `END`, `WINDOW` and `CSV` at the top.

`coverage.py` still uses the plain UTC window. That is fine for counting days,
but don't reuse it for downloading.

## Data quality

Verified with `check.py` (all 19 checks passed): complete dates (no missing,
extra or duplicate days), plausible values, daily values match summed hourly
values on Danish local days, and monthly means/totals match DMI's own monthly
values.

- `max_relative_hum` and `min_relative_hum` are removed in `download.py`
  (no data after September 2018). `mean_relative_hum` covers the full period.
- `max_precip_30m` is empty on some days.
- `max_temp_w_date` may carry the time of the maximum in its timestamp; only
  the date part is used.
- Sunshine (Sjælsmark, 06188), April 2023: the daily values sum to 259.7 h,
  while DMI's monthly value for the same station is 256.3 h. All other months
  match. This is a minor inconsistency in DMI's own data and is treated as a
  known exception in `check.py`.

## Source and license

Data © DMI (Danish Meteorological Institute), licensed under CC BY 4.0.
Credit DMI when the data is published.
API documentation: https://www.dmi.dk/friedata/dokumentation/apis/climate-data-api-1
