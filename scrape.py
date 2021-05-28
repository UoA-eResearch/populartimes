#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  

# Initialise driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)
driver.get("https://www.google.com/maps/search/place+of+interest/@-36.8508578,174.7615744,15z/data=!3m1!4b1")

results_div = driver.find_element_by_css_selector("div[aria-label='Results for place of interest']")
places = results_div.find_elements_by_css_selector("a[aria-label]")
for place in places:
    print(f"Clicking on {place.text}")
    place.click()
    code = driver.find_element_by_css_selector("button[data-tooltip='Copy plus code']").text
    print(code)
driver.close()