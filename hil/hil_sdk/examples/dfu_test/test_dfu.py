#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import os
import asyncio
import pytest

@pytest.mark.asyncio
async def test_ble_dfu(ble_dfu_fixture):

    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_image = os.path.join(test_dir, "app_update.bin")

    def update_callback(offset, total_size):

        percent = int(float(offset) / float(total_size) * 100)

        if percent % 10 == 0:
            print(f"DFU Progress: {percent}%")

    print("Starting DFU")
    dfu_status = await ble_dfu_fixture.image_upload(test_image, on_update=update_callback)
    print(f"DFU Complete: {dfu_status}")

    await asyncio.sleep(5)

    assert dfu_status
