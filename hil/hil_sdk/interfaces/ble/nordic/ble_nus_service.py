#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

from collections.abc import Callable
from ..ble_client import BLEClient
from binascii import hexlify

UART_TX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


class BLENUSService:

    """Provies an interface to read and write data via the Nordic UART Service (NUS)."""

    def __init__(self, client: BLEClient):

        """
        Construct a new BLENUSService object.

        :param client: BLEClient object to use for communication
        """

        self._client = client

    async def write_nus(self, data: bytearray) -> None:

        """
        Write data to the NUS characteristic.

        :param data: Data to send over NUS

        :return: None
        """
        print("%s: write: %s" % (self.__class__.__name__, hexlify(data)))
        await self._client.write_gatt(UART_TX_UUID, data)

    async def set_nus_received_cb(self, received_cb: Callable[[str, bytearray], None]) -> None:

        """
        Set the callback that is called when data is received.

        :param received_cb: Callback that will receive the UUID and received data when a notification arrives

        :return: None
        """
        print("%s: setting nus callback: %s" % (self.__class__.__name__, getattr(received_cb, '__name__', 'Unknown')))
        await self._client.start_notify(UART_RX_UUID, received_cb)
