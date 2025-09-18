import os
import time
import re
import asyncio
import pytest
import pytest_asyncio
from collections import namedtuple

from hil_sdk.interfaces.ble.ble_scanner import BLEScanner
from hil_sdk.interfaces.ble.ble_client import BLEClient
from hil_sdk.interfaces.ble.nordic.ble_dfu_service import BLEDFUService

# Represents the current version of the example firmware
STARTING_FW_VERSION = b"0.2"

# Represents the version of the specially-built downgrade firmware
DOWNGRADE_FW_VERSION = b"0.1"

@pytest.mark.asyncio
async def test_ble_shell_ping(ble_shell_fixture):

    print('"ping" command is expected to return "pong"')

    cmd_response = await ble_shell_fixture.execute_command(["hil", "ping"])

    print(f"Ping shell response: {cmd_response}")

    assert str(cmd_response["o"]).strip() == "pong"


@pytest.mark.asyncio
async def test_ble_shell_uptime(ble_shell_fixture):

    print("Query DUT uptime")

    cmd_response = await ble_shell_fixture.execute_command(["hil", "uptime"])
    response_str = str(cmd_response["o"]).strip()

    print(f"Uptime shell response: {cmd_response}")

    assert re.match(r"\d+ days, \d+ hours, \d+ minutes, \d+ seconds", response_str) != None


@pytest.mark.asyncio
async def test_ble_shell_uptime_ms(ble_shell_fixture):

    sleep_time_secs = 5
    accuracy_secs = 1

    print("Test uptime accuracy (to within %d seconds over %d seconds)" % (accuracy_secs,sleep_time_secs))

    async def get_uptime_ms():
        cmd_response = await ble_shell_fixture.execute_command(["hil", "uptime-ms"])
        response_str = str(cmd_response["o"]).strip()

        return int(response_str)

    initial = await get_uptime_ms()

    await asyncio.sleep(sleep_time_secs)

    second = await get_uptime_ms()

    uptime_delta_ms = abs(second - initial)
    target_diff_ms = abs(sleep_time_secs*1000 - uptime_delta_ms)

    print(f"Initial uptime ms: {initial}")
    print(f"Second uptime ms: {second}")
    print(f"Target ms: {sleep_time_secs*1000}")
    print(f"difference in ms: {target_diff_ms}")

    # Allow 1 second of tolerance
    assert 0 < target_diff_ms < (accuracy_secs*1000)


@pytest.mark.asyncio
async def test_ble_nus(ble_nus_fixture):

    test_data = b"This is a test"
    was_called = False

    def rx_callback(uuid, data):
        assert data == test_data
        nonlocal was_called
        was_called = True

    await ble_nus_fixture.set_nus_received_cb(rx_callback)

    await ble_nus_fixture.write_nus(test_data)

    await asyncio.sleep(5)

    assert was_called


async def wait_for_advertising_device(device_address: str, timeout: int) -> bool:

    """Wait for a device with the given name to appear in a device scan.
    Returns true if the device appeared, or false if the search timed out."""

    total_scan_time = 0

    while total_scan_time < timeout:

        def filter_function(advertising_device):
            return advertising_device.address == device_address

        start_time = time.monotonic()
        devices = await BLEScanner.find_devices(filter=filter_function)

        if len(devices) > 0:
            return True

        total_scan_time += (time.monotonic() - start_time)
        print(f"Scanned for {round(total_scan_time, 2)} total seconds, {device_address} not found...")

    return False


@pytest.mark.asyncio
async def test_ble_dfu(ble_client_fixture, jlink_fixture):

    # This DFU test verifies the DFU functionality of the target by temporarily downgrading and then reverting the image.
    # This is possible by uploading the downgraded image and setting its status to "pending", which means it will be
    # swapped with the current image and executed once, but the swap is not permanent, and it will be reverted on the next reset.
    # This is a test mode offered by Zephyr that is a safe way to execute firmware upgrades. In the event that
    # the upgrade is not functional, it allows the user to refuse the confirmation, allowing the previous working
    # firmware to be restored.
    #
    # More information can be found here:
    # https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/mcuboot/design.html
    #
    # High-Level Test Flow
    #    1. Get current version and check that it matches the expected "new" version number
    #    2. Transfer downgrade image
    #    3. Mark downgrade image as pending
    #    4. Restart into downgrade image
    #    5. Verify dis service shows downgraded version number
    #    6. Reset, which will cause a reboot into the original "new" image
    #    7. Verify that the reversion was successful

    dfu_service = BLEDFUService(ble_client_fixture)

    # First, verify that we have the correct version of firmware loaded
    dis_fw_version_uuid = "00002A26-0000-1000-8000-00805F9B34FB"
    dis_fw_version = await ble_client_fixture.read_gatt(dis_fw_version_uuid)
    assert dis_fw_version == STARTING_FW_VERSION
    print(f"DIS Service is reporting v{dis_fw_version.decode('utf-8')} for the active firmware version")

    # Print starting partition state
    image_states = await dfu_service.get_state_of_images(verbose=True)

    # Specify downgrade file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_image = os.path.join(test_dir, "app_downgrade_0_1.bin")

    # Next, perform DFU to an "older" version of the software
    # app_update.bin is a part of this test and is an identical version of the stock FW
    # with version 0.1
    current_progress = 0
    def update_callback(offset, total_size):

        nonlocal current_progress

        percent = (100 * offset) // total_size

        if percent >= current_progress:
            print(f"DFU Progress: {percent}%")
            current_progress += 5

    # Perform DFU
    dfu_status = await dfu_service.image_upload(test_image, on_update=update_callback)
    assert dfu_status == True

    # Print partition state
    image_states = await dfu_service.get_state_of_images(verbose=True)

    # Set the state of the image's confirmation to "False" which marks it for temporary execution
    print("Setting DFU image to pending (temporary execution)")
    dfu_hash = image_states["images"][1]["hash"]
    await dfu_service.set_state_of_image(dfu_hash, False)

    # Reset, which will cause the nRF to load the newly DFU'd firmware in test mode
    await ble_client_fixture.disconnect()
    print("Resetting target after DFU...")
    jlink_fixture.reset_and_go()

    print("Sleeping for 10 seconds for update to be applied...")
    await asyncio.sleep(10)

    # Wait for the nRF to copy the image between flash banks
    device_found = await wait_for_advertising_device(ble_client_fixture.address, 60)
    assert device_found

    # Since the target has been offline for an extended amount of time (over 30 seconds),
    # it has disappeared from the BlueZ stack's device list. Therefore the Bleak backend
    # requires we create a new client object.
    new_client = BLEClient(ble_client_fixture.address)
    await new_client.connect()
    dfu_service = BLEDFUService(new_client)
    dis_fw_version = await new_client.read_gatt(dis_fw_version_uuid)
    assert dis_fw_version == DOWNGRADE_FW_VERSION
    print(f"DIS Service is reporting v{dis_fw_version.decode('utf-8')} for the active firmware version")

    # Print partition state information
    image_states = await dfu_service.get_state_of_images(verbose=True)

    await new_client.disconnect()
    print("Resetting target to revert temporary execution of downgrade DFU...")
    jlink_fixture.reset_and_go()

    print("Sleeping for 10 seconds for update to be reverted...")
    await asyncio.sleep(10)

    # Wait for the nRF to copy the image between flash banks
    device_found = await wait_for_advertising_device(new_client.address, 60)
    assert device_found

    # A new client object is needed (see previous comment)
    new_client = BLEClient(ble_client_fixture.address)
    await new_client.connect()
    dfu_service = BLEDFUService(new_client)
    dis_fw_version = await new_client.read_gatt(dis_fw_version_uuid)
    assert dis_fw_version == STARTING_FW_VERSION
    print(f"DIS Service is reporting v{dis_fw_version.decode('utf-8')} for the active firmware version")

    # Print partition state information
    image_states = await dfu_service.get_state_of_images()

    await new_client.disconnect()


@pytest.mark.asyncio
async def test_ble_reconnect(ble_client_fixture, request):

    # We enter this function just having connected to the DUT
    print("Disconnect from %s" % ble_client_fixture._client_obj.address)
    await ble_client_fixture.disconnect()

    # Immediately try to reconnect to the device, capture the timeout error on connection failure
    print("Attempt to connect to %s" % ble_client_fixture._client_obj.address)
    try:
        await ble_client_fixture.connect()
    except TimeoutError:
        print("%s: got timeout while trying to connect to ble client %s" % (request.node.name, ble_client_fixture._client_obj.address))

    connected = await ble_client_fixture.is_connected()
    assert(connected)


@pytest.mark.asyncio
async def test_ble_disconnect_and_advertise(ble_client_fixture, request):

    # We enter this function just having connected to the DUT
    device_address = ble_client_fixture.address
    print("Disconnect from %s" % device_address)
    await ble_client_fixture.disconnect()

    # Check to see if device has started advertising again after disconnect
    print("Scan for advertising devices")

    def filter_function(advertising_device):
            return advertising_device.address == device_address

    devices = await BLEScanner.find_devices(filter=filter_function)
    assert len(devices) == 1


dis_service = namedtuple("dis_service", "uuid name value")

dis_services = [
    dis_service("2A24", "CONFIG_BT_DIS_MODEL", "EmbedOps HIL Demo Device"),
    dis_service("2A29", "CONFIG_BT_DIS_MANUF", "Dojo Five"),
    dis_service("2A25", "CONFIG_BT_DIS_SERIAL_NUMBER_STR", "EmbedOps Serial"),
    dis_service("2A26", "CONFIG_BT_DIS_FW_REV_STR", "0.2"),
]

# Uncomment the following code block to add the device information service PyTest
@pytest.mark.asyncio
async def test_ble_device_information_service(ble_client_fixture):
    for service in dis_services:
        uuid = service.uuid.lower()
        print(str(service))
        print(str(ble_client_fixture.lookup_uuid_name(uuid)))
        data = await ble_client_fixture.read_gatt(uuid)
        print(str(data))
        assert(service.value == data.decode("utf-8"))
