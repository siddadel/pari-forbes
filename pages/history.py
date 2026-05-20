import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# -----------------------------
# Fetch Forbes data
# -----------------------------
st.title("History Page")

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

params = {
    "fields": "personName,finalWorth,countryOfCitizenship,rank,source,industries,timestamp,date,city,gender,wealthHistory",
    "limit": 4000
}

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


r = requests.get(url, params=params, headers=headers)

data = r.json()

people = data["personList"]["personsLists"]

df = pd.DataFrame(people)

# -----------------------------
# Filter India
# -----------------------------

india_df = df[df["countryOfCitizenship"] == "India"]

india_df = india_df.sort_values(
    by="finalWorth",
    ascending=False
)

# -----------------------------
# Plot all billionaires together
# -----------------------------


fig, axes = plt.subplots(
    nrows=10,
    ncols=2,
    figsize=(16, 20)
)

axes = axes.flatten()

# -----------------------------
# Plot each billionaire
# -----------------------------

for ax, (_, row) in zip(axes, india_df.head(20).iterrows()):
    name = row["personName"]

    wealth_history = row.get("wealthHistory")

    if not wealth_history:
        continue

    dates = []
    values = []

    for item in wealth_history.items():
        points = item[1]
        for point in points:
            # Adjust keys if needed after debugging
            ts = point.get("date")
            worth = point.get("value")

            if ts is None or worth is None:
                continue

            # Convert milliseconds timestamp
            # dt = datetime.fromtimestamp(ts / 1000)
        
            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).\
                    astimezone(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None).\
                    strftime("%Y-%m-%d %H")

            dates.append(dt)

            values.append(worth)

    if len(dates) == 0:
        continue


    ax.plot(dates, values)

    ax.set_title(name)

    ax.grid(True)
# -----------------------------
# Graph formatting
# -----------------------------

ax.set_title("Wealth History of Indian Billionaires")

ax.set_xlabel("Date")

ax.set_ylabel("Net Worth")

ax.legend()

ax.grid(True)

fig.autofmt_xdate()

# -----------------------------
# Display in Streamlit
# -----------------------------

st.pyplot(fig)