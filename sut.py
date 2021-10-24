import logging
import socket

from baseRunner import BaseRunner
from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    SendReceiveParameters,
    SendParameters,
    UserException,
)

MAX_READ_SIZE = 4096 # in bytes

class SUT(BaseRunner):
    def __init__(self):
        super().__init__()

        logging.getLogger("").setLevel(logging.INFO)
        logging.info("sut started")

        self.clientSocket = None
        self.socket = None

    def reset(self):
        if not hasattr(self, "clientSocket"):
            return

        someException = None

        try:
            if self.clientSocket:
                self.clientSocket.close()
        except Exception as exception:
            someException = exception
            try:
                if self.socket:
                    self.socket.close()
            except Exception as otherException:
                someException = otherException
        finally:
            self.socket = None
            self.clientSocket = None

            if someException:
                raise someException

    def handleConnectCommand(self, parameters: ConnectParameters):
        logging.info("Attempting to connect to %s", parameters.dstPort)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", parameters.srcPort))
        logging.info("bind successful")

        self.socket.connect((parameters.destination, parameters.dstPort))
        logging.info("connection successful")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"]
        ))

    def handleListenCommand(self, parameters: ListenParameters):
        logging.info("starting socket on %s", parameters.srcPort)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", parameters.srcPort))
        self.socket.listen(1)

        logging.info("bind and listen successful")

        (self.clientSocket, _) = self.socket.accept()

        logging.info("received client connect")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["LISTEN"]
        ))

    def handleSendCommand(self, parameters: SendParameters):
        logging.info("sending packet to client")
        if not self.clientSocket:
            raise UserException("Not initialized yet")

        numBytes = self.clientSocket.send(parameters.payload or b"")
        logging.warning("sending completed")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
            description=f"Send {numBytes} bytes"
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        logging.info("receiving packet from client")
        if not self.clientSocket:
            raise UserException("Not initialized yet")

        self.clientSocket.settimeout(parameters.timeout)
        payload = self.clientSocket.recv(MAX_READ_SIZE)

        # cannot check TCP flags
        # so only check for the data sent
        if (parameters.payload and parameters.payload != payload):
            logging.warning("incorrect bytes received")
            raise UserException(f"Invalid data received: '{payload}'")

        logging.info("receive completed")
        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Received this payload: '{payload}'"
        ))

    def handleSendReceiveCommand(self, parameters: SendReceiveParameters):
        raise UserException("Unimplemented")

    def handleDisconnectCommand(self):
        logging.info("disconnecting from client")
        self.reset()
        logging.info("disconnect completed")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"]
        ))

    def handleAbortCommand(self):
        logging.info("aborting from client")
        return self.handleDisconnectCommand()
