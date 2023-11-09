#!/usr/bin/env python3

from util import *
import pandas as pd
from pprint import pprint

OUTFILE = "cafes.geojson"
features = {}
load(features, OUTFILE)

driver = initialise_driver()

links_to_click = [k for k in features.keys() if features[k]["properties"]["scraped_at"] < "2023-11-09"]

for i, link in enumerate(tqdm(links_to_click)):
    feat = features[link]
    name = feat["properties"].get("name")
    driver.get(link)
    try:
        extract_place(driver, features, name, link)
    except:
        print(f"Unable to extract {name}")
    updated_feat = features[link]
    if feat["properties"]["address"] != updated_feat["properties"]["address"]:
        print(f'Updating address for {name} from {feat["properties"]["address"]} to {updated_feat["properties"]["address"]}')
    if i % 100 == 0:
        save(features, OUTFILE)

try:
    driver.close()
except:
    print("Unable to close webdriver")
save(features, OUTFILE)