#!/bin/bash -e
git pull
python3 update_populartimes_data.py
python3 geojson2csv.py
git pull
git add data.csv data.geojson
git commit -m "auto update" --author="populartimes-bot <ubuntu@elevation.auckland-cer.cloud.edu.au>"
git push