#
# Copyright (C) 2024, Dojo Five
# All rights reserved.
#
import sys
from enum import Enum

# Allows code to be imported on non-Pi systems (eg for building docs)
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except:
    # Create a mock GPIO object to allow the rest of the code to be imported
    GPIO = obj = type('GPIO', (object,), {})
    GPIO.IN = 1
    GPIO.OUT = 0


class GPIOPinMode(Enum):
    """
    Enum for pin modes.
    """
    INPUT  = GPIO.IN
    OUTPUT = GPIO.OUT


class GPIOInterface:
    """
    Interface to the Raspberry Pi GPIO module.
    Pin numbering used by functions is identical to the numbers on the 40-pin header.
    A diagram can be found at: https://pinout.xyz/.
    """

    @staticmethod
    def setup_pin(pin: int | list[int], mode: GPIOPinMode):
        """
        Setup a pin for either input or output. This must be done prior to any read or write operations.

        :param pin: Pin number (or list of pin numbers) to be setup. The pin numbering scheme matches the header pins
          on the Raspberry Pi.
        :param mode: Mode to assign to given pin(s).
        """
        GPIO.setup(pin, mode.value)

    @staticmethod
    def read_pin(pin: int) -> bool:
        """
        Read the value of a single pin.

        :param pin: Pin number to read.
        :return: True if pin is high, False otherwise.
        """
        return GPIO.input(pin) == GPIO.HIGH

    @staticmethod
    def write_pin(pin: int | list[int], value: bool):
        """
        Write to a GPIO pin or multiple pins.

        :param pin: Pin number (or a list of pin numbers) to write to.
        :param value: Value to write to pin (True for HIGH, False for LOW).
        """
        GPIO.output(pin, value)

    @staticmethod
    def cleanup():
        """
        Clean up resources and reset pins to default states.
        NOTE: It is important to call this function prior to exiting your script
        to avoid accidental damage to the GPIO module.
        """
        GPIO.cleanup()
