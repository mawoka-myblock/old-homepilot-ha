"""Cover platform — dynamically creates one entity per Homepilot shutter device."""

from __future__ import annotations

import logging

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CMD_DOWN, CMD_STOP, CMD_UP, DEVICE_GROUP_COVER, DOMAIN
from .coordinator import HomepilotCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up covers from a config entry — one entity per shutter device."""
    coordinator: HomepilotCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track which dids we've already created entities for
    known_dids: set[int] = set()

    @callback
    def _add_new_devices() -> None:
        new_entities = []
        for did, device in coordinator.data.items():
            if (
                did not in known_dids
                and device.get("deviceGroup") == DEVICE_GROUP_COVER
            ):
                known_dids.add(did)
                new_entities.append(HomepilotCover(coordinator, did))
        if new_entities:
            async_add_entities(new_entities)

    # Add devices already present, and listen for future updates (new devices)
    _add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


class HomepilotCover(CoordinatorEntity[HomepilotCoordinator], CoverEntity):
    """A single roller shutter from the Homepilot hub."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: HomepilotCoordinator, did: int) -> None:
        super().__init__(coordinator)
        self._did = did
        device = coordinator.data[did]
        self._attr_unique_id = f"homepilot_{device['uid']}"
        self._attr_name = device["name"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["uid"])},
            name=device["name"],
            manufacturer="Rademacher",
            model=device.get("productName", "DuoFern Rohrmotor-Aktor"),
            sw_version=device.get("version"),
        )

    @property
    def _device(self) -> dict:
        return self.coordinator.data.get(self._did, {})

    @property
    def _hp_position(self) -> int | None:
        """Raw Homepilot position (0=open, 100=closed)."""
        return self._device.get("statusesMap", {}).get("Position")

    @property
    def current_cover_position(self) -> int | None:
        """HA position (0=closed, 100=open)."""
        if self._hp_position is None:
            return None
        return 100 - self._hp_position

    @property
    def is_closed(self) -> bool | None:
        if self._hp_position is None:
            return None
        return self._hp_position == 100

    @property
    def is_opening(self) -> bool:
        manual = self._device.get("statusesMap", {}).get("Manuellbetrieb", 0)
        # Homepilot doesn't expose direction cleanly; use manual mode as a proxy
        return False  # extend if your firmware exposes movement state

    @property
    def is_closing(self) -> bool:
        return False

    async def async_open_cover(self, **kwargs) -> None:
        await self.coordinator.async_send_command(self._did, CMD_UP)

    async def async_close_cover(self, **kwargs) -> None:
        await self.coordinator.async_send_command(self._did, CMD_DOWN)

    async def async_stop_cover(self, **kwargs) -> None:
        await self.coordinator.async_send_command(self._did, CMD_STOP)

    async def async_set_cover_position(self, **kwargs) -> None:
        position = kwargs["position"]  # HA scale: 0–100 open
        await self.coordinator.async_set_position(self._did, position)
