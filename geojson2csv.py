#!/usr/bin/env python

import json
import csv
with open("data.geojson") as f:
    data = json.load(f)
with open('data.csv', 'w') as csvfile:
    headers = list(data["features"][0]["properties"].keys()) + ["lat", "lng"]
    print(headers)
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()
    for f in data["features"]:
        p = f["properties"]
        p["lng"] = f["geometry"]["coordinates"][0]
        p["lat"] = f["geometry"]["coordinates"][1]
        writer.writerow(p)
print("Done")
