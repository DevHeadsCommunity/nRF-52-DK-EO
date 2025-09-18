# BLE NUS Example Project

This example shows testing of a device that has NUS echo implemented. 
NUS is the Nordic UART service, which is a BLE service that allows reading and writing 
data similar to a traditional UART interface. Use this test for any device that has NUS echo; that is,
it sends back whatever is sent to it. 
This example is designed to work with the HIL nRF53 demo project, which by default will advertise 
with the name "EmbedOps HIL Demo Device" and has a NUS echo implemented.

It consists of two files:

`conftest.py` - Implements a fixture that connects to the first device with `EmbedOps` in the name.

`test_nus_echo.py` - Contains a test that sends data and asserts that the received data is the same as what was sent.

This test also makes use of the `pytest-asyncio` module, which adds `asyncio` capabilities to PyTest.
