
"""
AQI from Davis AirLink sensor

Author: dorkmatt
https://github.com/dorkmatt/home-assistant-custom-components
Heavily modeled after https://github.com/cyberjunky/home-assistant-toon_boilerstatus

sensor:
  - platform: davis_airlink
    host: IP_ADDRESS
    resources:
      - temperature
      - humidity
      - dew_point
      - wet_bulb
      - heat_index
      - pm_1_last
      - pm_2p5_last
      - pm_10_last
      - pm_1
      - pm_2p5
      - pm_2p5_last_1_hour
      - pm_2p5_last_3_hours
      - pm_2p5_last_24_hours
      - pm_2p5_nowcast
      - pm_10
      - pm_10_last_1_hour
      - pm_10_last_3_hours
      - pm_10_last_24_hours
      - pm_10_nowcast
      - last_report_time
      - pct_pm_data_last_1_hour
      - pct_pm_data_last_3_hours
      - pct_pm_data_nowcast
      - pct_pm_data_last_24_hours
"""
import logging
from datetime import timedelta
import aiohttp
import asyncio
import async_timeout
import voluptuous as vol
# TODO import aqi (to calculate US EPA AQI number)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_RESOURCES,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

BASE_URL = 'http://{0}/v1/current_conditions'
_LOGGER = logging.getLogger(__name__)

# TODO: device only updates every ~60s, don't allow lt 60 sec for scan_interval
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

SENSOR_PREFIX = 'Davis AirLink '
SENSOR_TYPES = {
    'temp': ['Temperature', '°F', 'mdi:thermometer'],
    'hum': ['Humidity', '%', 'mdi:gauge'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_RESOURCES, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Davis AirLink sensors."""

    session = async_get_clientsession(hass)
    data = DavisAirLinkStatusData(session, config.get(CONF_HOST))
    await data.async_update()

    entities = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        name = SENSOR_PREFIX + SENSOR_TYPES[resource][0]
        unit = SENSOR_TYPES[resource][1]
        icon = SENSOR_TYPES[resource][2]

        _LOGGER.debug("Adding Davis AirLink Status sensor: {}, {}, {}, {}".format(name, sensor_type, unit, icon))
        entities.append(DavisAirLinkStatusSensor(data, name, sensor_type, unit, icon))

    async_add_entities(entities, True)

class DavisAirLinkStatusData(object):
    """Davis AirLink object and limit updates."""
    def __init__(self, session, host):
        """Initialize the data object."""

        self._session = session
        self._url = BASE_URL.format(host)
        self._data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Download and update data from Davis AirLink."""

        try:
            with async_timeout.timeout(5):
                response = await self._session.get(self._url)
        except aiohttp.ClientError:
            _LOGGER.error("Cannot poll Davis AirLink using url: %s", self._url)
            return
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error occurred while polling Davis AirLink using url: %s", self._url)
            return
        except Exception as err:
            _LOGGER.error("Unknown error occurred while polling Davis AirLink: %s", err)
            self._data = None
            return

        try:
            self._data = await response.json(content_type='application/json')
            _LOGGER.debug("Data received from Davis AirLink: %s", self._data)
        except Exception as err:
            _LOGGER.error("Cannot parse data received from Davis AirLink: %s", err)
            self._data = None
            return

    @property
    def latest_data(self):
        """Return the latest data object."""
        return self._data

class DavisAirLinkStatusSensor(Entity):
    """Representation of a Davis AirLink sensor."""

    def __init__(self, data, name, sensor_type, unit, icon):
        """Initialize the sensor."""
        self._data = data
        self._name = name
        self._type = sensor_type
        self._unit = unit
        self._icon = icon

        self._state = None
        self._last_updated = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr['Last Updated'] = self._last_updated
        return attr

    async def async_update(self):
        """Get the latest data and use it to update our sensor state."""

        await self._data.async_update()
            _LOGGER.debug("Device: {} State: {}".format(self._type, self._state))
