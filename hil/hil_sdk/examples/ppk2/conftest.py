import os
# Tests are executed with pytest
import pytest
import time
import logging

# We use asyncio to handle bluetooth interactions
# This plugin makes testing with asyncio easier
import pytest_asyncio

# Import EmbedOps provided sdk features
from hil_sdk.version import __version__
from hil_sdk.interfaces.jlink_interface import JLinkInterface
from hil_sdk.interfaces.nrfjprog_interface import nrfjprog_flash
from hil_sdk.interfaces.ppk2.ppk2_interface import PPK2Interface

@pytest.fixture(autouse=True, scope="session")
def hil_version_fixture():
    logging.info(f"HIL SDK version {__version__}")

# Run jlink fixture one time at session start
@pytest.fixture(autouse=True, scope="session")
def jlink_fixture(hil_version_fixture):

    logging.info("Creating J-Link interface...")
    return JLinkInterface("nRF5340_xxAA_APP")

# Run flash fixture one time at session start
# This fixture requests ppk2_fixture, to ensure that ppk2_fixture executes first
@pytest.fixture(autouse=True, scope="session")
def flash_fixture(jlink_fixture, ppk2_fixture, hil_extras_get_path):

    this_dir = os.path.dirname(os.path.abspath(__file__))

    logging.info("Flashing target...")
    assert nrfjprog_flash(hil_extras_get_path("build/zephyr/merged_domains.hex"), "NRF53") == 0

    logging.info("Resetting target...")
    assert jlink_fixture.reset_and_go()

    time.sleep(2)  # Sleep for a couple of seconds to let the target device start up


@pytest.fixture(scope="session", autouse=True)
def ppk2_fixture():

    # This fixture is called first during the test session.
    # This is because ppk.set_device_power() must be called
    # for the DUT processor to power on and be flashed.

    ppk = PPK2Interface()

    assert ppk.open() == True
    logging.info("PPK2 opened...")

    assert ppk.set_ampere_meter_mode()
    assert ppk.set_device_power(True)

    yield ppk

    assert ppk.close() == True
    logging.info("PPK2 closed...")


