#!/usr/bin/env python3

from util import *
import pandas as pd
from pprint import pprint

OUTFILE = "cafes.geojson"
features = {}
load(features, OUTFILE)

driver = initialise_driver()

for link in tqdm(features.keys()):
    feat = features[link]
    name = feat["properties"].get("name")
    driver.get(link)
    extract_place(driver, features, name, link)
    updated_feat = features[link]
    if feat["properties"]["address"] != updated_feat["properties"]["address"]:
        print(f'Updating address for {name} from {feat["properties"]["address"]} to {updated_feat["properties"]["address"]}')
        save(features, OUTFILE)

try:
    driver.close()
except:
    print("Unable to close webdriver")