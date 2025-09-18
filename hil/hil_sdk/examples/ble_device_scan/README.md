# BLE Device Scan Example Project

This example project shows the minimum necessary code to scan for advertising BLE devices and read the corresponding data.
This example is designed to work with the HIL nRF53 demo project, which by default will advertise the DIS service with 
the name "EmbedOps HIL Demo Device".

NOTE: The `find_devices` function provided by the `BLEInterface` class is asynchronous and uses Python's built-in
`asyncio` library. This requires a small amount of boilerplate code to exist in your test functions, which can be seen 
within the `test_ble_scan` function in this example project.

`conftest.py` - This file implements a fixture which creates and returns an instance of `BLEInterface`.
`test_ble_device_scan.py` - This file contains a test that searches for an advertising device with a specific name.
