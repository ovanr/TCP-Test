import logging
import socket
import random

from tcpTester.types import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    UserException,
)
from tcpTester.types import UserCallResult, UserCallResultType

MAX_READ_SIZE = 4096  # in bytes
TIMEOUT = 20


class SUT:
    """
    Implementation of the System Under Test (SUT)
    """

    def __init__(self):
        """
        Initializes class variables.
        """
        super().__init__()

        self.logger.info("SUT started")

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

    def reset(self):
        """
        Resets the sockets used to connect to and communicate with another TCP endpoint.

        :raise socket_exception: If the socket raised an exception and the clien_socket did not.

        :return: None
        """
        # client_exception = None
        # socket_exception = None

        # try:
        #     if self.client_socket:
        #         self.client_socket.close()
        # except Exception as exception:
        #     client_exception = exception

        # try:
        #     if self.socket:
        #         self.socket.close()
        # except Exception as other_exception:
        #     socket_exception = other_exception

        self.socket = None
        self.client_socket = None

        # if socket_exception and not client_exception:
        #     raise socket_exception

    def handle_connect_command(self, parameters: ConnectParameters):
        """
        Handles a TestCommand of type CONNECT.
        Establishes a new connection with another TCP endpoint.

        :param parameters: The parameters for the CONNECT command.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("Attempting to connect to %s", parameters.cPort)

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.bind(("", random.randint(5000, 50000)))
            self.logger.info("bind successful")
            self.socket.connect((parameters.destination, parameters.dst_port))

        except Exception as e:
            return UserCallResult(status=UserCallResultType.FAILURE)

        self.logger.info("connection successful")

        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_listen_command(self, parameters: ListenParameters):
        """
        Handles a TestCommand of type LISTEN.
        Passively listens for an incoming connection request from another TCP endpoint.

        :param parameters: The parameters for the LISTEN command.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("starting socket on %s", parameters.lport)
        try:

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.bind(("", parameters.lport))
            self.socket.listen(1)

            self.logger.info("bind and listen successful")

            (self.client_socket, _) = self.socket.accept()

            self.logger.info("received client connect")

        except Exception as e:
            return UserCallResult(status=UserCallResultType.FAILURE)
        
        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_send_command(self, parameters: SendParameters):
        """
        Handles a TestCommand of type SEND.
        Sends a given payload to the TCP endpoint with which the SUT is connected.

        :param parameters: The parameters for the SEND command.

        :raise UserException: If the client_socket is not yet initialized.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("sending packet to client")
        if not self.client_socket:
            return UserCallResult(status=UserCallResultType.FAILURE)

        num_bytes = self.client_socket.send(parameters.sPayload)
        self.logger.info("sending completed")

        return UserCallResult(status=UserCallResultType.SUCCESS)

    def handle_receive_command(self):
        """
        Handles a TestCommand of type RECEIVE.
        Receives a single packet from the TCP endpoint with which the SUT is connected.

        :param parameters: The parameters for the RECEIVE command.

        :raise UserException: If the client_socket is not yet initialized.
        :raise UserException: If the parameters specify an expected payload and it is different from the payload of the incoming packet.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("receiving packet from client")
        if not self.client_socket:
            raise UserException("Not initialized yet")

        payload = self.client_socket.recv(MAX_READ_SIZE)

        # TODO: If payload is empty or nothing can be received a FAILURE should be thrown.

        self.logger.info("receive completed")
        return UserCallResult(status=UserCallResultType.RECEIVE, payload=payload)

    def handle_close_command(self):
        """
        Handles a TestCommand of type DISCONNECT.
        Disconnects the connection between the SUT and the other TCP endpoint.
        Half closes the connection in case the TestCommand parameters call for it.

        :param parameters: The parameters for the DISCONNECT command.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("disconnecting from client")
        self.reset()
        self.logger.info("disconnect completed")

        return UserCallResult(status=UserCallResultType.SUCCESS)
