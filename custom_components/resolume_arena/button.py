"""Button entities to trigger Resolume clips."""
import logging
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN
from .helpers.entity import ResolumeEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Create one button per discovered clip slot."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    clip_slots = coordinator.get_clip_slots()
    if not clip_slots:
        _LOGGER.info("No clips found during initial scan (will retry on update).")
    buttons = [
        ResolumeClipButton(
            coordinator,
            slot["layer_id"],
            slot["layer_name"],
            slot["col_index"],
            slot["clip_id"],
            slot["clip_name"],
        )
        for slot in clip_slots
    ]
    async_add_entities(buttons)

class ResolumeClipButton(ResolumeEntity, ButtonEntity):
    def __init__(self, coordinator, layer_id, layer_name, col_index, clip_id, clip_name):
        super().__init__(coordinator)
        self._layer_id = layer_id
        self._layer_name = layer_name
        self._col_index = col_index
        self._clip_id = clip_id
        self._clip_name = clip_name
        self._host = coordinator.host
        self._port = coordinator.port

        self._attr_name = f"Clip {layer_name} C{col_index} ({clip_name})"
        self._attr_unique_id = f"resolume_{self._host}_clip_btn_{layer_id}_{col_index}"

        if clip_id:
            self._attr_entity_picture = (
                f"http://{self._host}:{self._port}/api/v1/composition/clips/by-id/{clip_id}/thumbnail"
            )

    @property
    def icon(self):
        layer_data = self.coordinator.data.get(self._layer_id) if self.coordinator.data else None
        if layer_data and layer_data.get("active_clip_id") == self._clip_id:
            return "mdi:play-box"
        return "mdi:play-box-outline"

    @property
    def extra_state_attributes(self):
        is_active = False
        layer_data = self.coordinator.data.get(self._layer_id) if self.coordinator.data else None
        if layer_data and layer_data.get("active_clip_id") == self._clip_id:
            is_active = True
        return {
            "is_active": is_active,
            "layer_name": self._layer_name,
            "layer_id": self._layer_id,
            "column_index": self._col_index,
            "clip_id": self._clip_id,
            "clip_name": self._clip_name,
            "host": self._host,
        }

    async def async_press(self):
        if not self._clip_id:
            _LOGGER.warning("No clip_id defined for this button, cannot trigger.")
            return
        url = f"http://{self._host}:{self._port}/api/v1/composition/clips/by-id/{self._clip_id}/connect"
        try:
            async with self.coordinator.session.post(url, timeout=5) as response:
                if response.status not in (200, 204):
                    _LOGGER.error("Error triggering clip %s: %s", self._clip_id, response.status)
                else:
                    _LOGGER.info("Clip %s triggered.", self._clip_id)
                    await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Exception triggering clip %s: %s", self._clip_id, err)
