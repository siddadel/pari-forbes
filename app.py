import requests
import pandas as pd

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

print(
    india_df[
        ["personName", "finalWorth", "source"]
    ].head(20)
)