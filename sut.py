from testCommand import *
from baseRunner import BaseRunner
import socket
import logging

MAX_READ_SIZE = 4096 # in bytes

class SUT(BaseRunner):
    def __init__(self):
        self.testNumber = -1

        logging.getLogger("").setLevel(logging.INFO)
        logging.info("sut started")

    def reset(self):
        if not hasattr(self, "clientSocket"):
            return

        someException = None

        try:
            self.clientSocket.close()
        except Exception as e1:
            someException = e1
            try:
                self.socket.close()
            except Exception as e2:
                someException = e2
        finally:
            self.socket = None
            self.clientSocket = None

            if someException:
                raise someException

    def handleConnectCommand(self, parameters: ConnectParameters):
        logging.info(f"starting socket on {parameters.srcPort}")
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((parameters.destination, parameters.srcPort))
        self.socket.listen(1)

        logging.info("bind and listen successful")

        (self.clientSocket, _) = self.socket.accept()

        logging.info("received client connect")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"]
        ))

    def handleSendCommand(self, parameters: SendParameters):
        logging.info("sending packet to client")
        self.clientSocket.send(parameters.bytes)
        logging.warn("sending completed")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        logging.info("receiving packet from client")

        self.clientSocket.settimeout(parameters.timeout)
        payload = self.clientSocket.recv(MAX_READ_SIZE)

        # cannot check TCP flags
        # so only check for the data sent
        if (parameters.bytes and parameters.bytes != payload):
            logging.warn("incorrect bytes received")
            raise UserException(f"Invalid data received: '{payload}'")

        logging.info("receive completed")
        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"]
        ))


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
