#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import logging
import pytest

from hil_sdk.interfaces.network.tcp import TCPServer
from hil_sdk.interfaces.serial.serial_interface import SerialInterface

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="session")
def serial_interface_fixture():
    try:
        serial = SerialInterface("/dev/ttyUSB0", 115200)
        yield serial
    except Exception as e:
        logging.error(f"Failed to setup Serial interface: {e}")
        raise
    finally:
        serial.close()

@pytest.fixture(scope="session")
def tcp_server_fixture():
    try:
        server = TCPServer("0.0.0.0", 1234)
        yield server
    except Exception as e:
        logging.error(f"Failed to setup TCP server: {e}")
        raise
    finally:
        server.close()
