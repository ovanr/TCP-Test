from __future__ import annotations
from typing import Optional, Union, List
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy

DEFAULT_TIMEOUT = 20  # in seconds

class WithShow:
    def __str__(self):
        state = deepcopy(self.__dict__)
        for k, v in state.items():
            if hasattr(v, '__str__'):
                state[k] = v.__str__()
        return str(state)

    def __repr__(self):
        return self.__str__()

class ParseException(Exception):
    pass

class UserException(Exception):
    pass

class CommandType(Enum):
    LISTEN = 0
    CONNECT = 1
    SEND = 2
    RECEIVE = 3
    CLOSE = 4

class UserCallResultType(Enum):
    SUCCESS = 0
    FAILURE = 1
    RECEIVE = 2

    @staticmethod
    def from_torxakis(structure: str):
        return UserCallResultType[structure.strip()]

    def to_torxakis(self):
        return self.name


class SEQ(Enum):
    SEQ_VALID = "SEQ_VALID"
    SEQ_INVALID = "SEQ_INVALID"

    @staticmethod
    def from_torxakis(structure: str):
        return SEQ[structure.strip()]

    def to_torxakis(self):
        return self.name

class ACK(Enum):
    ACK_VALID = "ACK_VALID"
    ACK_INVALID = "ACK_INVALID"

    @staticmethod
    def from_torxakis(structure: str):
        return ACK[structure.strip()]

    def to_torxakis(self):
        return self.name

class TCPFlag(Enum):
    ACK = "A"
    FIN = "F"
    RST = "R"
    SYN = "S"

    @staticmethod
    def from_torxakis(structure: str):
        return TCPFlag[structure.strip()]

    def to_torxakis(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

@dataclass
class UserCallResult(WithShow):
    status: UserCallResultType
    payload: Optional[bytes] = None

    def to_torxakis(self):
        status = self.status.to_torxakis()
        payload = '""' if not self.payload else '"' + self.payload.decode() + '"'

        if self.status in [UserCallResultType.SUCCESS, UserCallResultType.FAILURE]:
            return status

        return f"{status}({payload})"

@dataclass
class SendParameters(WithShow):
    payload: bytes

@dataclass
class ListenParameters(WithShow):
    src_port: int

@dataclass
class ConnectParameters(WithShow):
    src_port: int
    dst_port: int

Parameters = Union[ListenParameters,
                   ConnectParameters,
                   SendParameters,
                   None]

@dataclass
class UserCall(WithShow):
    command_type: CommandType
    command_parameters: Parameters = None

    @staticmethod
    def from_torxakis(structure: str):
        structure = structure.strip()
        if structure.startswith("LISTEN"):
            port = int(structure[7:-1])
            return UserCall(CommandType["LISTEN"], ListenParameters(port))

        if structure.startswith("CONNECT"):
            dst_port = int(structure[8:-1])
            return UserCall(CommandType["CONNECT"], ConnectParameters(dst_port))

        if structure.startswith("SEND"):
            payload = bytes(structure[5:-1].replace('"', '').encode())
            return UserCall(CommandType["SEND"], SendParameters(payload))

        if structure.startswith("RECEIVE"):
            return UserCall(CommandType["RECEIVE"])

        if structure.startswith("CLOSE"):
            return UserCall(CommandType["CLOSE"])

        raise ParseException(f"UserCall has format: {structure}")

@dataclass
class TCPPacket(WithShow):
    sport: int
    dport: int
    seq: SEQ
    ack: ACK
    flags: List[TCPFlag]
    payload: bytes

    @staticmethod
    def _to_tcp_flag_list(flags: List[TCPFlag]) -> str:
        if not flags:
            return "NIL"

        x = flags[0].to_torxakis()
        xs = TCPPacket._to_tcp_flag_list(flags[1:])
        return f"CONS({x}, {xs})"

    @staticmethod
    def _from_tcp_flag_list(structure: str) -> List[TCPFlag]:
        structure = structure.strip()

        if structure == "NIL":
            return []

        header = structure[0:4]
        if header != "CONS":
            raise ParseException(f"TCPFlagList has format: {structure}")

        structure = structure[5:-1]
        x = TCPFlag.from_torxakis(structure[0:structure.find(',')])
        xs = TCPPacket._from_tcp_flag_list(structure[structure.find(',')+1:])

        xs.insert(0,x)
        return xs

    @staticmethod
    def from_torxakis(structure: str) -> TCPPacket:
        structure = structure.strip()

        header = structure[0:9]
        if header != "TCPPacket":
            raise ParseException(f"TCPPacket has format: {structure}")

        tokens = filter(lambda t: t, structure[10:-1].split(','))
        sport = int(next(tokens))
        dport = int(next(tokens))
        seq = SEQ.from_torxakis(next(tokens))
        ack = ACK.from_torxakis(next(tokens))

        rest = ','.join(tokens).strip()
        if rest.startswith("NIL"):
            tokens = filter(lambda t: t, rest.split(','))
            flags = TCPPacket._from_tcp_flag_list(next(tokens))
            payload = bytes(next(tokens).replace('"', '').strip().encode())
        else:
            bracket_index = rest.rindex(')', 0, len(rest) -1)
            raw_flags = rest[0: bracket_index +1]
            flags = TCPPacket._from_tcp_flag_list(raw_flags)
            raw_payload = rest[bracket_index + 2:]
            payload = bytes(raw_payload.replace('"', '').strip().encode())

        return TCPPacket(sport, dport, seq, ack, flags, payload)

    def to_torxakis(self):
        self.flags.sort()

        seq = self.seq.to_torxakis()
        ack = self.ack.to_torxakis()
        flags = TCPPacket._to_tcp_flag_list(self.flags)
        payload = '"' + self.payload.decode() + '"'
        return f"TCPPacket({self.sport}, {self.dport}, {seq}, {ack}, {flags}, {payload})"
