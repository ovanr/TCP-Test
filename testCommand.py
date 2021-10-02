from enum import Enum
from typing import Optional, Union
from copy import deepcopy

class CommandType(Enum):
    SEND = 0
    RECEIVE = 1
    CONNECT = 2
    DISCONNECT = 3
    ABORT = 4
    RESULT = 5

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
                 bytes: bytes,
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

class ConnectParameters(WithShow):
    def __init__(self,
                 destination: str,
                 dstPort: int,
                 srcPort: int):
        self.destination = destination
        self.dstPort = dstPort
        self.srcPort = srcPort

class ResultParameters(WithShow):
    def __init__(self,
                 status: int,
                 operation: CommandType,
                 errorMessage: Optional[str] = None):
        self.status = status
        self.operation = operation
        self.errorMessage = errorMessage

Parameters = Union[SendParameters, 
                   ReceiveParameters, 
                   ConnectParameters, 
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
