from copy import deepcopy
from enum import Enum
from typing import Optional, Union
from dataclasses import dataclass

DEFAULT_TIMEOUT = 20  # in seconds


class UserException(Exception):
    pass


class CommandType(Enum):
    LISTEN = 0
    CONNECT = 1
    SEND = 2
    RECEIVE = 3
    CLOSE = 4


class WithShow:
    def __str__(self):
        state = deepcopy(self.__dict__)
        for k, v in state.items():
            if hasattr(v, '__str__'):
                state[k] = v.__str__()
        return str(state)

    def __repr__(self):
        return self.__str__()


@dataclass
class SendParameters(WithShow):
    sPayload: bytes


@dataclass
class ListenParameters(WithShow):
    lport: int

@dataclass
class ConnectParameters(WithShow):
    cPort: int

Parameters = Union[SendParameters,
                   ConnectParameters,
                   ListenParameters,
                   None]


@dataclass(init=False)
class Command(WithShow):
    command_type: CommandType
    command_parameters: Parameters = None

    def __init__(self, command_type: CommandType, command_parameters: Parameters = None):
        self.command_type = command_type
        self.command_parameters = command_parameters
