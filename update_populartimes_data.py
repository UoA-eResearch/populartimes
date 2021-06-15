#!/usr/bin/env python

from crawler import *
from util import *
from pprint import pprint

with open("data.geojson") as f:
    data = json.load(f)

for i, feature in enumerate(tqdm(data["features"])):
    if feature["properties"]["populartimes"] and feature["properties"]["address"]:
        p = feature["properties"]
        #pprint_times(p["populartimes"])
        popularity = get_populartimes_from_search(p["name"], p["address"])[2]
        if popularity:
            popularity, wait_times = get_popularity_for_day(popularity)
            popularity = [day["data"] for day in popularity]
            # shift last element to first
            popularity = popularity[-1:] + popularity[:-1]
            #pprint_times(popularity)
            p["populartimes"] = popularity
            p["scraped_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
            data["features"][i]["properties"] = p

with open("data.geojson", "w") as f:
    json.dump(data, f)
print(f"Wrote {len(data['features'])} places")