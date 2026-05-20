import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from datetime import datetime

# -----------------------------
# Fetch Forbes data
# -----------------------------
st.title("History Page")

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

params = {
    "fields": (
        "personName,"
        "finalWorth,"
        "countryOfCitizenship,"
        "rank,"
        "source,"
        "industries,"
        "timestamp,"
        "date,"
        "city,"
        "gender,"
        "wealthHistory"
    ),
    "limit": 4000
}

headers = {
    "User-Agent": "Mozilla/5.0"
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
# Debugging output
# -----------------------------

# st.write("DEBUG: wealthHistory type")

# st.write(type(india_df.iloc[0]["wealthHistory"]))

# st.write("DEBUG: first wealthHistory entry")

# st.write(india_df.iloc[0]["wealthHistory"])
for i in india_df.iloc[0]["wealthHistory"].keys():
    st.write(i)
# st.write(india_df.iloc[0]["wealthHistory"].items())

# -----------------------------
# Plot all billionaires together
# -----------------------------

# TOP_N = 10

fig, ax = plt.subplots(figsize=(14, 7))

for _, row in india_df.iterrows():

    name = row["personName"]

    wealth_history = row.get("wealthHistory")

    if not wealth_history:
        continue

    dates = []
    values = []

    for point in wealth_history:
        p = point["lastDay"]
        # Adjust keys if needed after debugging
        ts = p.get("date")
        worth = p.get("value")

        if ts is None or worth is None:
            continue

        # Convert milliseconds timestamp
        dt = datetime.fromtimestamp(ts / 1000)

        dates.append(dt)

        values.append(worth)

    if len(dates) == 0:
        continue

    ax.plot(
        dates,
        values,
        label=name
    )

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