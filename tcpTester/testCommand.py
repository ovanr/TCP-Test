from copy import deepcopy
from enum import Enum
from typing import Optional, Union
from dataclasses import dataclass


DEFAULT_TIMEOUT = 600 # 10 minutes

class UserException(Exception):
    pass


class CommandType(Enum):
    SEND = 0
    RECEIVE = 1
    SENDRECEIVE = 2
    CONNECT = 3
    LISTEN = 4
    DISCONNECT = 5
    ABORT = 6
    RESULT = 7


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
    payload: Optional[bytes] = None
    sequence_number: Optional[int] = None
    acknowledgement_number: Optional[int] = None
    flags: Optional[str] = None
    update_ts_seq: bool = True

@dataclass
class ReceiveParameters(WithShow):
    timeout: int = DEFAULT_TIMEOUT
    payload: Optional[bytes] = None
    flags: Optional[str] = None


@dataclass
class SendReceiveParameters(WithShow):
    send_parameters: SendParameters
    receive_parameters: ReceiveParameters


@dataclass
class ConnectParameters(WithShow):
    destination: str
    dst_port: int
    src_port: int
    full_handshake: bool = True


@dataclass
class ListenParameters(WithShow):
    interface: str
    src_port: int


@dataclass
class ResultParameters(WithShow):
    status: int
    operation: CommandType
    description: Optional[str] = None
    error_message: Optional[str] = None


Parameters = Union[SendParameters,
                   ReceiveParameters,
                   SendReceiveParameters,
                   ConnectParameters,
                   ListenParameters,
                   ResultParameters,
                   None]


@dataclass
class TestCommand(WithShow):
    test_number: int
    command_type: CommandType
    command_parameters: Parameters = None
    timestamp: Optional[int] = None
