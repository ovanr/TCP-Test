from copy import deepcopy
from enum import Enum
from typing import Optional, Union

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


class SendParameters(WithShow):
    def __init__(self,
                 bytes: Optional[bytes] = None,
                 sequenceNumber: Optional[int] = None,
                 acknowledgementNumber: Optional[int] = None,
                 flags: Optional[str] = None,
                 windowSize: Optional[int] = None,
                 checksum: Optional[int] = None,
                 urgentPointer: Optional[int] = None):
        self.bytes = bytes
        self.sequenceNumber = sequenceNumber
        self.acknowledgementNumber = acknowledgementNumber
        self.flags = flags
        self.windowSize = windowSize
        self.checksum = checksum
        self.urgentPointer = urgentPointer

class ReceiveParameters(WithShow):
    def __init__(self,
                 timeout: int,
                 bytes: Optional[bytes] = None,
                 flags: Optional[str] = None):
        self.timeout = timeout
        self.bytes = bytes
        self.flags = flags

class SendReceiveParameters(WithShow):
    def __init__(self,
                 sendParameters: SendParameters,
                 receiveParameters: ReceiveParameters):
        self.sendParameters = sendParameters
        self.receiveParameters = receiveParameters

class ConnectParameters(WithShow):
    def __init__(self,
                 destination: str,
                 dstPort: int,
                 srcPort: int,
                 fullHandshake: bool = True):
        self.destination = destination
        self.dstPort = dstPort
        self.srcPort = srcPort
        self.fullHandshake = fullHandshake

class ListenParameters(WithShow):
    def __init__(self, interface: str, srcPort: int):
        self.interface = interface
        self.srcPort = srcPort

class ResultParameters(WithShow):
    def __init__(self,
                 status: int,
                 operation: CommandType,
                 description: Optional[str] = None,
                 errorMessage: Optional[str] = None):
        self.status = status
        self.operation = operation
        self.errorMessage = errorMessage
        self.description = description

Parameters = Union[SendParameters,
                   ReceiveParameters,
                   SendReceiveParameters,
                   ConnectParameters,
                   ListenParameters,
                   ResultParameters,
                   None]

class TestCommand(WithShow):
    def __init__(self,
                 testNumber: int,
                 commandType: CommandType,
                 commandParameters: Parameters = None,
                 timestamp: Optional[int] = None):
        self.testNumber = testNumber
        self.commandType = commandType
        self.commandParameters = commandParameters
        self.timestamp = timestamp
