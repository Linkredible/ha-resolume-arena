"""Sensors for Resolume Arena."""
import logging
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
from .helpers.entity import ResolumeEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Create one 'Active Clip' sensor per layer."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    layers = coordinator.get_layers()
    if not layers:
        _LOGGER.warning("No layers found in Resolume composition.")
        return
    sensors = [
        ResolumeActiveClipSensor(coordinator, layer_id, layer_name)
        for layer_id, layer_name in layers.items()
    ]
    async_add_entities(sensors)

class ResolumeActiveClipSensor(ResolumeEntity, SensorEntity):
    """Shows the active clip name for a layer."""
    _attr_icon = "mdi:play-box"
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator, layer_id, layer_name):
        super().__init__(coordinator)
        self._layer_id = layer_id
        self._layer_name = layer_name
        self._host = coordinator.host
        self._attr_name = f"{layer_name} Active Clip"
        self._attr_unique_id = f"resolume_{self._host}_layer_{layer_id}_active_clip"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return "Unknown"
        layer_data = self.coordinator.data.get(self._layer_id)
        if not layer_data:
            return "Unknown"
        return layer_data.get("active_clip_name", "Empty")

    @property
    def extra_state_attributes(self):
        layer_data = (self.coordinator.data.get(self._layer_id) or {}) if self.coordinator.data else {}
        return {
            "layer_name": self._layer_name,
            "layer_id": self._layer_id,
            "active_clip_id": layer_data.get("active_clip_id"),
        }
