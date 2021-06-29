#!/bin/bash -e
git pull
python3 update_populartimes_data.py
python3 geojson2csv.py
git commit -am "auto update" --author="populartimes-bot <ubuntu@elevation.auckland-cer.cloud.edu.au"
git push