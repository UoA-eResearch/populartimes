#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from pprint import pprint
from openlocationcode import openlocationcode as olc

# gmaps starts their weeks on sunday
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# Initialise driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
driver.implicitly_wait(5)
driver.get("https://www.google.com/maps/search/place+of+interest/@-36.8508578,174.7615744,15z/data=!3m1!4b1")

results = []
for i in range(20):
    places = []
    scrollCount = 0
    while len(places) < 20 and scrollCount < 10:
        scrollCount += 1
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element_by_css_selector("div[aria-label='Results for place of interest']"))
        places = driver.find_elements_by_css_selector("div[aria-label='Results for place of interest'] a[aria-label]")
    place = places[i]
    print(f"Clicking on {place.get_attribute('aria-label')}")
    place.click()
    code = driver.find_element_by_css_selector("button[data-tooltip='Copy plus code']").text
    codeArea = olc.decode(olc.recoverNearest(code.split()[0], -36.84840987798827, 174.7621911279435))
    print(code, codeArea.latitudeCenter, codeArea.longitudeCenter)
    address = None
    try:
        address = driver.find_element_by_css_selector("button[data-tooltip='Copy address']").get_attribute("aria-label").split(":")[-1].strip()
        print(address)
    except NoSuchElementException:
        pass
    try:
        popular = driver.find_element_by_css_selector("div.section-popular-times")
        print("Has popular times")
        times = []
        dow = 0
        hour_prev = 0
        for elem in driver.find_elements_by_css_selector("div.section-popular-times-bar"):
            bits = elem.get_attribute("aria-label").split()
            if bits[0] == "Currently":
                hour += 1
                times.append({
                    "live_frequency": int(bits[1].rstrip("%")),
                    "frequency": int(bits[-2].rstrip("%")),
                    "hour": hour,
                    "day": days[dow % 7]
                })
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
                times.append({
                    "frequency": int(bits[0].rstrip("%")),
                    "hour": hour,
                    "day": days[dow % 7]
                })
        pprint(times)
    except NoSuchElementException:
        print("No popular times available, skipping")
    driver.find_element_by_xpath('//button/span[text()="Back to results"]').click()
driver.find_element_by_css_selector("button[aria-label=' Next page ']").click()

driver.close()