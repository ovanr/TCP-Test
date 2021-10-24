from copy import deepcopy
from enum import Enum
from typing import Optional, Union
from dataclasses import dataclass

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
        for k,v in state.items():
            if hasattr(v, '__str__'):
                state[k] = v.__str__()
        return str(state)

    def __repr__(self):
        return self.__str__()


@dataclass
class SendParameters(WithShow):
    payload: Optional[bytes] = None
    sequenceNumber: Optional[int] = None
    acknowledgementNumber: Optional[int] = None
    flags: Optional[str] = None
    windowSize: Optional[int] = None
    checksum: Optional[int] = None
    urgentPointer: Optional[int] = None

@dataclass
class ReceiveParameters(WithShow):
    timeout: int
    payload: Optional[bytes] = None
    flags: Optional[str] = None

@dataclass
class SendReceiveParameters(WithShow):
    sendParameters: SendParameters
    receiveParameters: ReceiveParameters

@dataclass
class ConnectParameters(WithShow):
    destination: str
    dstPort: int
    srcPort: int
    fullHandshake: bool = True

@dataclass
class ListenParameters(WithShow):
    interface: str
    srcPort: int

@dataclass
class ResultParameters(WithShow):
    status: int
    operation: CommandType
    description: Optional[str] = None
    errorMessage: Optional[str] = None

Parameters = Union[SendParameters,
                   ReceiveParameters,
                   SendReceiveParameters,
                   ConnectParameters,
                   ListenParameters,
                   ResultParameters,
                   None]

@dataclass
class TestCommand(WithShow):
    testNumber: int
    commandType: CommandType
    commandParameters: Parameters = None
    timestamp: Optional[int] = None
