from abc import ABC, abstractmethod
import logging
from typing import cast

from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    DisconnectParameters,
    SendParameters,
    SendReceiveParameters,
    UserException,
    TestCommand
)


class BaseRunner(ABC):
    _test_number: int = -1

    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        pass

    def __init__(self):
        self._test_number: int = -1

    def execute_command(self, cmd: TestCommand):
        if cmd.test_number == -2:
            pass
        elif cmd.test_number != self._test_number:
            self._test_number = cmd.test_number


        result = None
        try:
            if cmd.command_type == CommandType["LISTEN"]:
                result = self.handle_listen_command(
                    cast(ListenParameters, cmd.command_parameters)
                )
            elif cmd.command_type == CommandType["CONNECT"]:
                result = self.handle_connect_command(cast(ConnectParameters, cmd.command_parameters))
            elif cmd.command_type == CommandType["SEND"]:
                result = self.handle_send_command(cast(SendParameters, cmd.command_parameters))
            elif cmd.command_type == CommandType["RECEIVE"]:
                result = self.handle_receive_command(cast(ReceiveParameters, cmd.command_parameters))
            elif cmd.command_type == CommandType["SENDRECEIVE"]:
                result = self.handle_send_receive_command(cast(SendReceiveParameters, cmd.command_parameters))
            elif cmd.command_type == CommandType["DISCONNECT"]:
                result = self.handle_disconnect_command(cast(DisconnectParameters, cmd.command_parameters))
            elif cmd.command_type == CommandType["ABORT"]:
                result = self.handle_abort_command()
        except UserException as exception:
            self.logger.warning("Command ended with error: %s", exception)
            result = self.make_result(ResultParameters(
                status=1,
                operation=cmd.command_type,
                error_message=str(exception)
            ))
        except Exception as exception:
            self.logger.warning("Command ended with error: %s", exception)
            result = self.make_result(ResultParameters(
                status=2,
                operation=cmd.command_type,
                error_message=str(exception)
            ))

        return result

    def make_result(self, params: ResultParameters):
        return TestCommand(
            test_number=self._test_number,
            command_type=CommandType["RESULT"],
            command_parameters=params
        )

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def handle_listen_command(self, parameters: ListenParameters):
        pass

    @abstractmethod
    def handle_connect_command(self, parameters: ConnectParameters):
        pass

    @abstractmethod
    def handle_send_receive_command(self, parameters: SendReceiveParameters):
        pass

    @abstractmethod
    def handle_receive_command(self, parameters: ReceiveParameters):
        pass

    @abstractmethod
    def handle_send_command(self, parameters: SendParameters):
        pass

    @abstractmethod
    def handle_disconnect_command(self, parameters: DisconnectParameters):
        pass

    @abstractmethod
    def handle_abort_command(self):
        pass
