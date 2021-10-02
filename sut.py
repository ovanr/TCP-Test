from testCommand import *
from baseRunner import BaseRunner
import socket

MAX_READ_SIZE = 4096 # in bytes

class SUT(BaseRunner):
    def __init__(self):
        self.testNumber = -1

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
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((parameters.destination, parameters.srcPort))

            self.socket.listen(1)
            (self.clientSocket, _) = self.socket.accept()

            return self.makeResult(ResultParameters(
                status=0,
                operation=CommandType["CONNECT"]
            ))
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["CONNECT"],
                errorMessage=str(e)
            ))

    def handleSendCommand(self, parameters: SendParameters):
        try:
            self.clientSocket.send(parameters.bytes)
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["SEND"],
                errorMessage=str(e)
            ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        try:
            self.clientSocket.settimeout(parameters.timeout)
            payload = self.clientSocket.recv(MAX_READ_SIZE)
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["RECEIVE"],
                errorMessage=str(e)
            ))

        # cannot check TCP flags
        # so only check for the data sent
        if (parameters.bytes and parameters.bytes != payload):
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["RECEIVE"],
                errorMessage=f"Invalid data received: '{payload}'"
            ))

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"]
        ))


    def handleDisconnectCommand(self):
        try:
            self.reset()

            return self.makeResult(ResultParameters(
                status=0,
                operation=CommandType["DISCONNECT"]
            ))
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["DISCONNECT"],
                errorMessage=str(e)
            ))

    def handleAbortCommand(self):
        return self.handleDisconnectCommand()
