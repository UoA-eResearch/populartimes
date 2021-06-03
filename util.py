#!/usr/bin/env python

from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from openlocationcode import openlocationcode as olc
from tqdm import tqdm
import json
import time
import re
import os

# gmaps starts their weeks on sunday
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def initialise_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def pprint_times(times):
    for i, day in enumerate(days):
        print(day, times[i])

def click(driver, elem):
    try:
        elem.click()
    except:
        driver.execute_script("arguments[0].click();", elem)

def extract_place(driver, features, name, link):
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
    category = None
    try:
        category = driver.find_element_by_css_selector("button[jsaction='pane.rating.category']").text
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
            "category": category,
            "link": link,
            "code": code,
            "live_info": live_info,
            "populartimes": times,
            "scraped_at": datetime.now().isoformat(sep=" ", timespec="seconds")
        }
    }
    #print(feature)
    features[link] = feature

def extract_page(driver, features):
    placesNeedsRefresh = True
    for i in tqdm(range(20)):
        try:
            # multiple results
            # Only refresh places if necessary. This is more efficient when skipping over already extracted places
            if placesNeedsRefresh:
                places = []
                scrollCount = 0
                while len(places) < 20 and scrollCount < 10:
                    scrollCount += 1
                    print("scrolling")
                    driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element_by_css_selector("div[aria-label^='Results for']"))
                    time.sleep(1)
                    places = driver.find_elements_by_css_selector("div[aria-label^='Results for'] a[aria-label]")
                if not places:
                    print("No places")
                    raise IndexError
                placesNeedsRefresh = False
            place = places[i]
            name = place.get_attribute('aria-label')
            link = place.get_attribute("href")
            if link in features:
                print(f"Skipping {name}")
                continue
            print(f"Clicking on {name}")
            click(driver, place)
            placesNeedsRefresh = True
            extract_place(driver, features, name, link)
            for retry in range(5):
                try:
                    driver.find_element_by_xpath('//button/span[text()="Back to results"]').click()
                    break
                except:
                    print(retry)
                    if retry == 4:
                        raise
                    else:
                        time.sleep(retry)
        except NoSuchElementException:
            # Single result
            try:
                name = driver.find_element_by_css_selector("h1[class*='header-title-title']").text
                if name:
                    print(f"Found {name}")
                    link = driver.current_url
                    if link in features:
                        print(f"Skipping {name}")
                    else:
                        extract_place(driver, features, name, link)
            except:
                pass
            raise IndexError

def load(features, OUTFILE):
    if os.path.isfile(OUTFILE):
        # Load existing data
        with open(OUTFILE) as f:
            data = json.load(f)
            for feature in data["features"]:
                features[feature["properties"]["link"]] = feature
            print(f"Loaded {len(features)} features")

def save(features, OUTFILE):
    if features:
        geojson = {
            "type": "FeatureCollection",
            "features": list(features.values())
        }

        with open(OUTFILE, "w") as f:
            json.dump(geojson, f)
        print(f"Wrote {len(features)} places")