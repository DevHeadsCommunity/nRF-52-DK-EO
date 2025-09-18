# BLE Shell Example Project

This example shows testing of a device's shell using ``BLEShellService``. It sends a simple ping command that is expected 
to be implemented by the target device.

It consists of two files:

`conftest.py` - Implements a fixture that connects to the first device with `EmbedOps` in the name.

`test_shell.py` - Contains a test that executes a single shell command.

This test also makes use of the `pytest-asyncio` module, which adds `asyncio` capabilities to PyTest.