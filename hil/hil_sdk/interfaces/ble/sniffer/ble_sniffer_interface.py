import logging
from multiprocessing import Queue
from .ble_sniffer_process import BLESnifferProcess
from ...utility.child_worker import ChildWorkerCommand, ChildWorkerResponse

# Timeout to wait for any command to complete
# IMPORTANT: This must be longer than the longest expected command completion time,
#     which is currently "open" at around 3 seconds
COMMAND_TIMEOUT      = 5.0
PROCESS_JOIN_TIMEOUT = 5.0  # Seconds to wait for child process to cleanup and join (based on observed execution)

# Child process interface defines
STATUS_OK    = 0
STATUS_ERROR = -1

class BLESnifferInterface:

    """
    Provides an interface to a Nordic BLE sniffer module, connected via serial port.
    This interface creates PCAP files by managing a child process that runs separately
    from the tests to optimally use multiple CPUs.
    """

    def __init__(self, serial_port) -> None:

        """
        Create a BLESnifferInterface.

        :param serial_port: Name of BLE sniffer serial port
        """

        self.serial_port = serial_port
        self.child_process = None

    def start_sniffing(self, outfile: str, device_address: str, address_is_random: bool = True) -> bool:

        """
        Start sniffing for a specific device by address.

        :param outfile: Name of output pcap file

        :param device_address: Address (as a string of octet values separated by colons) of device to follow

        :param address_is_random: True if address is random (default), False if address is public

        :return: True on success, False otherwise
        :rtype: bool
        """

        # Create and start the child process
        self.command_input_queue = Queue(maxsize=1)
        self.command_output_queue = Queue()
        self.child_process = BLESnifferProcess(self.command_input_queue, self.command_output_queue)
        self.child_process.start()

        open_params = {"device_address": device_address,
                       "address_is_random": address_is_random,
                       "outfile": outfile,
                       "serial_port": self.serial_port}

        open_response = self._send_command("open", open_params)

        if open_response.status != STATUS_OK:
            logging.error(f"Unable to start sniffing: {open_response.data}")
            return False

        return True

    def stop_sniffing(self) -> bool:

        """
        Close the sniffer, stop the child process and cleanup all resources.
        This function may block while the child process is joining.

        :return: True on success, False otherwise
        :rtype: bool
        """

        # For safety, reset prior to closing
        self._send_command("close", None)

        if self.child_process is not None:

            # Wait five seconds for child to clean up gracefully before killing
            self.child_process.join(PROCESS_JOIN_TIMEOUT)

            if self.child_process.exitcode is None:
                self.child_process.kill()  # Force kill child process
                return False

        return True

    def _send_command(self, command_type: str, data) -> ChildWorkerResponse:

        """Send a command via the input queue and wait for a result from the output"""

        try:
            self.command_input_queue.put(ChildWorkerCommand(command_type, data))
            return self.command_output_queue.get(timeout=COMMAND_TIMEOUT)  # This is just a sensible timeout
        except:
            # Queue was empty
            return ChildWorkerResponse(STATUS_ERROR, None)
