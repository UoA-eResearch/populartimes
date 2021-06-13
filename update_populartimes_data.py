#!/usr/bin/env python

from crawler import *
from util import *
from pprint import pprint
import json
from tqdm import tqdm

with open("data.geojson") as f:
    data = json.load(f)

features = [f for f in data["features"] if f["properties"]["populartimes"] and f["properties"]["address"]]

for feature in tqdm(features):
    p = feature["properties"]
    print(p)
    print(pprint_times(p["populartimes"]))
    popularity = get_populartimes_from_search(p["name"], p["address"])[2]
    popularity, wait_times = get_popularity_for_day(popularity)
    popularity = [day["data"] for day in popularity]
    # shift last element to first
    popularity = popularity[-1:] + popularity[:-1] 
    print(pprint_times(popularity))
    break