#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

from ..ble_client import BLEClient
import asyncio
import cbor2

# Singular characteristic used for send and receive
SMP_UUID = "da2e7828-fbce-4e01-ae9e-261174997c48"

# SMP operations
OP_READ      = 0
OP_READ_RSP  = 1
OP_WRITE     = 2
OP_WRITE_RSP = 3

# Image management group and commands
GRP_OS_MANAGEMENT    = 0
IMAGE_STATE_COMMAND  = 0
IMAGE_UPLOAD_COMMAND = 1
IMAGE_ERASE_COMMAND  = 5

# Shell group and commands
GRP_SHELL_MANAGEMENT = 9
SHELL_EXECUTE_CMD    = 0

# Other non-supported groups
GRP_IMAGE_MANAGEMENT = 1
GRP_STATS_MANAGEMENT = 2
GRP_FILE_MANAGEMENT  = 8



class BLESMPService:

    """Provides an interface to send and receive SMP messages over Nordic's SMP Transport."""

    def __init__(self, client: BLEClient):

        """
        Construct a new BLESMPService object.

        :param client: BLEClient object to use for communication
        """

        self.smp_event = asyncio.Event()
        self.smp_response = None
        self._client = client

    async def write_smp_and_response(self, data: bytearray, timeout=10):

        """
        Write SMP data and wait for a response based on a timeout

        :param data: Byte data to write to SMP characteristic

        :param timeout: Timeout of operation (in seconds)

        :return: Response object as a dictionary
        """

        try:

            # Make sure we are subscribed to notifications
            if SMP_UUID not in self._client.get_notified_uuids():
                await self._client.start_notify(SMP_UUID, self._smp_rx_cb)

            self.smp_event.clear()
            await self._client.write_gatt(SMP_UUID, data, response=False)
            await asyncio.wait_for(self.smp_event.wait(), timeout=timeout)
            self.smp_event.clear()

            return self.smp_response

        except TimeoutError:
            return None

    def _smp_rx_cb(self, char_uuid: str, data: bytearray):

        """
        Internal function that acts as an SMP received callback. Sets an event to notify the class
        that new data has been received, and sets the global response object.

        :param char_uuid: Characteristic over which the data was received

        :param data: Received data
        """

        op, data_length, group, _, command = BLESMPService._parse_smp_header(data[0:8])

        cbor_data = data[8:]
        cbor_obj = cbor2.loads(cbor_data)

        self.smp_response = cbor_obj
        self.smp_event.set()

    @staticmethod
    def _get_smp_header(operation, data_length: int, group: int, sequence: int, command: int):

        """
        Internal function to return an SMP header buffer specifically for image management

        :param operation: Type of SMP operation to execute

        :param data_length: Length of SMP payload data

        :param group: Group number

        :param sequence: Sequence number (usually 0)

        :param command: Command number

        :meta private:
        """

        return [operation | 8,  0] + \
            list(data_length.to_bytes(2, byteorder="big")) + \
            list(group.to_bytes(2, byteorder="big")) + \
            [sequence, command]

    @staticmethod
    def _parse_smp_header(header_bytes: bytearray):

        """
        Internal function to return an SMP header buffer specifically for image management

        :param header_bytes: Header bytes to decode

        :meta private:
        """

        operation   = header_bytes[0] & 0b111
        data_length = int.from_bytes(header_bytes[2:4], byteorder="big")
        group       = int.from_bytes(header_bytes[4:6], byteorder="big")
        sequence    = header_bytes[6]
        command     = header_bytes[7]

        return operation, data_length, group, sequence, command
