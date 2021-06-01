#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from openlocationcode import openlocationcode as olc
from datetime import datetime
from tqdm import tqdm
import time
import re
import json
import os
import traceback

# gmaps starts their weeks on sunday
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
OUTFILE = "data.geojson"

# Initialise driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
driver.implicitly_wait(5)
driver.get("https://www.google.com/maps/search/place+of+interest/@-36.8508578,174.7615744,15z/data=!3m1!4b1")

def pprint_times(times):
    for i, day in enumerate(days):
        print(day, times[i])

features = []
seen_links = []

if os.path.isfile(OUTFILE):
    with open(OUTFILE) as f:
        data = json.load(f)
        features = data["features"]
        print(f"Loaded {len(features)} features")
        seen_links = [d["properties"]["link"] for d in features]

def extract_page():
    placesNeedsRefresh = True
    for i in tqdm(range(20)):
        scrollCount = 0
        if placesNeedsRefresh:
            places = []
            while len(places) < 20 and scrollCount < 10:
                scrollCount += 1
                #print("scrolling")
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element_by_css_selector("div[aria-label='Results for place of interest']"))
                time.sleep(1)
                places = driver.find_elements_by_css_selector("div[aria-label='Results for place of interest'] a[aria-label]")
            placesNeedsRefresh = False
        place = places[i]
        name = place.get_attribute('aria-label')
        link = place.get_attribute("href")
        if link in seen_links:
            print(f"Skipping {name}")
            continue
        print(f"Clicking on {name}")
        place.click()
        placesNeedsRefresh = True
        approx_ll = re.search(f'(?P<lat>-?\d+\.\d+).+?(?P<lng>-?\d+\.\d+)', link).groupdict()
        lat = float(approx_ll["lat"])
        lng = float(approx_ll["lng"])
        try:
            code = driver.find_element_by_css_selector("button[data-tooltip='Copy plus code']").text
            codeArea = olc.decode(olc.recoverNearest(code.split()[0], lat, lng))
            lat = codeArea.latitudeCenter
            lng = codeArea.longitudeCenter
        except NoSuchElementException:
            print("No plus code, latlong might be inaccurate")
            code = None
        address = None
        try:
            address = driver.find_element_by_css_selector("button[data-tooltip='Copy address']").get_attribute("aria-label").split(":")[-1].strip()
        except NoSuchElementException:
            pass
        live_info = None
        try:
            popular = driver.find_element_by_css_selector("div.section-popular-times")
            print("Has popular times")
            times = [[0]*24 for _ in range(7)] # 2D matrix, 7 days of the week, 24h per day
            dow = 0
            hour_prev = 0
            for elem in driver.find_elements_by_css_selector("div.section-popular-times-bar"):
                bits = elem.get_attribute("aria-label").split()
                if bits[0] == "%":
                    # Closed on this day
                    dow += 1
                elif bits[0] == "Currently":
                    hour += 1
                    live_info = {
                        "frequency": int(bits[1].rstrip("%")),
                        "hour": hour,
                        "day": days[dow % 7]
                    }
                    times[dow % 7][hour] = int(bits[-2].rstrip("%"))
                else:
                    am_pm = bits[-1]
                    hour = int(bits[-2])
                    if hour == 12:
                        hour = 0
                    if am_pm == "pm.":
                        hour += 12
                    if hour < hour_prev:
                        dow += 1
                    hour_prev = hour
                    times[dow % 7][hour] = int(bits[0].rstrip("%"))
            #pprint_times(times)
        except NoSuchElementException:
            print("No popular times available")
            times = None
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat]
            },
            "properties": {
                "name": name,
                "address": address,
                "link": link,
                "code": code,
                "live_info": live_info,
                "populartimes": times,
                "scraped_at": datetime.now().isoformat(sep=" ", timespec="seconds")
            }
        }
        #print(feature)
        features.append(feature)
        driver.find_element_by_xpath('//button/span[text()="Back to results"]').click()

retry = 0
while True:
    try:
        extract_page()
        try:
            driver.find_element_by_css_selector("button[aria-label=' Next page ']").click()
            print("Going to next page")
        except NoSuchElementException:
            print("All done!")
            break
        except ElementClickInterceptedException:
            retry += 1
            if retry > 5:
                raise
            else:
                time.sleep(1)
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        with open("error.html", "w") as f:
            f.write(driver.page_source)
        break

print(f"Extracted {len(features)} places")
driver.close()

if features:
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(OUTFILE, "w") as f:
        json.dump(geojson, f)