"""DataUpdateCoordinator for the Resolume Arena integration."""
import logging
from datetime import timedelta
from aiohttp import ClientError

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, SCAN_INTERVAL_SECONDS
from .helpers.api import composition_url, layer_by_id_url, clip_by_id_url

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)

class ResolumeDataUpdateCoordinator(DataUpdateCoordinator):
    """Periodically pulls state from Resolume's HTTP API."""

    def __init__(self, hass, host, port):
        self.host = host
        self.port = port
        self.session = async_get_clientsession(hass)

        self._layers = {}          # {layer_id: layer_name}
        self._clip_slots = []      # [{layer_id, layer_name, col_index, clip_id, clip_name}]
        self._clip_name_cache = {} # {clip_id: clip_name}
        self.composition_name = f"Resolume ({host})"

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    def _get_value(self, param_obj, default=None):
        """Safely read .value out of Resolume params, with sensible fallbacks."""
        if isinstance(param_obj, dict):
            val = param_obj.get("value", default)
            return val if val is not None else default
        if param_obj is None:
            return default
        return param_obj

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            name=self.composition_name,
            manufacturer="Resolume",
            model="Arena",
            via_device=None,
        )

    def get_layers(self):
        """Public copy of discovered layers mapping."""
        return dict(self._layers)

    def get_clip_slots(self):
        """Public copy of discovered clip slots."""
        return list(self._clip_slots)

    async def _async_discover_layers(self):
        """Discover all layers (including nested groups)."""
        try:
            async with self.session.get(composition_url(self.host, self.port), timeout=10) as response:
                if response.status != 200:
                    raise UpdateFailed(f"API Error (Composition): {response.status}")
                composition = await response.json()

                comp_name_param = composition.get("name", {})
                self.composition_name = self._get_value(comp_name_param, f"Resolume ({self.host})")

                self._layers.clear()

                def process_item(item, group_name=""):
                    if not isinstance(item, dict):
                        return
                    if "clips" in item:  # it's a Layer
                        layer_id = item.get("id")
                        if layer_id and layer_id not in self._layers:
                            layer_name = self._get_value(item.get("name"), f"Layer {layer_id}")
                            full_name = f"{group_name} - {layer_name}" if group_name else layer_name
                            self._layers[layer_id] = full_name
                    elif "layers" in item or "layergroups" in item:  # it's a Group
                        current_group_name = self._get_value(item.get("name"), "Group")
                        nested_group_name = f"{group_name} - {current_group_name}" if group_name else current_group_name
                        for layer in self._get_value(item.get("layers"), []):
                            process_item(layer, nested_group_name)
                        for subgroup in self._get_value(item.get("layergroups"), []):
                            process_item(subgroup, nested_group_name)

                for it in self._get_value(composition.get("layers"), []):
                    process_item(it)
                for it in self._get_value(composition.get("layergroups"), []):
                    process_item(it)

                _LOGGER.info("Resolume: %s layers discovered (recursive).", len(self._layers))

        except ClientError as err:
            raise UpdateFailed(f"Connection Error (Discovery): {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error during discovery: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _async_update_data(self):
        """Fetch layer state and discover clips."""
        if not self._layers:
            await self._async_discover_layers()
            if not self._layers:
                _LOGGER.warning("No layers found, aborting update.")
                return {}

        data = {}
        self._clip_slots = []

        try:
            for layer_id, layer_name in self._layers.items():
                url = layer_by_id_url(self.host, self.port, layer_id)
                async with self.session.get(url, timeout=5) as response:
                    if response.status != 200:
                        _LOGGER.warning("Failed to get layer %s (maybe a group?), skipping.", layer_id)
                        continue

                    layer_detail = await response.json()

                    # Active clip
                    active_clip = layer_detail.get("active_clip")
                    active_clip_name = "Empty"
                    active_clip_id = None
                    if active_clip:
                        name_param = active_clip.get("name") or (active_clip.get("params", {}) or {}).get("name")
                        active_clip_name = self._get_value(name_param, "Unnamed Clip")
                        active_clip_id = active_clip.get("id")

                    # Layer states
                    bypassed_param = layer_detail.get("bypassed", {})
                    solo_param = layer_detail.get("solo", {})

                    data[layer_id] = {
                        "active_clip_name": active_clip_name,
                        "active_clip_id": active_clip_id,
                        "is_bypassed": self._get_value(bypassed_param, False),
                        "is_solo": self._get_value(solo_param, False),
                    }

                    # Discover clips
                    clips_list = self._get_value(layer_detail.get("clips", {}), [])
                    if isinstance(clips_list, list):
                        for idx, clip in enumerate(clips_list, start=1):
                            if not clip:
                                continue

                            clip_id = clip.get("id")
                            name_param = clip.get("name") or (clip.get("params", {}) or {}).get("name")
                            clip_name = self._get_value(name_param, None)

                            if clip_name is None and clip_id:
                                clip_name = self._clip_name_cache.get(clip_id)
                                if clip_name is None:
                                    try:
                                        c_url = clip_by_id_url(self.host, self.port, clip_id)
                                        async with self.session.get(c_url, timeout=2) as r:
                                            if r.status == 200:
                                                cd = await r.json()
                                                np = cd.get("name") or (cd.get("params", {}) or {}).get("name")
                                                clip_name = self._get_value(np, None)
                                                if clip_name:
                                                    self._clip_name_cache[clip_id] = clip_name
                                    except Exception:
                                        pass

                            if not clip_name:
                                clip_name = f"Clip {idx}"

                            self._clip_slots.append({
                                "layer_id": layer_id,
                                "layer_name": layer_name,
                                "col_index": idx,
                                "clip_id": clip_id,
                                "clip_name": clip_name,
                            })

            return data

        except ClientError as err:
            raise UpdateFailed(f"Connection Error (Update): {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error during update: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}")
