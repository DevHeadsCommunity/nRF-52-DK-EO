import time
import pylink
import logging
import threading
from multiprocessing import Queue
from .utility.child_worker import ChildWorker, ChildWorkerCommand, ChildWorkerResponse

# Timeout to wait for any command to complete
# IMPORTANT: This must be longer than the longest expected command completion time,
#     which is currently "open" at around 3 seconds
COMMAND_TIMEOUT      = 5.0
PROCESS_JOIN_TIMEOUT = 5.0  # Seconds to wait for child process to cleanup and join (based on observed execution)

# Child process interface defines
STATUS_OK    = 0
STATUS_ERROR = -1

class RTTInterface():

    """
    Provides an interface to read RTT messages via a connected J-Link.
    NOTE: When using this class, additional operations via the J-Link are not possible.
    """

    def __init__(self, target_cpu, outfile) -> None:

        """
        Create new instance and spawn child process, which will connect to the J-Link.
        Target CPU must match the J-Link naming convention (ie, "nRF5340_xxAA_APP")
        """

        self.target_cpu = target_cpu
        self.outfile_name = outfile
        self.outfile = None
        self.thread_exit_flag = False
        self.command_input_queue = Queue()
        self.command_output_queue = Queue()
        self.data_output_queue = Queue()
        self.child_process = RTTChildWorker(self.command_input_queue, self.command_output_queue, self.data_output_queue)
        self.child_process.start()

        threading.Thread(target=self._rtt_receive_thread).start()

    def start(self) -> bool:

        open_params = {"type": "open", "target_cpu": self.target_cpu}

        open_response = self._send_command("open", open_params)

        if open_response.status != STATUS_OK:
            logging.error(f"Unable to start RTT: {open_response.data}")
            return False

        # Open the outfile file
        self.outfile = open(self.outfile_name, "w")

        return True

    def stop(self) -> bool:

        """
        Explicitly kill the child process, which will release the J-Link.
        """

        self._send_command("close", None)
        self.thread_exit_flag = True

        if self.outfile is not None:
            self.outfile.close()

        if self.child_process is not None:

            # Wait five seconds for child to clean up gracefully before killing
            self.child_process.join(PROCESS_JOIN_TIMEOUT)

            if self.child_process.exitcode is None:
                self.child_process.kill()  # Force kill child process
                return False

        return True

    def _rtt_receive_thread(self):

        # Continuously listen for messages from the child process

        while not self.thread_exit_flag:

            try:
                out_data = self.data_output_queue.get(timeout=1)

                if self.outfile is not None:
                    self.outfile.write(out_data["data"] + "\n")
            except:
                pass  # Queue was empty

    def _send_command(self, command_type: str, data) -> ChildWorkerResponse:

        """Send a command via the input queue and wait for a result from the output"""

        try:
            self.command_input_queue.put(ChildWorkerCommand(command_type, data))
            return self.command_output_queue.get(timeout=COMMAND_TIMEOUT)  # This is just a sensible timeout
        except:
            # Queue was empty
            return ChildWorkerResponse(STATUS_ERROR, None)

class RTTChildWorker(ChildWorker):

    def __init__(self, command_input_queue: Queue, command_output_queue: Queue, data_output_queue: Queue):

        super().__init__(command_input_queue, command_output_queue)

        self.data_output_queue = data_output_queue

    def process_command(self, command: ChildWorkerCommand) -> ChildWorkerResponse:

        if command.command_type == "open":

            # The Linux method of resolving the dyanamic lib path is not reliable,
            # so we must use a hard-coded path
            lib = pylink.Library(dllpath="/opt/SEGGER/JLink_V790/libjlinkarm.so.7")
            self.jlink = pylink.JLink(lib=lib)
            self.jlink.open()
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            self.jlink.connect(command.data["target_cpu"])

            self._start_worker_thread()

            return ChildWorkerResponse(0, None)

        if command.command_type == "close":

            self.jlink.close()
            self._stop_worker_thread()
            self._stop_process()  # This should cause the process to join()

            return ChildWorkerResponse(0, None)

    def worker_thread_target(self):

        self.jlink.rtt_start(None)

        try:

            while self.jlink.connected() and not self.worker_exit_flag:

                terminal_bytes = self.jlink.rtt_read(0, 1024)

                if terminal_bytes:
                    msg = "".join(map(chr, terminal_bytes))
                    self.data_output_queue.put({"type": "data", "data":msg})

                time.sleep(0.1)

        except Exception as e:

            logging.error(f"RTT: IO read thread exception, exiting: {str(e)}")
            self.command_output_queue.put({"type": "error", "data": str(e)})
            return
