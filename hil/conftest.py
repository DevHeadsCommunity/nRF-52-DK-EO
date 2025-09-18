import os
# Tests are executed with pytest
import pytest
import time
import subprocess
import asyncio
import logging

# We use asyncio to handle bluetooth interactions
# This plugin makes testing with asyncio easier
import pytest_asyncio

# Import EmbedOps provided sdk features
from hil_sdk.interfaces.jlink_interface import JLinkInterface
from hil_sdk.interfaces.ble.ble_client import BLEClient
from hil_sdk.interfaces.ble.nordic.ble_shell_service import BLEShellService
from hil_sdk.interfaces.ble.nordic.ble_nus_service import BLENUSService
from hil_sdk.interfaces.ble.nordic.ble_dfu_service import BLEDFUService
from hil_sdk.interfaces.ble.ble_scanner import BLEScanner
from hil_sdk.interfaces.nrfjprog_interface import nrfjprog_flash
from hil_sdk.interfaces.serial.serial_interface import SerialInterface

BLE_ADDR_STR_LEN = 18  # Length of a BLE address string (including newline)

# Run jlink fixture one time at session start
@pytest.fixture(autouse=True, scope="session")
def jlink_fixture():

    logging.info("Creating J-Link interface...")
    return JLinkInterface("nRF5340_xxAA_APP")

# Run flash fixture one time at session start
@pytest.fixture(autouse=True, scope="session")
def flash_fixture(jlink_fixture, hil_extras_get_path):

    this_dir = os.path.dirname(os.path.abspath(__file__))

    logging.info("Flashing target...")
    assert nrfjprog_flash(hil_extras_get_path("build/zephyr/merged_domains.hex"), "NRF53") == 0

    logging.info("Resetting target...")
    assert jlink_fixture.reset_and_go()

    time.sleep(2)  # Sleep for a couple of seconds to let the target device start up


@pytest.fixture(scope="function", autouse=True)
def btmon_fixture(request, hil_results_open):

    btmon_out = hil_results_open("btmon.log", "w")

    p = subprocess.Popen(["btmon"], stdout=btmon_out, stderr=btmon_out)

    yield

    p.terminate()
    btmon_out.close()


@pytest.fixture
def serial_ble_address_fixture():

    """
    Fixture that uses the target's UART to retrieve the BLE address
    of the physically connected device. This is useful to distinguish
    between two advertising devices with the same name.
    """

    port_name = '/dev/ttyACM1'
    s = SerialInterface(port_name, baudrate=115200, read_timeout=0.5)

    # Data for communicating with target over serial
    mac_addr_command = "mac_address\n".encode()
    assert s.write(mac_addr_command) == len(mac_addr_command)

    response_bytes = s.read(BLE_ADDR_STR_LEN)
    assert len(response_bytes) == BLE_ADDR_STR_LEN

    connected_ble_addr = bytes.decode(response_bytes).strip()
    logging.info(f"Connected BLE address is {connected_ble_addr}")

    yield connected_ble_addr

    s.close()

@pytest_asyncio.fixture
async def ble_client_fixture(serial_ble_address_fixture):

    def filter_function(advertising_device):
        return advertising_device.address == serial_ble_address_fixture

    devices = await BLEScanner.find_devices(filter=filter_function)
    assert len(devices) == 1  # Only expect a single device with the given address

    device = devices[0]

    logging.info(f"Connecting to {device.name} ({device.address})...")

    client = BLEClient(device.address)
    connect_status = await client.connect()
    assert connect_status == True

    yield client

    await client.disconnect()

    logging.info("Disconnected!")


@pytest.fixture
def ble_shell_fixture(ble_client_fixture):

    return BLEShellService(ble_client_fixture)

@pytest.fixture
def ble_nus_fixture(ble_client_fixture):

    return BLENUSService(ble_client_fixture)

@pytest.fixture
def ble_dfu_fixture(ble_client_fixture):

    return BLEDFUService(ble_client_fixture)
