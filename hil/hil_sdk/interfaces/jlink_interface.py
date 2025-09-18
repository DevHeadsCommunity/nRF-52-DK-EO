#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

"""Provide an interface to the J-Link Command program through a Python interface"""
import os
import tempfile
import subprocess
import platform

if platform.system() == "Windows":
    JLINK_CMD = "JLink.exe"
else:
    JLINK_CMD = "JLinkExe"


class JLinkInterface:

    """Represents an instance of a J-Link Debugger"""

    def __init__(self, device, interface='SWD', speed=4000) -> None:

        """
        Create a new J-Link instance. Note that this constructor does not attempt to communicate to the J-Link; that is done
        on subsequent function calls.

        :param device: Name of the device target processor
        :type device: str
        :param interface: Interface via which to connect to the target (defaults to SWD)
        :type interface: str
        :param speed: Connection speed (default 4000 KHz)
        :type speed: int
        """

        self.device = device
        self.interface = interface
        self.speed = speed

    def load_file(self, filename: str, logfile: str = None) -> bool:

        """Load a file onto the target device via the J-Link. Note that this function does not support .bin files as they
        require an offset address.

        :param filename: Path of the file to be loaded

        :param logfile: Optional path to a file that JLink Commander will write logs to

        :return: Status of operation (True on success, False otherwise)
        :rtype: bool
        """

        if not os.path.isfile(filename):
            return False

        try:

            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

            full_path = os.path.abspath(filename)
            temp_file.write(f"loadfile {full_path}\n")
            temp_file.write("q\n")
            temp_file.close()

            args = self._build_args(temp_file.name)
            ret = self._execute_args(args, logfile)
            os.remove(temp_file.name)

            return ret

        except Exception as e:
            os.remove(temp_file.name)
            return False

    def reset_and_go(self, logfile: str = None) -> bool:

        """Perform a reset of the target device.

        :param logfile: Optional path to a file that JLink Commander will write logs to

        :return: Status of operation (True on success, False otherwise)
        :rtype: bool
        """

        try:

            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

            temp_file.write("r\n")
            temp_file.write("Sleep 2000\n")
            temp_file.write("g\n")
            temp_file.write("q\n")
            temp_file.close()

            args = self._build_args(temp_file.name)
            ret = self._execute_args(args, logfile)
            os.remove(temp_file.name)

            return ret

        except Exception as e:
            os.remove(temp_file.name)
            return False

    def run_commands(self, commands: list[str], logfile: str = None) -> bool:

        """Run a series of J-Link Commands as you would find in a script file.
        Example commands are loadfile, reset, go, etc. Each element in the array
        is a command and its arguments, for example:
        commands = ['reset', 'loadfile /build/fw.hex', 'exit']

        Commands can be found at https://wiki.segger.com/J-Link_Commander.

        :param commands: List of commands to execute

        :param logfile: Optional path to a file that JLink Commander will write logs to

        :return: Status of operation (True on success, False otherwise)
        :rtype: bool
        """

        try:

            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
            
            for command in commands:
                temp_file.write(f"{command}\n")
            temp_file.close()

            args = self._build_args(temp_file.name)
            ret = self._execute_args(args, logfile)
            os.remove(temp_file.name)

            return ret

        except Exception as e:
            os.remove(temp_file.name)
            return False

    def _build_args(self, command_file: str) -> str:

        """
        Internal function to build a connection args string based on the initial values from the constructor
        :param command_file: Path to command file
        :return: Full argument string that can be passed to the J-Link commander
        """

        device_args    = f"-device {self.device}" if self.device else ""
        interface_args = f"-if {self.interface}" if self.interface else ""
        speed_args     = f"-speed {str(self.speed)}" if self.speed else ""

        return f" {device_args} {interface_args} {speed_args} -ExitOnError 1 -CommandFile {command_file}"

    def _execute_args(self, args, logfile) -> bool:

        """
        Execute a set of full arguments, optionally log to a file,
        and return the status of the execution.
        """

        ret_proc = subprocess.run(f"{JLINK_CMD} {args}",
                                    shell=True, 
                                    text=True,
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)
        
        # Optionally log the stdout/stderr combination to a file
        if logfile is not None:
            with open(logfile, "w") as log_out:
                log_out.write(ret_proc.stdout)
                
        return ret_proc.returncode == 0


