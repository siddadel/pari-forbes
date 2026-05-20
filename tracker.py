import os
import time
import smtplib
import requests
import pandas as pd

from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
        "timestamp",
        "industries",
        "city",
        "gender"
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

# =========================================================
# PARSE DATA
# =========================================================

people = data["personList"]["personsLists"]

df = pd.DataFrame(people)

india_df = df[
    df["countryOfCitizenship"] == "India"
].copy()

india_df = india_df.sort_values(
    by="finalWorth",
    ascending=False
)

india_df["worth_billion_usd"] = (
    india_df["finalWorth"] / 1000
).round(2)

india_df['time'] = df["timestamp"].apply(
    lambda ts: (
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        .astimezone(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        if pd.notnull(ts) else None
    )
)

india_df.reset_index(drop=True, inplace=True)

# =========================================================
# SAVE DATED SNAPSHOT
# =========================================================

today = datetime.utcnow().strftime("%Y-%m-%d")

dated_snapshot = SNAPSHOT_DIR / f"{today}.csv"

india_df.to_csv(
    dated_snapshot,
    index=False
)

# =========================================================
# FIRST RUN
# =========================================================

if not LATEST_CSV.exists():

    india_df.to_csv(LATEST_CSV, index=False)

    india_df.to_excel(LATEST_XLSX, index=False)

    print("Initial snapshot created.")

    exit()

# =========================================================
# LOAD PREVIOUS SNAPSHOT
# =========================================================

previous_df = pd.read_csv(LATEST_CSV)

# =========================================================
# MERGE DATASETS
# =========================================================

merged = india_df.merge(
    previous_df,
    on="personName",
    how="outer",
    suffixes=("_new", "_old"),
    indicator=True
)

# =========================================================
# DETECT ADDED / REMOVED
# =========================================================

added = merged[
    merged["_merge"] == "left_only"
]

removed = merged[
    merged["_merge"] == "right_only"
]

existing = merged[
    merged["_merge"] == "both"
].copy()

# =========================================================
# WEALTH + RANK CHANGES
# =========================================================

existing["wealth_change"] = (
    existing["finalWorth_new"]
    - existing["finalWorth_old"]
)

existing["wealth_change_billion"] = (
    existing["wealth_change"] / 1000
).round(2)

existing["rank_change"] = (
    existing["rank_old"]
    - existing["rank_new"]
)

# =========================================================
# SIGNIFICANT MOVERS
# =========================================================

significant = existing[
    existing["wealth_change"].abs()
    >= SIGNIFICANT_CHANGE_MILLIONS
]

top_gainers = existing[existing["wealth_change"]>0].sort_values(
    by="wealth_change",
    ascending=False
).head(10)

top_losers = existing[existing["wealth_change"]<0].sort_values(
    by="wealth_change",
    ascending=True
).head(10)

top_rank_jumps = existing.sort_values(
    by="rank_change",
    ascending=False
).head(10)

# =========================================================
# BUILD HTML EMAIL
# =========================================================

html = f"""
<h1>India Billionaire Weekly Update</h1>

<p>
Generated:
{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
</p>
"""

# ---------------------------------------------------------
# NEW ENTRANTS
# ---------------------------------------------------------

if len(added):

    html += "<h2>New Entrants</h2><ul>"

    for _, row in added.iterrows():

        html += (
            f"<li>"
            f"{row['personName']} "
            f"(${row['worth_billion_usd_new']}B)"
            f"</li>"
        )

    html += "</ul>"

# ---------------------------------------------------------
# REMOVED
# ---------------------------------------------------------

if len(removed):

    html += "<h2>Removed</h2><ul>"

    for _, row in removed.iterrows():

        html += (
            f"<li>{row['personName']}, Old Wealth: {row['wealth_change_old']}, New Wealth: {row['wealth_change_new']}</td>"
        )

    html += "</ul>"

# ---------------------------------------------------------
# TOP GAINERS
# ---------------------------------------------------------

html += """
<h2>Top Wealth Gainers</h2>

<table border="1" cellpadding="6" cellspacing="0">
<tr>
<th>Name</th>
<th>Change ($B)</th>
<th>Old Wealth</th>
<th>New Wealth</th>
</tr>
"""

for _, row in top_gainers.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>+{row['wealth_change_billion']}</td>"
        f"<td>{row['wealth_change_old']}</td>"
        f"<td>{row['wealth_change_new']}</td>"
        f"</tr>"
    )

html += "</table>"

# ---------------------------------------------------------
# TOP LOSERS
# ---------------------------------------------------------

html += """
<h2>Top Wealth Losers</h2>

<table border="1" cellpadding="6" cellspacing="0">
<tr>
<th>Name</th>
<th>Change ($B)</th>
<th>Old Wealth</th>
<th>New Wealth</th>
</tr>
"""

for _, row in top_losers.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>{row['wealth_change_billion']}</td>"
        f"<td>{row['wealth_change_old']}</td>"
        f"<td>{row['wealth_change_new']}</td>"
        f"</tr>"
    )

html += "</table>"

# ---------------------------------------------------------
# RANK JUMPS
# ---------------------------------------------------------

html += """
<h2>Largest Rank Improvements</h2>

<table border="1" cellpadding="6" cellspacing="0">
<tr>
<th>Name</th>
<th>Rank Change</th>
<th>Old</th>
<th>New</th>
</tr>
"""

for _, row in top_rank_jumps.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>{row['rank_change']}</td>"
        f"<td>{row["rank_old"]}</td>"
        f"<td>{row["rank_new"]}</td>"
        f"</tr>"
    )

html += "</table>"


# ---------------------------------------------------------
# ALL CHANGES
# ---------------------------------------------------------

html += """
<h2>All Billionares</h2>

<table border="1" cellpadding="6" cellspacing="0">
<tr>
<th>Name</th>
<th>Change ($B)</th>
</tr>
"""

for _, row in existing.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>{row['wealth_change_billion']}</td>"
        f"</tr>"
    )

html += "</table>"

# =========================================================
# ONLY SEND EMAIL IF THERE ARE CHANGES
# =========================================================

has_changes = (
    len(added)
    or len(removed)
    or len(significant)
)

if has_changes:

    msg = EmailMessage()

    msg["Subject"] = (
        "India Billionaire Weekly Changes"
    )

    msg["From"] = os.environ["EMAIL_ADDRESS"]

    msg["To"] = os.environ["RECIPIENT"]

    msg.set_content(
        "HTML email not supported."
    )

    msg.add_alternative(
        html,
        subtype="html"
    )

    # -----------------------------------------------------
    # ATTACH CSV
    # -----------------------------------------------------

    india_df.to_csv(
        LATEST_CSV,
        index=False
    )

    with open(LATEST_CSV, "rb") as f:

        msg.add_attachment(
            f.read(),
            maintype="text",
            subtype="csv",
            filename="latest.csv"
        )

    # -----------------------------------------------------
    # ATTACH XLSX
    # -----------------------------------------------------

    india_df.to_excel(
        LATEST_XLSX,
        index=False
    )

    with open(LATEST_XLSX, "rb") as f:

        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype=(
                "vnd.openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),
            filename="latest.xlsx"
        )

    # -----------------------------------------------------
    # SEND EMAIL
    # -----------------------------------------------------

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            os.environ["EMAIL_ADDRESS"],
            os.environ["EMAIL_PASSWORD"]
        )

        smtp.send_message(msg)

    print("Email sent.")

else:

    print("No significant changes detected.")

# =========================================================
# UPDATE LATEST SNAPSHOT
# =========================================================

india_df.to_csv(
    LATEST_CSV,
    index=False
)

india_df.to_excel(
    LATEST_XLSX,
    index=False
)

print("Snapshots updated.")