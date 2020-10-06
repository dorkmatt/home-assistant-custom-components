#!/usr/bin/env python3

import json, sys, requests, argparse

try:
    import aqi
except ImportError:
    sys.exit("Please install required python module: python-aqi")

def calculate_aqi(HOST):
    try:
        url = 'http://' + HOST + '/v1/current_conditions'
        print(f"# Querying {url}")
        response = requests.get(url, timeout=5, allow_redirects=False)
    except:
        sys.exit("Failed to fetch data from AirLink device")

    airlink_json_values = response.json()['data']['conditions'][0]

    myaqi = aqi.to_aqi([
        (aqi.POLLUTANT_PM10, airlink_json_values['pm_10']),
        (aqi.POLLUTANT_PM25, airlink_json_values['pm_2p5']),
    ])

    print(f"# AirLink Device ID (MAC address): {response.json()['data']['did']}")
    print(f"AQI is {myaqi} (Raw values pm_10: {airlink_json_values['pm_10']} pm_2p5: {airlink_json_values['pm_2p5']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False,
        description='Calculate AQI value derived from Davis AirLink')
    parser.add_argument('-H', '--help', action='help',
        help='show this help message and exit')
    parser.add_argument('-h', '--host', required=True, default=False,
        help='Hostname or IP address')

    if parser.parse_args().host:
        host = parser.parse_args().host
        calculate_aqi(host)
    else:
        parser.print_help()
