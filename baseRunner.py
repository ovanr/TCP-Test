from abc import ABC, abstractmethod
import logging
from typing import cast

from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    SendParameters,
    SendReceiveParameters,
    UserException,
    TestCommand
)

class BaseRunner(ABC):
    def __init__(self):
        self.testNumber = -1

    def executeCommand(self, cmd: TestCommand):
        if cmd.testNumber != self.testNumber:
            self.testNumber = cmd.testNumber
            try:
                self.reset()
            except Exception:
                pass

        result = None
        try:
            if cmd.commandType == CommandType["LISTEN"]:
                result = self.handleListenCommand(
                    cast(ListenParameters, cmd.commandParameters)
                )
            elif cmd.commandType == CommandType["CONNECT"]:
                result = self.handleConnectCommand(
                    cast(ConnectParameters, cmd.commandParameters)
                )
            elif cmd.commandType == CommandType["SEND"]:
                result = self.handleSendCommand(
                    cast(SendParameters, cmd.commandParameters)
                )
            elif cmd.commandType == CommandType["RECEIVE"]:
                result = self.handleReceiveCommand(
                    cast(ReceiveParameters, cmd.commandParameters)
                )
            elif cmd.commandType == CommandType["SENDRECEIVE"]:
                result = self.handleSendReceiveCommand(
                    cast(SendReceiveParameters, cmd.commandParameters)
                )
            elif cmd.commandType == CommandType["DISCONNECT"]:
                result = self.handleDisconnectCommand()
            elif cmd.commandType == CommandType["ABORT"]:
                result = self.handleAbortCommand()
        except UserException as exception:
            logging.warning("Command ended with error.")
            result = self.makeResult(ResultParameters(
                status=1,
                operation=cmd.commandType,
                errorMessage=str(exception)
            ))
        except Exception as exception:
            logging.warning("Command ended with error.")
            result = self.makeResult(ResultParameters(
                status=2,
                operation=cmd.commandType,
                errorMessage=str(exception)
            ))

        return result


    def makeResult(self, params: ResultParameters):
        return TestCommand(
            testNumber=self.testNumber,
            commandType=CommandType["RESULT"],
            commandParameters=params
        )

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def handleListenCommand(self, parameters: ListenParameters):
        pass

    @abstractmethod
    def handleConnectCommand(self, parameters: ConnectParameters):
        pass

    @abstractmethod
    def handleSendReceiveCommand(self, parameters: SendReceiveParameters):
        pass

    @abstractmethod
    def handleReceiveCommand(self, parameters: ReceiveParameters):
        pass

    @abstractmethod
    def handleSendCommand(self, parameters: SendParameters):
        pass

    @abstractmethod
    def handleDisconnectCommand(self):
        pass

    @abstractmethod
    def handleAbortCommand(self):
        pass
