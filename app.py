import requests
import pandas as pd
import streamlit as st

st.title("Live Indian Billionaires CSV")

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

params = {
    "fields": "personName,finalWorth,countryOfCitizenship,source",
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

csv = india_df.to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="india_billionaires.csv",
    mime="text/csv"
)

st.dataframe(india_df)