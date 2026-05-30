"""DataUpdateCoordinator for Homepilot — fetches all devices in one request."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_DEVICES, CID_POSITION, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class HomepilotCoordinator(DataUpdateCoordinator[dict[int, dict]]):
    """Polls Homepilot and keeps a {did: device_dict} mapping."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self.base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _async_update_data(self) -> dict[int, dict]:
        url = self.base_url + API_DEVICES
        try:
            async with self._get_session().get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"Error fetching Homepilot devices: {err}") from err

        devices = payload.get("devices", [])
        return {dev["did"]: dev for dev in devices}


async def async_send_command(self, did: int, cid: int, goto: int | None = None) -> None:
    """Send a command to a single device."""
    url = self.base_url + API_DEVICES
    body: dict = {"did": did, "cid": cid, "command": 1}
    if goto is not None:
        body["goto"] = goto
    try:
        async with self._get_session().post(
            url, data=body, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
    except Exception as err:
        _LOGGER.error("Command cid=%s to device %s failed: %s", cid, did, err)

    async def async_set_position(self, did: int, ha_position: int) -> None:
        hp_position = 100 - ha_position
        await self.async_send_command(did, cid=CID_POSITION, goto=hp_position)

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
