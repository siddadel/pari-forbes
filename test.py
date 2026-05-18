import os
import time
import smtplib
import requests
import pandas as pd

from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).parent

SNAPSHOT_DIR = BASE_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

LATEST_CSV = BASE_DIR / "latest.csv"
LATEST_XLSX = BASE_DIR / "latest.xlsx"

SIGNIFICANT_CHANGE_MILLIONS = 500  # $500M threshold

# =========================================================
# FETCH LIVE FORBES DATA
# =========================================================

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.forbes.com/",
    "Accept": "application/json,text/plain,*/*"
}

params = {
    "fields": (
        "personName,"
        "finalWorth,"
        "countryOfCitizenship,"
        "rank,"
        "source,"
        "timestamp"
    ),
    "limit": 4000
}

data = None

for attempt in range(3):

    try:

        print(f"Fetch attempt {attempt + 1}")

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        break

    except Exception as e:

        print(f"Fetch failed: {e}")

        if attempt < 2:
            time.sleep(5)

if data is None:
    raise Exception("Could not fetch Forbes data.")


print(data)
