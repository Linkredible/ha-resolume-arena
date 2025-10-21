"""Binary sensors for Resolume Arena layer states (Bypass / Solo)."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN
from .helpers.entity import ResolumeEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Create 'Bypass' and 'Solo' binary sensors per layer."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    layers = coordinator.get_layers()
    if not layers:
        _LOGGER.warning("No layers found in Resolume composition.")
        return
    entities = []
    for layer_id, layer_name in layers.items():
        entities.append(ResolumeLayerBypassed(coordinator, layer_id, layer_name))
        entities.append(ResolumeLayerSolo(coordinator, layer_id, layer_name))
    async_add_entities(entities)

class _BaseLayerBool(ResolumeEntity, BinarySensorEntity):
    def __init__(self, coordinator, layer_id, layer_name):
        super().__init__(coordinator)
        self._layer_id = layer_id
        self._layer_name = layer_name
        self._host = coordinator.host

    @property
    def extra_state_attributes(self):
        return {"layer_name": self._layer_name, "layer_id": self._layer_id}

class ResolumeLayerBypassed(_BaseLayerBool):
    _attr_icon = "mdi:minus-circle-outline"

    def __init__(self, coordinator, layer_id, layer_name):
        super().__init__(coordinator, layer_id, layer_name)
        self._attr_name = f"{layer_name} Bypass"
        self._attr_unique_id = f"resolume_{self._host}_layer_{layer_id}_bypassed"

    @property
    def is_on(self):
        layer_data = (self.coordinator.data.get(self._layer_id) or {}) if self.coordinator.data else {}
        return bool(layer_data.get("is_bypassed", False))

class ResolumeLayerSolo(_BaseLayerBool):
    _attr_icon = "mdi:account-voice"

    def __init__(self, coordinator, layer_id, layer_name):
        super().__init__(coordinator, layer_id, layer_name)
        self._attr_name = f"{layer_name} Solo"
        self._attr_unique_id = f"resolume_{self._host}_layer_{layer_id}_solo"

    @property
    def is_on(self):
        layer_data = (self.coordinator.data.get(self._layer_id) or {}) if self.coordinator.data else {}
        return bool(layer_data.get("is_solo", False))
