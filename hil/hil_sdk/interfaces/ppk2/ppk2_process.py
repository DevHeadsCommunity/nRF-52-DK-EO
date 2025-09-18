import time
import serial
from multiprocessing import Queue
from threading import Lock
from multiprocessing import Lock
from ..utility.child_worker import ChildWorker, ChildWorkerCommand, ChildWorkerResponse

GET_METADATA_BYTES   = bytearray([0x19])
RESET_BYTES          = bytearray([0x20])
RESET_TIMEOUT        = 3.0  # Seconds to wait after resetting, before attempting to open again
GET_METADATA_TIMEOUT = 1.0  # Seconds to wait after requesting metadata

class PPK2Process(ChildWorker):

    def __init__(self, command_input_queue: Queue, command_output_queue: Queue):

        super().__init__(command_input_queue, command_output_queue)

        self.serial_lock = Lock()
        self.input_buffer = bytearray()

    def process_command(self, command: ChildWorkerCommand) -> ChildWorkerResponse:

        if command.command_type == "open":

            # Attempt to open port prior to starting thread
            try:
                self.port = serial.Serial(command.data)
            except Exception as e:
                return ChildWorkerResponse(-1, str(e))

            # Prior to getting metadata, reset the device
            self.port.write(RESET_BYTES)
            self.port.close()
            time.sleep(RESET_TIMEOUT)

            self.port = serial.Serial(command.data)

            # Prior to starting the worker thread, we want to get the metadata to return to parent
            metadata_bytes = self._get_metadata()

            self.port.reset_input_buffer()  # Discard any stray data

            # Kick off the thread which periodically reads data and sends to parent process via Queue
            self._start_worker_thread()

            return ChildWorkerResponse(0, metadata_bytes)

        elif command.command_type == "close" and self.port is not None:

            self._stop_worker_thread()

            self.serial_lock.acquire()

            # Send a reset command
            self.port.write(RESET_BYTES)

            self.port.close()

            self._stop_process()  # This should cause the process to join()

            return ChildWorkerResponse(0, None)

        elif command.command_type == "read_and_flush":

            data = self.input_buffer.copy()
            self.input_buffer.clear()
            return ChildWorkerResponse(0, data)

        elif command.command_type == "write" and self.port is not None:

            bytes_written = self.port.write(command.data)
            return ChildWorkerResponse(0, bytes_written)

    def worker_thread_target(self):

        # When we stream, we have exclusive usage of the serial port
        self.serial_lock.acquire()

        while not self.worker_exit_flag:

            read_data = self.port.read(self.port.in_waiting)

            if len(read_data) > 0:
                self.input_buffer.extend(read_data)

        self.serial_lock.release()

    def _get_metadata(self):

        self.port.write(GET_METADATA_BYTES)  # Command for triggering metadata send
        time.sleep(GET_METADATA_TIMEOUT)  # Give the PPK2 enough time to send all metadata

        bytes_read = self.port.read(self.port.in_waiting)
        return bytes_read
