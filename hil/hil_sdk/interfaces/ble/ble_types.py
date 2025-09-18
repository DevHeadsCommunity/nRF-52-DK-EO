#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

"""BLE type definitions and models used by BLEInterface."""


class BLEAdvertisingDevice:

    """Represents a device that is advertising."""

    def __init__(self, address: str, name: str, rssi: int, service_uuids: list, backend_obj):

        self.address = address
        """Address of device"""
        self.name = name
        """Name of device"""
        self.rssi = rssi
        """RSSI of device"""
        self.service_uuids = service_uuids
        """List of advertised service UUIDs"""

        self._backend_obj = backend_obj
