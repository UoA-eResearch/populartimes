#!/usr/bin/env python

from crawler import *
from util import *
from datetime import datetime, timedelta
import dateutil.parser
import time
from pprint import pprint

with open("data.geojson") as f:
    data = json.load(f)

try:
    for i, feature in enumerate(tqdm(data["features"])):
        p = feature["properties"]
        if p["populartimes"] and p["address"] and dateutil.parser.isoparse(p["scraped_at"]) < (datetime.now() - timedelta(days=2)):
            #print(p)
            #pprint_times(p["populartimes"])
            for retry in range(10):
                try:
                    result = get_populartimes_from_search(p["name"], p["address"])
                    popularity = result[2]
                    live_info = result[3]
                    break
                except Exception as e:
                    print(f"ERROR for {p}: {e}, retrying in 1s")
                    time.sleep(1)
            if popularity:
                popularity, wait_times = get_popularity_for_day(popularity)
                popularity = [day["data"] for day in popularity]
                # shift last element to first
                popularity = popularity[-1:] + popularity[:-1]
                #pprint_times(popularity)
                p["populartimes"] = popularity
                p["scraped_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
                if live_info:
                    p["live_info"] = {
                        "frequency": live_info,
                        # Store a timestamp here too, as it's possible to get popularity info without live_info in future runs
                        "scraped_at": p["scraped_at"]
                    }
                data["features"][i]["properties"] = p
except KeyboardInterrupt:
    print("Interrupted by user, will now save")
except Exception as e:
    print(f"ERROR: {e}")

with open("data.geojson", "w") as f:
    json.dump(data, f)
print(f"Wrote {len(data['features'])} places")
