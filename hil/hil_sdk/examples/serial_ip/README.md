# Serial-IP Example Project

This example showcases the functionality of a serial-to-IP converter. Any messages that come in to the serial port are sent over TCP to the remote server/client. This example assumes that a serial communication channel exists between the HIL Gateway and the DUT and that the DUT has network access to the HIL Gateway.

It consists of two files:

`conftest.py` - Implements a fixture that returns a `SerialInterface()` interface and a fixture that returns a `TCPServer()`.

`test_serial_ip.py` - Contains a test that sends a message over serial to the DUT and receives the same message back from the DUT over TCP.
