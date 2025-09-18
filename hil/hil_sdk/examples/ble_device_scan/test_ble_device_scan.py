#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import asyncio
from hil_sdk.interfaces.ble.ble_scanner import BLEScanner


def test_ble_scan():

    async def test_func():

        devices = await BLEScanner.find_devices()
        device_names = [d.name for d in devices]

        assert "EmbedOps HIL Demo Device" in device_names

    asyncio.run(test_func())
