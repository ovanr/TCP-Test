import logging
import socket

from tcpTester.baseRunner import BaseRunner
from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    DisconnectParameters,
    SendReceiveParameters,
    SendParameters,
    UserException,
)

MAX_READ_SIZE = 4096  # in bytes
TIMEOUT = 20


class SUT(BaseRunner):
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
        self.logger.info("Attempting to connect to %s", parameters.dst_port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.socket.bind(("", parameters.src_port))
        self.logger.info("bind successful")

        self.socket.connect((parameters.destination, parameters.dst_port))
        self.logger.info("connection successful")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"]
        ))

    def handle_listen_command(self, parameters: ListenParameters):
        """
        Handles a TestCommand of type LISTEN.
        Passively listens for an incoming connection request from another TCP endpoint.

        :param parameters: The parameters for the LISTEN command.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("starting socket on %s", parameters.src_port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.socket.bind(("", parameters.src_port))
        self.socket.listen(1)

        self.logger.info("bind and listen successful")

        (self.client_socket, _) = self.socket.accept()

        self.logger.info("received client connect")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["LISTEN"]
        ))

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
            raise UserException("Not initialized yet")

        num_bytes = self.client_socket.send(parameters.payload or b"")
        self.logger.warning("sending completed")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
            description=f"Send {num_bytes} bytes"
        ))

    def handle_receive_command(self, parameters: ReceiveParameters):
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

        self.client_socket.settimeout(parameters.timeout)
        payload = self.client_socket.recv(MAX_READ_SIZE)

        # cannot check TCP flags
        # so only check for the data sent
        if parameters.payload and parameters.payload != payload:
            self.logger.warning("incorrect bytes received")
            raise UserException(f"Invalid data received: '{payload}'")

        self.logger.info("receive completed")
        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Received this payload: '{payload}'"
        ))

    def handle_send_receive_command(self, parameters: SendReceiveParameters):
        """
        Handles a TestCommand of type SENDRECEIVE.
        This command is not implemented for the SUT.

        :param parameters: The parameters for the SEND command.

        :raise UserException: Always.

        :return: None
        """
        raise UserException("Unimplemented")

    def handle_disconnect_command(self, parameters: DisconnectParameters):
        """
        Handles a TestCommand of type DISCONNECT.
        Disconnects the connection between the SUT and the other TCP endpoint.
        Half closes the connection in case the TestCommand parameters call for it.

        :param parameters: The parameters for the DISCONNECT command.

        :return: A TestCommand of type RESULT.
        """
        if parameters.half_close and self.client_socket:
            self.logger.info("half-closing connection")

            self.client_socket.shutdown(socket.SHUT_WR)

            return self.make_result(ResultParameters(
                status=0,
                operation=CommandType["DISCONNECT"]
            ))


        self.logger.info("disconnecting from client")
        self.reset()
        self.logger.info("disconnect completed")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"]
        ))

    def handle_abort_command(self):
        """
        Aborts the current connection with the SUT's communication partner.

        :return: A TestCommand of type ABORT.
        """
        self.logger.info("aborting from client")
        self.reset()

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["ABORT"]
        ))
