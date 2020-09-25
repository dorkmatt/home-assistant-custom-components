"""
AQI from Davis AirLink sensor

Author: dorkmatt
https://github.com/dorkmatt/home-assistant-custom-components

sensor:
  - platform: davis_airlink
    [host: IP_ADDRESS]
    scan_interval: 10
    resources:
      - aqi
      - algorithm_agency
      - unfiltered_data
"""
