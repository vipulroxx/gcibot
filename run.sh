#!/bin/sh
python gcibot.py apertium brlcad copyleftgames drupal-google fossasia mifos sahana-eden sugar wikimedia-dev kde-soc openmrs haiku &

while true; do
        python update.py
        sleep 10m
done
