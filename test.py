import requests
import json

url = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"

r = requests.get(url)
data = r.json()

person = data["personList"]["personsLists"][0]

print(person.keys())