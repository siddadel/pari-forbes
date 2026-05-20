import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

st.title("Live Indian Billionaires CSV")

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"


# dict_keys(['naturalId', 'name', 'year', 'uri', 'rank', 'listUri', 
# 'visible', 'position', 'imageExists', 'bio', 'finalWorth', 'person', 'personName', 
# 'state', 'city', 'source', 'industries', 
# 'countryOfCitizenship', 'timestamp', 'version', 
# 'selfMade', 'gender', 'birthDate', 'lastName', 'financialAssets', 
# 'date', 'wealthList', 'estWorthPrev', 'privateAssetsWorth', 
# 'familyList', 'interactive', 'selfMadeRank', 'archivedWorth', 'thumbnail', 'squareImage', 'bioSuppress', 
# 'csfDisplayFields', 'bios', 'abouts', 'philanthropyScore', 'wealthHistory'])
params = {
    "fields": "personName,finalWorth,countryOfCitizenship,rank,source,industries,timestamp,date,city,gender",
    "limit": 4000
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(url, params=params, headers=headers)

data = r.json()

people = data["personList"]["personsLists"]

df = pd.DataFrame(people)

india_df = df[df["countryOfCitizenship"] == "India"]

india_df = india_df.sort_values(
    by="finalWorth",
    ascending=False
)

india_df['billions'] =  india_df['finalWorth']/1000
india_df['time'] = df["timestamp"].apply(
    lambda ts: (
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        .astimezone(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        if pd.notnull(ts) else None
    )
)

india_df['date-correct'] = df["date"].apply(
    lambda ts: (
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        .astimezone(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        if pd.notnull(ts) else None
    )
)



csv = india_df.to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="india_billionaires.csv",
    mime="text/csv"
)

st.dataframe(india_df)
