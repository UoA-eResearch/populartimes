#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from openlocationcode import openlocationcode as olc
from datetime import datetime
import time
import re
import json

# gmaps starts their weeks on sunday
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

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
for i in range(20):
    places = []
    scrollCount = 0
    while len(places) < 20 and scrollCount < 10:
        scrollCount += 1
        print("scrolling")
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element_by_css_selector("div[aria-label='Results for place of interest']"))
        time.sleep(.1)
        places = driver.find_elements_by_css_selector("div[aria-label='Results for place of interest'] a[aria-label]")
    place = places[i]
    name = place.get_attribute('aria-label')
    print(f"Clicking on {name}")
    place.click()
    link = place.get_attribute("href")
    code = driver.find_element_by_css_selector("button[data-tooltip='Copy plus code']").text
    approx_ll = re.search(f'(?P<lat>-?\d+\.\d+).+?(?P<lng>-?\d+\.\d+)', link).groupdict()
    approx_lat = float(approx_ll["lat"])
    approx_lng = float(approx_ll["lng"])
    codeArea = olc.decode(olc.recoverNearest(code.split()[0], approx_lat, approx_lng))
    lat = codeArea.latitudeCenter
    lng = codeArea.longitudeCenter
    address = None
    try:
        address = driver.find_element_by_css_selector("button[data-tooltip='Copy address']").get_attribute("aria-label").split(":")[-1].strip()
    except NoSuchElementException:
        pass
    try:
        popular = driver.find_element_by_css_selector("div.section-popular-times")
        print("Has popular times")
        times = [[0]*24 for _ in range(7)] # 2D matrix, 7 days of the week, 24h per day
        dow = 0
        hour_prev = 0
        live_info = None
        for elem in driver.find_elements_by_css_selector("div.section-popular-times-bar"):
            bits = elem.get_attribute("aria-label").split()
            if bits[0] == "Currently":
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
        print(feature)
        features.append(feature)
    except NoSuchElementException:
        print("No popular times available, skipping")
    driver.find_element_by_xpath('//button/span[text()="Back to results"]').click()
driver.find_element_by_css_selector("button[aria-label=' Next page ']").click()

driver.close()

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open("data.geojson", "w") as f:
    json.dump(geojson, f)