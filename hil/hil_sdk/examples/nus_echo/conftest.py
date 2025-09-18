#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import os
import pytest
import pytest_asyncio
import logging
import time

from hil_sdk.version import __version__
from hil_sdk.interfaces.ble.ble_client import BLEClient
from hil_sdk.interfaces.ble.nordic.ble_nus_service import BLENUSService
from hil_sdk.interfaces.ble.ble_scanner import BLEScanner
from hil_sdk.interfaces.jlink_interface import JLinkInterface
from hil_sdk.interfaces.nrfjprog_interface import nrfjprog_flash

@pytest.fixture(autouse=True, scope="session")
def hil_version_fixture():
    logging.info(f"HIL SDK version {__version__}")

@pytest.fixture(autouse=True, scope="session")
def jlink_fixture(hil_version_fixture):

    logging.info("Creating J-Link interface...")
    return JLinkInterface("nRF5340_xxAA_APP")

# Run flash fixture one time at session start
@pytest.fixture(autouse=True, scope="session")
def flash_fixture(jlink_fixture, hil_extras_get_path):

    logging.info("Flashing target...")
    assert nrfjprog_flash(hil_extras_get_path("build/zephyr/merged_domains.hex"), "NRF53") == 0

    logging.info("Resetting target...")
    assert jlink_fixture.reset_and_go()

    time.sleep(2)  # Sleep for a couple of seconds to let the target device start up

@pytest.fixture
def reset_fixture(jlink_fixture):

    logging.info("Resetting target...")
    assert jlink_fixture.reset_and_go()

@pytest_asyncio.fixture
async def ble_nus_fixture(reset_fixture):

    devices = await BLEScanner.find_devices()

    address = None
    device = None
    for d in devices:
        if "EmbedOps" in d.name:
            address = d.address
            device = d

    if address is None:
        logging.error('EmbedOps device not found!')
        assert False

    logging.info("EmbedOps address: " + address)

    client = BLEClient(device)

    await client.connect()

    nus_service = BLENUSService(client)

    yield nus_service

    await client.disconnect()




