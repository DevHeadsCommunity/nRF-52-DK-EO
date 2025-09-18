#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import asyncio
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_ble_nus(ble_nus_fixture):

    test_data = b"This is a test"

    async def rx_callback(uuid, data):
        assert data == test_data

    await ble_nus_fixture.set_nus_received_cb(rx_callback)

    await ble_nus_fixture.write_nus(test_data)

    await asyncio.sleep(5)
