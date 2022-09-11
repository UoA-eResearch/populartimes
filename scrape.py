#!/usr/bin/env python3

from util import *
import pandas as pd

OUTFILE = "data.geojson"
df = pd.read_csv("locations.csv")
# Ignore locations that have already been scraped
locations = df.name[pd.isna(df.scraped_at)]
print(f"Have {len(locations)} locations")
locations = iter(tqdm(locations))

driver = initialise_driver()
location = next(locations)
location_type = 'place of interest'
search = f"{location_type} in {location}"
print(search)
driver.get(f"https://www.google.com/maps/search/{search}?hl=en")

features = {}
load(features, OUTFILE)

while True:
    try:
        extract_page(driver, features)
        print(f"Got all places for {location}")
        save(features, OUTFILE)
        # Record that we've scraped this location
        df.scraped_at[df.name == location] = pd.Timestamp.now()
        df.to_csv("locations.csv", index=False)
        try:
            location = next(locations)
        except StopIteration:
            print("All locations complete")
            break
        search = f"{location_type} in {location}"
        print(search)
        driver.get(f"https://www.google.com/maps/search/{search}?hl=en")
    except KeyboardInterrupt:
        print("Interrupted by user, will now save")
        break
    except Exception as e:
        # Some other Exception - try reload the whole page and start over
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        with open("error.html", "w") as f:
            f.write(driver.page_source)
        # Restart
        driver.get(f"https://www.google.com/maps/search/{search}?hl=en")

save(features, OUTFILE)

try:
    driver.close()
except:
    print("Unable to close webdriver")