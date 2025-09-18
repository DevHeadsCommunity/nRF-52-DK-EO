import threading
from multiprocessing import Process, Queue

# Types for the commands and their responses
class ChildWorkerCommand:

    def __init__(self, command_type: str, data) -> None:
        self.command_type = command_type
        self.data = data

class ChildWorkerResponse:

    def __init__(self, status: int, data) -> None:
        self.status = status
        self.data = data

class ChildWorker(Process):

    """
    Template class for a basic child worker process that continuously listens for
    commands from a parent class.
    """

    def __init__(self, command_input_queue: Queue, command_output_queue: Queue):

        super().__init__()

        self.command_input_queue = command_input_queue
        self.command_output_queue = command_output_queue

        self.worker_thread = None      # Worker thread reference
        self.run_exit_flag = False     # Used to stop the run() method to exit gracefully
        self.worker_exit_flag = False  # Used to stop child worker thread

    def run(self):

        """
        Continuously receive commands from the parent process.
        """

        while not self.run_exit_flag:

            input_obj = self.command_input_queue.get()
            command_result = self.process_command(input_obj)

            self.command_output_queue.put(command_result)

    def process_command(self, command: ChildWorkerCommand) -> ChildWorkerResponse:

        """
        Must be implemented by child class
        """

        raise NotImplementedError

    def worker_thread_target(self):

        """
        Must be implemented by child class
        """

        raise NotImplementedError

    def _start_worker_thread(self):

        """
        Starts the child worker thread
        """

        self.worker_thread = threading.Thread(target=self.worker_thread_target)
        self.worker_thread.start()

    def _stop_worker_thread(self, timeout = None):

        """
        Stops the child worker thread and waits for its termination.
        """

        if self.worker_thread is not None and self.worker_thread.is_alive:
            self.worker_exit_flag = True
            self.worker_thread.join(timeout=timeout)


    def _stop_process(self):

        """
        Stop ourselves by interrupting the run() method
        """

        self.run_exit_flag = True
