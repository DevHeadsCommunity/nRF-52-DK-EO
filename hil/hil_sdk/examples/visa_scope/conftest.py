#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import os
import pytest
import logging
import time

from hil_sdk.version import __version__
from hil_sdk.interfaces.jlink_interface import JLinkInterface
from hil_sdk.interfaces.nrfjprog_interface import nrfjprog_flash
from hil_sdk.interfaces.visa.oscilloscope.visa_scope_sds804xhd import VISAScopeSDS804XHD

@pytest.fixture(autouse=True, scope="session")
def hil_version_fixture():
    logging.info(f"HIL SDK version {__version__}")

@pytest.fixture(autouse=True, scope="session")
def jlink_fixture(hil_version_fixture):

    logging.info("Creating J-Link interface...")
    return JLinkInterface("nRF5340_xxAA_APP")

@pytest.fixture(autouse=True, scope="session")
def flash_fixture(jlink_fixture, hil_extras_get_path):

    logging.info("Flashing target...")
    assert nrfjprog_flash(hil_extras_get_path("build/zephyr/merged_domains.hex"), "NRF53") == 0

    logging.info("Resetting target...")
    assert jlink_fixture.reset_and_go()

    time.sleep(2)  # Sleep for a couple of seconds to let the target device start up


@pytest.fixture
def visa_scope_sds804xhd_fixture():
    return VISAScopeSDS804XHD()