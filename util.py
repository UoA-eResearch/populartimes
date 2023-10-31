#!/usr/bin/env python

from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
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
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.implicitly_wait(5)
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
    try:
        approx_ll = re.search(f'(?P<lat>-?\d+\.\d+).+?(?P<lng>-?\d+\.\d+)', link).groupdict()
        lat = float(approx_ll["lat"])
        lng = float(approx_ll["lng"])
    except AttributeError:
        print(f"No approx latlong in URL {link} for {name}")
        return
    try:
        code = driver.find_element(By.CSS_SELECTOR, "button[aria-label^='Plus code:']").text
        print(f"Plus code: {code}")
        codeArea = olc.decode(olc.recoverNearest(code.split()[0], lat, lng))
        lat = codeArea.latitudeCenter
        lng = codeArea.longitudeCenter
    except NoSuchElementException:
        print("No plus code, latlong might be inaccurate")
        code = None
    except StaleElementReferenceException:
        # Try again
        print("Got a StaleElementReferenceException when trying to get the plus code, trying again")
        time.sleep(.1)
        return extract_place(driver, features, name, link)
    driver.implicitly_wait(.1)
    address = None
    try:
        address = driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy address']").get_attribute("aria-label").split(":")[-1].strip()
    except NoSuchElementException:
        pass
    category = None
    try:
        category = driver.find_element(By.CSS_SELECTOR, "button[jsaction='pane.rating.category']").text
    except NoSuchElementException:
        pass
    live_info = None
    try:
        popular = driver.find_element(By.CSS_SELECTOR, "div[aria-label^='Popular times']")
        print("Has popular times")
        times = [[0]*24 for _ in range(7)] # 2D matrix, 7 days of the week, 24h per day
        dow = 0
        hour_prev = 0
        for elem in driver.find_elements(By.CSS_SELECTOR, "div[aria-label*='busy']"):
            bits = elem.get_attribute("aria-label").split()
            if bits[0] == "%":
                # Closed on this day
                dow += 1
            elif bits[0] == "Currently":
                print("Has live info")
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
    except StaleElementReferenceException:
        # Try again
        print("Got a StaleElementReferenceException when trying to get the popular times, trying again")
        time.sleep(.1)
        return extract_place(driver, features, name, link)
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
    driver.implicitly_wait(5)

def refreshPlaces(driver):
    places = []
    scrollCount = 0
    while len(places) < 120 and scrollCount < 10:
        scrollCount += 1
        print("scrolling")
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element(By.CSS_SELECTOR, "div[aria-label^='Results']"))
        time.sleep(1)
        places = driver.find_elements(By.CSS_SELECTOR, "div[aria-label^='Results'] a[aria-label]")
    if not places:
        print("No places")
        raise IndexError
    return places

def extract_page(driver, features):
    try:
        places = refreshPlaces(driver)
    except NoSuchElementException:
        # Single result
        name = driver.find_element(By.CSS_SELECTOR, "h1").text
        print(f"Found {name}")
        link = driver.current_url
        if link in features:
            print(f"Skipping {name}")
        else:
            extract_place(driver, features, name, link)
        return 1

    for place in tqdm(places):
        name = place.get_attribute('aria-label')
        link = place.get_attribute("href")
        if name.startswith("Ad ·"):
            # Don't click on Ads
            continue
        if link in features:
            print(f"Skipping {name}")
            continue
        print(f"Clicking on {name}")
        click(driver, place)
        extract_place(driver, features, name, link)
    return len(places)

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