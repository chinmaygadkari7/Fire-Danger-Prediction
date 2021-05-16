import os
import requests
import json
import math
from urllib import parse
import logging
from random import choice

BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"


def fetch_soil_moisture():
    with open("data/soil-moisture.json", "r") as f:
        data = json.load(f)

    return data


def get_forecast(locality, key):
    """
    Get 15 days weather forecast from Visual Crossing Weather API
    """
    quoted_locality = parse.quote(locality)
    forecast_url = BASE_URL + '{locality}, VIC/'.format(locality=quoted_locality) # forecast url
    params = {
        'key': key,
        'include': 'fcst',
        'unitGroup': 'metric'
    }

    response = requests.get(forecast_url, params=params)

    if response.status_code != 200:
        logging.info("Unsuccessful request from WeatherAPI for %r", locality)
        logging.info(response.text)
        raise RuntimeError(response.text)

    forecast = json.loads(response.text)
    logging.info("Successfully fetched forecast for %r", locality)
    return forecast


def get_historical_weather(locality, key):
    """
    Get historical observations for last 7 days from Visual Crossing Weather API
    """
    # quote the locality string (for url encoding)
    quoted_locality = parse.quote(locality)
    historical_url = BASE_URL + '{locality},VIC/last15days'.format(locality=quoted_locality)
    params = {
        'key': key,
        'include': 'obs',
        'unitGroup': 'metric'
    }

    # send get request
    response = requests.get(historical_url, params=params)

    if response.status_code != 200:
        logging.info("Unsuccessful request from WeatherAPI for %r", locality)
        logging.info(response.text)
        raise RuntimeError(response.text)

    # load JSON response
    observations = json.loads(response.text)
    logging.info("Successfully fetched historical observations for %r", locality)
    return observations

def find_last_precipitation(obs):
    """
    Calculate number of days its been from last rainfall
    """
    days_since_last_precipitation = 0
    for day in sorted(obs['days'], reverse=True, key= lambda  d: d['datetime']):
        precip= day['precip'] if day['precip'] is not None else 0
        if precip == 0:
            days_since_last_precipitation += 1
        else:
            break

        return days_since_last_precipitation


def get_FFDI_category(FFDI):
    """
    Get Category for Forest Fire Danger Index
    """
    if FFDI >= 0 and FFDI <= 11:
        return 'low-moderate'
    elif FFDI > 11 and FFDI <= 24:
        return "high"
    elif FFDI > 24 and FFDI <= 49:
        return "very high"
    elif FFDI > 49 and FFDI <= 99:
        return "severe"
    elif FFDI > 99 and FFDI <= 149:
        return "extreme"
    else:
        return "catastrophic (code red)"


def get_fire_danger_forecast(locality, key):
    """
    Forecast Forest Fire Danger Index based on historial observations and weather forecast
    """

    locality = locality.lower()
    logging.info("Calulating fire danger rating for %r", locality)

    soil_moisture_deficits = fetch_soil_moisture()
    if locality not in soil_moisture_deficits.keys():
        logging.error("Locality not found in dataset %r", locality)
        raise LookupError("Locality not found.")

    SMD = soil_moisture_deficits.get(locality)

    observations = get_historical_weather(locality, key)
    days_since_last_precipitation = find_last_precipitation(observations)
    forecast = get_forecast(locality, key)
    A = days_since_last_precipitation - 1

    for day in forecast['days']:
        if day['precip'] == 0:
            A += 1
        else:
            A = 0

        R = day['precip'] if day['precip'] is not None else 0# precipitation in mm
        V = day['windspeed'] # windspeed in km/h
        T = day['tempmax'] # maximum temperature in degree C
        RH = day['humidity']

        # Calculate Drought factor
        x = (A ** 1.3) / (((A** 1.3) + R - 2) + 0.00001)
        F =  ((41*(x**2)) + x) / ((40*(x**2) + x + 1) + 0.00001)
        DF = 10.5 * (1- math.exp(-((SMD + 30)/40))) * F # Drought factor

        # Calculate Forest fire danger index
        FFDI = 1.2753 * math.exp((0.987 * math.log(DF+0.00001)) + (0.0338 * T) + (0.0234 * V) - (0.0345 * RH))
        FFDI_category  = get_FFDI_category(FFDI)

        day['FFDI'] = max(FFDI, 0.1)
        day['FFDI_category'] = FFDI_category

    logging.info("Successfully calculated predictions for %r", locality)
    return forecast
