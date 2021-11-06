import logging
import socket

from tcpTester.baseRunner import BaseRunner
from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    SendReceiveParameters,
    SendParameters,
    UserException,
)

MAX_READ_SIZE = 4096  # in bytes


class SUT(BaseRunner):

    def __init__(self):
        super().__init__()

        self.logger.info("sut started")

        self.client_socket = None
        self.socket = None

    @property
    def logger(self):
        return logging.getLogger("SUT")

    def reset(self):
        if not hasattr(self, "clientSocket"):
            return

        some_exception = None

        try:
            if self.client_socket:
                self.client_socket.close()
        except Exception as exception:
            some_exception = exception
            try:
                if self.socket:
                    self.socket.close()
            except Exception as other_exception:
                some_exception = other_exception
        finally:
            self.socket = None
            self.client_socket = None

            if some_exception:
                raise some_exception

    def handle_connect_command(self, parameters: ConnectParameters):
        self.logger.info("Attempting to connect to %s", parameters.dst_port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", parameters.src_port))
        self.logger.info("bind successful")

        self.socket.connect((parameters.destination, parameters.dst_port))
        self.logger.info("connection successful")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"]
        ))

    def handle_listen_command(self, parameters: ListenParameters):
        self.logger.info("starting socket on %s", parameters.src_port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        raise UserException("Unimplemented")

    def handle_disconnect_command(self):
        self.logger.info("disconnecting from client")
        self.reset()
        self.logger.info("disconnect completed")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"]
        ))

    def handle_abort_command(self):
        self.logger.info("aborting from client")
        return self.handle_disconnect_command()
