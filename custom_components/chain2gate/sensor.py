"""Platform for sensor integration of C2G."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
    discovery_info=None):
    """ Setup sensor platform """

    gate = hass.data[DOMAIN][config_entry.entry_id]

    sensors = gate.get_sensors()

    for sensor in sensors:
        async_add_entities([C2GHASensor(gate, sensor)], update_before_add=True)


class C2GHASensor(SensorEntity, RestoreEntity):
    """Representation of a Sensor."""

    def __init__(self, gate, c2g_sensor):
        super().__init__()
        self.gate = gate
        self._c2g_sensor = c2g_sensor
        self._available = True
        self._unit_of_measurement = c2g_sensor.unit_of_measurement

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._c2g_sensor.name
    
    @property
    def native_value(self):
        return self._state

    @property
    def state(self):
        """Return the state of the device."""
        return self._state
    
    @property
    def native_unit_of_measurement(self):
        """Return the native unit of measurement of this entity, if any."""
        return self._unit_of_measurement
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement
    
    @property
    def device_class(self):
        return self._c2g_sensor.device_class

    @property
    def state_class(self):
        return self._c2g_sensor.state_class

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.gate.id + "_" + self.name

    @property
    def available(self) -> bool:
        return self._available
    
    @property
    def should_poll(self):
        """Return that polling is not necessary."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            configuration_url="http://" + self.gate.ip,
            manufacturer="MAC s.r.l",
            model="Chain2Gate",
            name=self.gate.id,
            identifiers={(DOMAIN, self.gate.id)},
            sw_version=self.gate.prog_id,
        )
    
    async def async_added_to_hass(self):
        """Register callback to update hass after device was changed."""
        await super().async_added_to_hass()
        
        # todo: seems like it does restore an old state, but it's not the last one
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._state = last_state.state

        async def after_update_callback():
            """Call after device was updated."""
            await self.async_update_ha_state(True)
        self._c2g_sensor.set_callback(after_update_callback)

    async def async_update(self):
        """Retrieve latest state."""
        self._state = self._c2g_sensor.value
        self._unit_of_measurement = self._c2g_sensor.unit_of_measurement