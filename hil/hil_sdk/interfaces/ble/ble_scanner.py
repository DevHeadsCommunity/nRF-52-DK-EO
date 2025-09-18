#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#
import re
import string
from typing import Callable
from bleak import BleakScanner
from .ble_types import BLEAdvertisingDevice

class BLEScanner:

    """Provides a scanner interface to the gateway's BLE stack."""

    @staticmethod
    async def find_devices(timeout: float = 5.0,
                           verbose: bool = True,
                           filter: Callable[[BLEAdvertisingDevice], bool] = None) -> list[BLEAdvertisingDevice]:

        """
        Find devices via a BLE scan. Timeout optionally provided.
        Note that this function is asynchronous via the built-in asyncio library. See the example project
        ble_device_scan for usage and testing examples.

        :param timeout: Timeout limit of scan operation

        :param verbose: Verbosity flag

        :param filter: Filter function called for every scanned device (return True to accept a device)

        :return: List of found devices
        """

        scanned_devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
        devices = []
        devices_filtered = []

        for address, device_data in scanned_devices.items():
            # Remove non-printable characters
            name    = re.sub(r'[^{0}\n]'.format(string.printable), '', device_data[0].name)
            address = re.sub(r'[^{0}\n]'.format(string.printable), '', device_data[0].address)

            rssi = device_data[1].rssi
            service_uuids = device_data[1].service_uuids

            advertising_device = BLEAdvertisingDevice(address, name, rssi, service_uuids, device_data[0])

            # Add to non-filtered device list
            devices.append(advertising_device)

            # Apply filtering if applicable
            if filter is not None:
                if filter(advertising_device) == True:
                    devices_filtered.append(advertising_device)
            else:
                devices_filtered.append(advertising_device)

        # Sort by RSSI
        devices.sort(reverse=True, key=lambda device: device.rssi)

        if verbose:
            print("%s: Starting scan..." % (__class__.__name__))
            print("----------------------------------------------------------")
            print("---------------------- SCAN RESULTS ----------------------")
            print("----------------------------------------------------------")
            for device in devices:
                print(f"{device.name : <30}{device.address : <20}{device.rssi : >4} dBm")
            print("----------------------------------------------------------")
        if verbose and filter is not None:
            print("----------------------------------------------------------")
            print("----------------- FILTERED SCAN RESULTS ------------------")
            print("----------------------------------------------------------")
            for device in devices_filtered:
                print(f"{device.name : <30}{device.address : <20}{device.rssi : >4} dBm")
            print("----------------------------------------------------------")

        return devices_filtered
