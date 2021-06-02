#!/usr/bin/env python3

from util import *
import pandas as pd

OUTFILE = "data.geojson"
df = pd.read_csv("locations.csv")
df = df[df.TA2021_V1_00_NAME == "Auckland"]
print(f"Have {len(df)} locations")
locations = iter(tqdm(df.SA22021_V1_00_NAME_ASCII))

driver = initialise_driver()
location = next(locations)
location_type = 'place of interest'
search = f"{location_type} in {location}, Auckland"
print(search)
driver.get(f"https://www.google.com/maps/search/{search}")

features = {}
load(features, OUTFILE)

while True:
    try:
        extract_page(driver, features)
        if driver.find_element_by_css_selector("button[aria-label=' Next page ']").get_attribute("disabled"):
            raise IndexError
        click(driver, driver.find_element_by_css_selector("button[aria-label=' Next page ']"))
        print("Going to next page")
        time.sleep(2)
    except IndexError:
        try:
            next_page = driver.find_element_by_css_selector("button[aria-label=' Next page ']")
        except:
            next_page = None
        if not next_page or next_page.get_attribute("disabled"):
            print("All done!")
            save(features, OUTFILE)
            # Record that we've scraped this location
            df.scraped_at[df.SA22021_V1_00_NAME_ASCII == location] = pd.Timestamp.now()
            df.to_csv("locations.csv", index=False)
            location = next(locations)
            search = f"{location_type} in {location}, Auckland"
            print(search)
            driver.get(f"https://www.google.com/maps/search/{search}")
        else:
            print("Got an IndexError, but there's more pages...")
            next_page.click()
    except KeyboardInterrupt:
        print("Interrupted by user, will now save")
        break
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        with open("error.html", "w") as f:
            f.write(driver.page_source)
        break

save(features, OUTFILE)

try:
    driver.close()
except:
    print("Unable to close webdriver")