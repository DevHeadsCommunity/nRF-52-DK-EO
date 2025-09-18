import time
import serial
import logging
from multiprocessing import Queue
from .SnifferAPI import Sniffer
from ...utility.child_worker import ChildWorker, ChildWorkerCommand, ChildWorkerResponse

class BLESnifferProcess(ChildWorker):

    """
    A child process class that communicates with the Nordic BLE Sniffer
    and outputs all packets to the given PCAP file.

    This process uses the SnifferAPI which available from the "Downloads section of this link:
    https://www.nordicsemi.com/Products/Development-tools/nRF-Sniffer-for-Bluetooth-LE/Download?lang=en#infotabs

    Specifically, this code uses this SnifferAPI version:
    https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/desktop-software/nrf-sniffer/sw/nrf_sniffer_for_bluetooth_le_4.1.1.zip

    This ZIP file also contains documentation concerning the SnifferAPI and how to properly use it.
    """

    def __init__(self, command_input_queue: Queue, command_output_queue: Queue):

        super().__init__(command_input_queue, command_output_queue)

        self.sniffer = None
        self.outfile = None
        self.device_address = None

    def process_command(self, command: ChildWorkerCommand) -> ChildWorkerResponse:

        if command.command_type == "open":

            self.outfile = command.data["outfile"]

            if self.outfile is None:
                return ChildWorkerResponse(-1, "Outfile path must be specified")

            self.serial_port = command.data["serial_port"]
            self.device_address = command.data["device_address"]
            self.address_is_random = command.data["address_is_random"]

            # Parse the string address into bytes
            if self.device_address is not None:
                b_values_str = self.device_address.split(":")
                self.device_address = [int(b, 16) for b in b_values_str]
                self.device_address.append(1 if self.address_is_random else 0)

            self.sniffer = self._open_sniffer(self.serial_port, self.outfile)

            if self.sniffer is None:
                return ChildWorkerResponse(-1, "Sniffer object was none")

            self._start_worker_thread()

            return ChildWorkerResponse(0, None)

        elif command.command_type == "close":

            self.sniffer.doExit()

            self._stop_worker_thread()
            self._stop_process()  # This should cause the process to join()

            return ChildWorkerResponse(0, None)

    def worker_thread_target(self):

        # Start the sniffer module. This call is mandatory.
        self.sniffer.start()

        # Scan for new advertisers
        self.sniffer.scan()

        for _ in range(10):

            time.sleep(1)
            devices = self.sniffer.getDevices()
            logging.debug(f"Sniffer devices list: {devices}")

            filtered = [devices.find(self.device_address)]

            # We have to choose a single device
            logging.debug(f"Sniffer devices filtered list: {filtered}")
            if len(filtered) > 0:
                logging.debug(f"Sniffer following {filtered[0]}")
                self.sniffer.follow(filtered[0])
                break

        while not self.worker_exit_flag:
            time.sleep(1)  # Idle

    def _open_sniffer(self, serial_port: str, outfile: str):

        ports = [serial_port] # For now, the serial port must be hardcoded

        if len(ports) > 0:
            # Initialize the sniffer on the first port found with baudrate 1000000.
            # If you are using an old firmware version <= 2.0.0, simply remove the baudrate parameter here.
            return Sniffer.Sniffer(portnum=ports[0], baudrate=1000000, capture_file_path=outfile)
        else:
            logging.error("No BLE sniffer devices found!")
            return None
