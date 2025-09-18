#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import serial
from enum import Enum

# These Enum classes help bind our SDK types directly to backend type values (pyserial, in this case)

class SerialByteSize(Enum):
    FIVE  = serial.FIVEBITS
    SIX   = serial.SIXBITS
    SEVEN = serial.SEVENBITS
    EIGHT = serial.EIGHTBITS

class SerialParity(Enum):
    NONE  = serial.PARITY_NONE
    EVEN  = serial.PARITY_EVEN
    ODD   = serial.PARITY_ODD
    MARK  = serial.PARITY_MARK
    SPACE = serial.PARITY_SPACE

class SerialStopBits(Enum):
    ONE            = serial.STOPBITS_ONE
    ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
    TWO            = serial.STOPBITS_TWO

class SerialInterfaceException(Exception):
    pass

class SerialInterface:

    """Provides a serial/UART interface"""

    def __init__(self,
                 port: str,
                 baudrate: int = 9600,
                 bytesize: SerialByteSize = SerialByteSize.EIGHT,
                 parity: SerialParity = SerialParity.NONE,
                 stopbits: SerialStopBits = SerialStopBits.ONE,
                 read_timeout: float = None,
                 write_timeout: float = None,
                 sw_flow_control: bool = False,
                 hw_rtscts_flow_control: bool = False,
                 hw_dsrdtr_flow_control: bool = False,
                ):

        """
        Create and open a new serial port interface. If the port could not be opened,
        a SerialInterfaceException is thrown

        :param port: Name of the port to open

        :param baudrate: Baudrate of the port (9600 by default)

        :param bytesize: Size, in bits, of a byte

        :param parity: Parity checking value

        :param stopbits: Number of stopbits

        :param read_timeout: Timeout of read operations (in seconds). None for infinite timeout; 0 for non-blocking.

        :param write_timeout: Timeout of write operations (in seconds). Defaults to blocking.

        :param sw_flow_control: Enables software flowcontrol

        :param hw_rtscts_flow_control: Enables hardware RTS/CTS flowcontrol

        :param hw_dsrdtr_flow_control: Enables hardware DSR/DTR flowcontrol
        """

        self.port = None

        try:

            # Attempt to open
            self.port = serial.Serial(port=port,
                                      baudrate=baudrate,
                                      bytesize=bytesize.value,
                                      parity=parity.value,
                                      stopbits=stopbits.value,
                                      timeout=read_timeout,
                                      write_timeout=write_timeout,
                                      xonxoff=sw_flow_control,
                                      rtscts=hw_rtscts_flow_control,
                                      dsrdtr=hw_dsrdtr_flow_control
                                      )

        except (ValueError, serial.SerialException) as exc:
            raise SerialInterfaceException() from exc

    def write(self, data: bytes | bytearray) -> int:

        """
        Write data to the serial interface.

        :param data: Data to write to port

        :return: Number of bytes written to port.
        :rtype: int
        """

        if self.port is not None:
            return self.port.write(data)
        else:
            raise SerialInterfaceException("Cannot write to a port that is not open.")

    def read(self, size: int = 1) -> bytes:

        """
        Read data from the serial interface.

        :param size: Number of bytes to read (defaults to 1).

        :return: Bytes read from the serial interface (or None in case of error).
        :rtype: bytes
        """

        if self.port is not None:
            return self.port.read(size=size)
        else:
            raise SerialInterfaceException("Cannot read from a port that is not open.")

    def close(self) -> None:

        """
        Close the serial port interface.
        """

        if self.port is not None:
            self.port.close()
        else:
            raise SerialInterfaceException("Cannot close a port that is not open.")

    def flush_input(self) -> None:

        """
        Flush the input buffer.
        """

        if self.port is not None:
            self.port.reset_input_buffer()
        else:
            raise SerialInterfaceException("Cannot flush a port that is not open.")
        
    def flush_output(self) -> None:

        """
        Flush the output buffer.
        """

        if self.port is not None:
            self.port.reset_output_buffer()
        else:
            raise SerialInterfaceException("Cannot flush a port that is not open.")

    def in_waiting(self) -> int:

        """
        Return the number of bytes currently in the input buffer.
        """

        if self.port is not None:
            return self.port.in_waiting
        else:
            raise SerialInterfaceException("Cannot get in_waiting on a port that is not open.")

