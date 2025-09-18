#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import paramiko
from paramiko import SSHClient
from scp import SCPClient

class RemoteInterface():

    """Provides an interface for remote device communication over SSH and SCP."""

    def __init__(self, hostname: str, username: str | None = None, password: str | None = None) -> None:
        """
        Create a new RemoteInterface instance.

        :param hostname: The hostname or IP address of the remote device.
        :param username: The username to use for authentication (optional).
        :param password: The password to use for authentication (optional).
        """
        self.ssh = SSHClient()
        # WARNING: This automatically adds the host key to ~/.ssh/known_hosts if it's new. While convenient for automation,
        # it bypasses host key verification and increases the risk of man-in-the-middle attacks.
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {hostname}...")
        self.ssh.connect(hostname=hostname, username=username, password=password)

    def scp_send(self, files_to_be_sent: str, remote_path: str = b'.', recursive=False) -> None:
        """
        Send files to the remote device using SCP.

        :param files_to_be_sent: The files to send (can be a single file or a directory).
        :param remote_path: The destination path on the remote device (defaults to the current directory).
        :param recursive: Whether to send directories recursively (defaults to False).
        """
        scp = SCPClient(self.ssh.get_transport())
        print(f"Sending {files_to_be_sent} to the remote device...")
        scp.put(files=files_to_be_sent, remote_path=remote_path, recursive=recursive)
        scp.close()

    def scp_receive(self, files_to_be_received: str, local_path: str = b'', recursive=False) -> None:
        """
        Receive files from the remote device using SCP.

        :param files_to_be_received: The files to receive (can be a single file or a directory).
        :param local_path: The destination path on the local device (defaults to the current directory).
        :param recursive: Whether to receive directories recursively (defaults to False).
        """
        scp = SCPClient(self.ssh.get_transport())
        print(f"Receiving {files_to_be_received} from the remote device...")
        scp.get(remote_path=files_to_be_received, local_path=local_path, recursive=recursive)
        scp.close()

    def ssh_exec(self, command: str) -> str:
        """
        Execute a command on the remote device via SSH.

        :param command: The command to execute.
        :return: The output of the command.
        """
        print(f"Executing {command} on the remote device...")
        stdin, stdout, stderr = self.ssh.exec_command(command=command, get_pty=True)
        command_output = []

        for line in iter(stdout.readline, ""):
            print(line, end="")
            command_output.append(line)

        command_output_string = "".join(command_output)
        return command_output_string
