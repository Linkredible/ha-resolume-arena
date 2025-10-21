"""Common base entity for Resolume integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class ResolumeEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._host = coordinator.host
        self._attr_device_info = coordinator.device_info
