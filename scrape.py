#!/usr/bin/env python3

from util import *
import pandas as pd

OUTFILE = "cafes.geojson"
df = pd.read_csv("locations.csv")
# Ignore locations that have already been scraped
locations = df.name[df.n_places.isna()]
print(f"Have {len(locations)} locations")
locations = iter(tqdm(locations))

driver = initialise_driver()
location = next(locations)
location_type = 'cafes'
search = f"{location_type} in {location}"
print(search)
url = f"https://www.google.com/maps/search/{search}?hl=en"
print(url)
driver.get(url)

features = {}
load(features, OUTFILE)

while True:
    try:
        n_places = extract_page(driver, features)
        print(f"Got {n_places} places for {location}")
        save(features, OUTFILE)
        # Record that we've scraped this location
        df.scraped_at[df.name == location] = pd.Timestamp.now()
        df.n_places[df.name == location] = n_places
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
        try:
            with open("error.html", "w") as f:
                f.write(driver.page_source)
                driver.save_screenshot("error.png")
        except:
            print("can't even write error.html...")
        # Restart
        driver.get(f"https://www.google.com/maps/search/{search}?hl=en")

save(features, OUTFILE)

try:
    driver.close()
except:
    print("Unable to close webdriver")