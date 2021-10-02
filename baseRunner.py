
from abc import ABC
from testCommand import *
from typing import cast

class BaseRunner(ABC):
    def executeCommand(self, cmd: TestCommand):
        if (cmd.testNumber != self.testNumber):
            self.testNumber = cmd.testNumber
            try:
                self.reset()
            except Exception:
                pass

        try:
            if cmd.commandType == CommandType["CONNECT"]:
                return self.handleConnectCommand(cast(ConnectParameters, cmd.commandParameters))
            elif cmd.commandType == CommandType["RECEIVE"]:
                return self.handleReceiveCommand(cast(ReceiveParameters, cmd.commandParameters))
            elif cmd.commandType == CommandType["SEND"]:
                return self.handleSendCommand(cast(SendParameters, cmd.commandParameters))
            elif cmd.commandType == CommandType["DISCONNECT"]:
                return self.handleDisconnectCommand()
            elif cmd.commandType == CommandType["ABORT"]:
                return self.handleAbortCommand()
        except UserException as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=cmd.commandType,
                errorMessage=str(e)
            ))
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=2,
                operation=cmd.commandType,
                errorMessage=str(e)
            ))


    def makeResult(self, params: ResultParameters):
        return TestCommand(
            testNumber=self.testNumber, 
            commandType=CommandType["RESULT"],
            commandParameters=params
        )

    def reset(self):
        pass

    def handleConnectCommand(self, parameters: ConnectParameters):
        pass

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        pass

    def handleSendCommand(self, parameters: SendParameters):
        pass

    def handleDisconnectCommand(self):
        pass

    def handleAbortCommand(self):
        pass
