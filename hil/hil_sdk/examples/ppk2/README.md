# PPK2 Example Project

This example shows power-profiling with the Nordic PPK2 in ampere-meter mode. It is designed to
work with the nRF53DK but can easily be used with other hardware.

## nRF53DK Usage

One way to use this example code is with the nRF53 development kit. The trace of SB40 (directly behind connector P22) must be cut, making it open. Then, connect the PPK2 as follows:

- PPK2 GND to External Supply (P21) GND
- PPK2 VOUT (red wire) to the pin of P22 that is closest to the edge of the board
- PPK2 VIN (brown wire) to the pin of P22 that is closest to the USB connector

This effectively places the PPK2 in series with the nRF53DK's application processor power supply. The PPK2 itself must be plugged into the gateway with a micro-USB cable. Make sure you use the port labeled "DATA/POWER" and not the one for power only.

When you are done, simply install a jumper across P22 to restore normal DK operation.

## Other Systems

This example code can also be used with other development boards or hardware setups, provided you have the ability to insert the PPK2
in series with the processor's power supply. Refer to Nordic's [official documentation](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2) for instructions on connecting to a DUT.

This project consists of two files:

`conftest.py` - Implements a fixture that flashes firmware, connects
to the PPK2, and opens it for data collection

`test_ppk2.py` - Contains a test that collects current measurements and calculates average power consumption
