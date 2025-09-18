#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import asyncio
import bleak
from .ble_types import BLEAdvertisingDevice

class BLEClient:

    """Provides an interface to the gateway's BLE stack."""

    def __init__(self, address_or_device):

        """
        Construct a new BLE Client object.

        :param address_or_device: Client address to connect to, or BLEAdvertisingDevice object reference
        """

        self.address_or_device = address_or_device
        self._client_obj = None

        # This dict holds the user's desired notification callbacks so we can translate out the backend object
        self._notify_callbacks = {}

    async def connect(self, timeout: float = 10, retry_count: int = 5) -> bool:

        """
        Attempt to connect the client

        :param timeout: Timeout limit of scan operation

        :param retry_count: Number of times to attempt to connect in case of failure

        :return: True on success, false otherwise
        """

        for i in range(retry_count):
            try:
                self._client_obj, self.address = BLEClient._get_backend_object(self.address_or_device)
                await self._client_obj.connect(timeout=timeout)
                return True
            except:
                print(f"Connection attempt {i} failed, retrying...")

        return False

    def is_connected(self) -> bool:

        """
        Return an is_connected future

        :return: True on connected, false otherwise
        """
        return self._client_obj.is_connected()

    async def disconnect(self) -> bool:

        """
        Attempt to disconnect the client

        :return: True on success, false otherwise
        """

        if self._client_obj:
            return await self._client_obj.disconnect()

        return False

    async def read_gatt(self, char_uuid: str) -> bytearray:

        """
        Read a GATT characteristic value by UUID

        :param char_uuid: Full UUID of characteristic

        :return: Characteristic value
        """

        if self._client_obj:
            return await self._client_obj.read_gatt_char(bleak.uuids.normalize_uuid_str(char_uuid))

    async def write_gatt(self, char_uuid: str, data, response=False) -> None:

        """
        Write to a GATT characteristic by UUID

        :param char_uuid: Full UUID of characteristic

        :param data: Data to be written

        :param response: True if write-with-response is desired, False if write-without-response, None for autodetect
        """

        if self._client_obj:
            return await self._client_obj.write_gatt_char(char_uuid, data, response)

    async def start_notify(self, char_uuid: str, callback) -> None:

        """
        Start listening for notifications on a given characteristic.

        :param char_uuid: Full UUID of characteristic

        :param callback: Callback that accepts two parameters: The first is the UUID of the characteristic, the second is the received data
        """

        if self._client_obj and callback:

            uuid = char_uuid.lower()
            self._notify_callbacks[uuid] = callback
            return await self._client_obj.start_notify(uuid, self._notification_callback)

    def get_notified_uuids(self):

        """Return a list of the UUIDs that are currently subscribed for notifications"""

        return list(self._notify_callbacks.keys())

    def _notification_callback(self, characteristic: bleak.BleakGATTCharacteristic, value: bytearray):

        """Private method to translate the backend's notify callback into a consistent interface that remains
        the same, even if the BLE backend changes."""

        uuid = characteristic.uuid.lower()
        user_callback = self._notify_callbacks[uuid]
        user_callback(uuid, value)

    def lookup_uuid_name(self, char_uuid: str):
        """
        Return the standard name for a given 16 bit UUID

        :param char_uuid: 16bit UUID of characteristic

        """
        return bleak.uuids.uuid16_dict[int(char_uuid,16)]

    @staticmethod
    def _get_backend_object(address_or_device):

        if isinstance(address_or_device, BLEAdvertisingDevice):
            client_obj = bleak.BleakClient(address_or_device._backend_obj)
            address = client_obj.address
        else:
            # Assume that the parameter is an address
            client_obj = bleak.BleakClient(address_or_device)
            address = address_or_device

        return client_obj, address
