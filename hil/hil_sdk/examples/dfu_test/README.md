# BLE DFU Example Project

This example shows testing of the DFU process using a test blinky image. It uploads the test blinky image to the device,
and verifies it was uploaded correctly (it does not confirm the image, so it will never be executed on the target device).

It consists of two files:

`conftest.py` - Implements a fixture that connects to the first device with `EmbedOps` in the name.

`test_dfu.py` - Contains a test that sends data and asserts that the DFU process was successful.

This test also makes use of the `pytest-asyncio` module, which adds `asyncio` capabilities to PyTest.