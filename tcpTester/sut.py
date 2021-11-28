import logging
import socket
import random
from typing import cast

from tcpTester.types import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    UserCall,
    UserCallResult,
    UserCallResultType
)

MAX_READ_SIZE = 4096  # in bytes
TIMEOUT = 20

class SUT:
    """
    Implementation of the System Under Test (SUT)
    """

    def __init__(self, ts_ip: str):
        """
        Initializes class variables.
        """
        self.logger.info("SUT started")

        self.ts_ip = ts_ip

        # Socket for communicating with another TCP endpoint.
        self.client_socket = None
        # Socket for connecting with another TCP endpoint.
        self.socket = None

    @property
    def logger(self):
        """
        Returns the logger used for the SUT

        :return: The logger for the SUT
        """
        return logging.getLogger("SUT")

    def handle_user_call(self, user_call: UserCall) -> UserCallResult:
        if user_call.command_type == CommandType["LISTEN"]:
            return self.handle_listen_call(cast(ListenParameters, user_call.command_parameters))
        if user_call.command_type == CommandType["CONNECT"]:
            return self.handle_connect_call(cast(ConnectParameters, user_call.command_parameters))
        if user_call.command_type == CommandType["SEND"]:
            return self.handle_send_call(cast(SendParameters, user_call.command_parameters))
        if user_call.command_type == CommandType["RECEIVE"]:
            return self.handle_receive_call()
        if user_call.command_type == CommandType["CLOSE"]:
            return self.handle_close_call()

        return UserCallResult(UserCallResultType.FAILURE)

    def reset(self):
        """
        Resets the sockets used to connect to and communicate with another TCP endpoint.
        """
        self.socket = None
        self.client_socket = None

    def handle_connect_call(self, parameters: ConnectParameters):
        """
        Establishes a new connection with another TCP endpoint.
        """
        self.logger.info("Attempting to connect to %s", parameters.dst_port)

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(TIMEOUT)
            self.client_socket.bind(("", parameters.src_port))
            self.logger.info("bind successful")
            self.client_socket.connect((self.ts_ip, parameters.dst_port))

        except Exception:
            return UserCallResult(status=UserCallResultType.FAILURE)

        self.logger.info("connection successful")

        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_listen_call(self, parameters: ListenParameters):
        """
        Passively listens for an incoming connection request from another TCP endpoint.
        """

        # clear any previous sockets
        self.reset()

        self.logger.info("starting socket on %s", parameters.src_port)
        try:

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.bind(("", parameters.src_port))
            self.socket.listen(1)

            self.logger.info("bind and listen successful")

            (self.client_socket, _) = self.socket.accept()

            self.logger.info("received client connect")

        except Exception:
            return UserCallResult(status=UserCallResultType.FAILURE)

        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_send_call(self, parameters: SendParameters):
        """
        Sends a given payload to the TCP endpoint with which the SUT is connected.
        """
        self.logger.info("sending packet to client")
        if not self.client_socket:
            return UserCallResult(status=UserCallResultType.FAILURE)

        try:
            num_bytes = self.client_socket.send(parameters.payload)
        except Exception:
            return UserCallResult(status=UserCallResultType.FAILURE)

        self.logger.info("sending completed")

        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_receive_call(self):
        """
        Receives a single packet from the TCP endpoint with which the SUT is connected.
        """
        self.logger.info("receiving packet from client")
        if not self.client_socket:
            return UserCallResult(status=UserCallResultType.FAILURE)

        try:
            payload = self.client_socket.recv(MAX_READ_SIZE)
        except Exception:
            return UserCallResult(status=UserCallResultType.FAILURE)

        self.logger.info("receive completed")
        return UserCallResult(status=UserCallResultType.RECEIVE, payload=payload)

    def handle_close_call(self):
        """
        Disconnects the connection between the SUT and the other TCP endpoint.
        """

        self.logger.info("disconnecting from client")
        if self.client_socket:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
            self.reset()
            self.logger.info("disconnect completed")
            return UserCallResult(status=UserCallResultType.SUCCESS)

        self.logger.info("disconnect failed")
        return UserCallResult(status=UserCallResultType.FAILURE)
