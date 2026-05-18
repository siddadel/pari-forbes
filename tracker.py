import os
import requests
import pandas as pd
import smtplib

from email.message import EmailMessage

CSV_PATH = "latest.csv"

# -------------------------
# FETCH CURRENT DATA
# -------------------------

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    ),
    "Referer": "https://www.forbes.com/"
}

params = {
    "fields": (
        "personName,finalWorth,"
        "countryOfCitizenship,rank,source"
    ),
    "limit": 4000
}

r = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

data = r.json()

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

# -------------------------
# FIRST RUN
# -------------------------

if not os.path.exists(CSV_PATH):

    india_df.to_csv(CSV_PATH, index=False)

    print("Initial snapshot created.")

    exit()

# -------------------------
# LOAD PREVIOUS
# -------------------------

prev_df = pd.read_csv(CSV_PATH)

# Merge
merged = india_df.merge(
    prev_df,
    on="personName",
    how="outer",
    suffixes=("_new", "_old"),
    indicator=True
)

# -------------------------
# DETECT CHANGES
# -------------------------

added = merged[
    merged["_merge"] == "left_only"
]

removed = merged[
    merged["_merge"] == "right_only"
]

existing = merged[
    merged["_merge"] == "both"
].copy()

# Wealth change
existing["wealth_change"] = (
    existing["finalWorth_new"]
    - existing["finalWorth_old"]
)

# Rank change
existing["rank_change"] = (
    existing["rank_old"]
    - existing["rank_new"]
)

# Biggest gainers
top_gainers = existing.sort_values(
    by="wealth_change",
    ascending=False
).head(10)

# Biggest losers
top_losers = existing.sort_values(
    by="wealth_change",
    ascending=True
).head(10)

# Biggest rank jumps
top_rank_jumps = existing.sort_values(
    by="rank_change",
    ascending=False
).head(10)

# -------------------------
# BUILD HTML EMAIL
# -------------------------

html = """
<h2>India Billionaire Weekly Update</h2>
"""

if len(added):

    html += "<h3>New Entrants</h3><ul>"

    for _, row in added.iterrows():

        html += (
            f"<li>{row['personName']} "
            f"(${row['worth_billion_usd_new']}B)</li>"
        )

    html += "</ul>"

if len(removed):

    html += "<h3>Removed</h3><ul>"

    for _, row in removed.iterrows():

        html += (
            f"<li>{row['personName']}</li>"
        )

    html += "</ul>"

html += """
<h3>Top Wealth Gainers</h3>
<table border="1" cellpadding="5">
<tr>
<th>Name</th>
<th>Change ($M)</th>
</tr>
"""

for _, row in top_gainers.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>{row['wealth_change']:.0f}</td>"
        f"</tr>"
    )

html += "</table>"

html += """
<h3>Top Wealth Losers</h3>
<table border="1" cellpadding="5">
<tr>
<th>Name</th>
<th>Change ($M)</th>
</tr>
"""

for _, row in top_losers.iterrows():

    html += (
        f"<tr>"
        f"<td>{row['personName']}</td>"
        f"<td>{row['wealth_change']:.0f}</td>"
        f"</tr>"
    )

html += "</table>"

# -------------------------
# SAVE FILES
# -------------------------

india_df.to_csv(
    "latest.csv",
    index=False
)

india_df.to_excel(
    "latest.xlsx",
    index=False
)

# -------------------------
# SEND EMAIL
# -------------------------

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

# Attach CSV
with open("latest.csv", "rb") as f:

    msg.add_attachment(
        f.read(),
        maintype="text",
        subtype="csv",
        filename="latest.csv"
    )

# Attach XLSX
with open("latest.xlsx", "rb") as f:

    msg.add_attachment(
        f.read(),
        maintype=(
            "application"
        ),
        subtype=(
            "vnd.openxmlformats-"
            "officedocument."
            "spreadsheetml.sheet"
        ),
        filename="latest.xlsx"
    )

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