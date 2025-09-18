#
# Copyright (C) 2025, Dojo Five
# All rights reserved.
#

import socket

class TCPServer():
    def __init__(self, hostname: str, port: int):
        """
        Initialize the TCP server.

        :param hostname: The hostname or IP address to bind the server to.
        :param port: The port number to listen on.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((hostname, port))
        self.socket.listen()
        self.conn = None
        self.connected = False

    def connect(self):
        """
        Accept a connection from a client.
        """
        self.conn, addr = self.socket.accept()
        print(f"Connected by {addr}")
        self.connected = True

    def close(self):
        """
        Close the TCP connection.
        """
        self.socket.close()

    def send(self, data):
        """
        Send data to the connected client.

        :param data: The data to send (bytes).
        """
        if not self.connected:
            raise RuntimeError("TCP server is not connected to a client")
        self.conn.sendall(data)

    def receive(self, buffer_size: int = 1024):
        """
        Receive data from the connected client.

        :param buffer_size: The maximum amount of data to receive at once (default: 1024).
        """
        if not self.connected:
            raise RuntimeError("TCP server is not connected to a client")
        return self.conn.recv(buffer_size)

class TCPClient():
    def __init__(self, hostname: str, port: int):
        """
        Initialize the TCP client.

        :param hostname: The hostname or IP address to connect to.
        :param port: The port number to connect to.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostname = hostname
        self.port = port
        self.connected = False

    def connect(self):
        """
        Connect to the TCP server.
        """
        self.socket.connect((self.hostname, self.port))
        self.connected = True

    def close(self):
        """
        Close the TCP connection.
        """
        self.socket.close()

    def send(self, data):
        """
        Send data to the connected server.

        :param data: The data to send (bytes).
        """
        if not self.connected:
            raise RuntimeError("TCP client is not connected to a server")
        self.socket.sendall(data)

    def receive(self, buffer_size: int = 1024):
        """
        Receive data from the connected server.

        :param buffer_size: The maximum amount of data to receive at once (default: 1024).
        """
        if not self.connected:
            raise RuntimeError("TCP client is not connected to a server")
        return self.socket.recv(buffer_size)
