# https://github.com/linsvensson/sensor.greenely
"""Greenely API"""
import logging
from datetime import datetime, timedelta
import calendar
import requests
import json
from prometheus_client import start_http_server, Gauge
import time
import os

_LOGGER = logging.getLogger(__name__)

jwt = ''
url_check_auth = 'https://api2.greenely.com/v1/checkauth'
url_login = 'https://api2.greenely.com/v1/login'
url_data = 'https://api2.greenely.com/v3/data/'
url_facilities_base = 'https://api2.greenely.com/v1/facilities/'
headers = {'Accept-Language': 'sv-SE',
           'User-Agent': 'Android 2 111',
           'Content-Type': 'application/json; charset=utf-8',
           'Authorization': jwt}

email = os.getenv("GR_EMAIL")
password = os.getenv("GR_PASSWORD")
facility_id = "primary"


def get_facility_id():
    result = requests.get(
        url_facilities_base + 'primary?includes=retail_state&includes=consumption_limits&includes=parameters',
        headers=headers)
    if result.status_code == requests.codes.ok:
        data = result.json()
        facility_id = str(data['data']['parameters']['facility_id'])
        _LOGGER.debug('Fetched facility id %s', facility_id)
    else:
        _LOGGER.error('Failed to fetch facility id %s', result.text)


def login():
    """Login to the Greenely API."""
    result = False
    loginInfo = {'email': email,
                 'password': password}
    loginResult = requests.post(url_login, headers=headers, data=json.dumps(loginInfo))
    if loginResult.status_code == requests.codes.ok:
        jsonResult = loginResult.json()
        jwt = "JWT " + jsonResult['jwt']
        headers['Authorization'] = jwt
        _LOGGER.debug('Successfully logged in and updated jwt')
        if facility_id == 'primary':
            get_facility_id()
        else:
            _LOGGER.debug('Facility id is %s', facility_id)
        result = True
    else:
        _LOGGER.error(loginResult.text)
    return result


def check_auth():
    """Check to see if our jwt is valid."""
    result = requests.get(url_check_auth, headers=headers)
    if result.status_code == requests.codes.ok:
        _LOGGER.debug('jwt is valid!')
        print(result.text)
        return True
    else:
        if login() == False:
            _LOGGER.debug(result.text)
            print(result.text)
            return False
    return True


def get_price_data():
    today = datetime.today()
    start = "?from=" + str(today.year) + "-" + today.strftime("%m") + "-01"
    endOfMonth = calendar.monthrange(today.year, today.month)[1]
    end = "&to=" + str(today.year) + "-" + today.strftime("%m") + "-" + str(endOfMonth);
    url = url_facilities_base + facility_id + '/consumption-cost' + start + end + "&resolution=monthly&prediction=false&exclude_additions=false&exclude_monthly_fee=false&exclude_vat=false"
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == requests.codes.ok:
        data = response.json()
        return data['data']
    else:
        _LOGGER.error('Failed to get price data, %s', response.text)
        return data


def get_spot_price():
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=2)
    start = "?from=" + str(yesterday.year) + "-" + yesterday.strftime("%m") + "-" + yesterday.strftime("%d")
    end = "&to=" + str(tomorrow.year) + "-" + tomorrow.strftime("%m") + "-" + tomorrow.strftime("%d")
    url = url_facilities_base + facility_id + "/spot-price" + start + end + "&resolution=hourly"
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == requests.codes.ok:
        data = response.json()
        return data
    else:
        _LOGGER.error('Failed to get spot price data, %s', response.text)
        return data


def get_usage():
    endDate = datetime.now().replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0) - timedelta(days=1)
    startDate = endDate - timedelta(days=5)
    start = "?from=" + str(startDate.year) + "-" + startDate.strftime("%m") + '-' + str(startDate.day)
    end = "&to=" + str(endDate.year) + "-" + endDate.strftime("%m") + '-' + str(endDate.day)
    url = url_facilities_base + facility_id + '/consumption' + start + end + "&resolution=" + "daily"
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == requests.codes.ok:
        data = response.json()
        for value in data['data']:
            if data['data'][value]['usage'] is not None:
                usage = data['data'][value]['usage']
        return round(usage/1000, 1)
    else:
        _LOGGER.error('Failed to fetch usage data, %s', response.text)
        return data


def get_current_spot_price():
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    currentTime = today.strftime("%Y-%m-%d %H:00")
    start = "?from=" + str(today.year) + "-" + today.strftime("%m") + "-" + today.strftime("%d")
    end = "&to=" + str(tomorrow.year) + "-" + tomorrow.strftime("%m") + "-" + tomorrow.strftime("%d")
    url = url_facilities_base + facility_id + "/spot-price" + start + end + "&resolution=hourly"
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == requests.codes.ok:
        data = response.json()['data']
        for value in data:
            if data[value]['localtime'] == currentTime:
                price = data[value]['price']
                roundedPrice = round(price / 100000, 2)
        return roundedPrice
    else:
        _LOGGER.error('Failed to get spot price data, %s', response.text)
        return data


def get_daily_usage():
    today = datetime.today()
    endDate = datetime.now().replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0) - timedelta(days=1)
    startDate = datetime.today().replace(day=1)

    start = "?from=" + str(startDate.year) + "-" + today.strftime("%m") + '-' + '01'
    end = "&to=" + str(endDate.year) + "-" + endDate.strftime("%m") + '-' + str(endDate.day)
    url = url_facilities_base + facility_id + '/consumption' + start + end + "&resolution=" + "daily"
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == requests.codes.ok:
        data = response.json()
        total_usage = 0
        for value in data['data']:
            if data['data'][value]['usage'] is not None:
                total_usage += data['data'][value]['usage']
        return round(total_usage / 1000, 1)
    else:
        _LOGGER.error('Failed to fetch usage data, %s', response.text)
        return data

def main():
    """Main entry point"""
    if check_auth():
        spot_price = Gauge("greenely_spot_price", "current price per kWh")
        el_usage = Gauge("greenely_last_day_usage", "last daily usage, kWh")
        total_el_usage=Gauge("greenely_total_usage", "total usage from month beginning, kWh")

        start_http_server(9101)

        while True:
            spot_price.set(get_current_spot_price())
            el_usage.set(get_usage())
            total_el_usage.set(get_daily_usage())
            time.sleep(1800)


if __name__ == "__main__":
    main()
