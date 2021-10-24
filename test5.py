from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    TestCommand,
)

DESCRIPTION = "Connection Establishment with active Host"

IP_SUT = "192.168.92.112"
PORT_TS = 6006
PORT_SUT = 5006

serverQueue = [
    TestCommand(
        0,
        CommandType['CONNECT'],
        ConnectParameters(
            destination=IP_SUT,
            srcPort=PORT_TS,
            dstPort=PORT_SUT
        )
    )
]

sutQueue = [
    TestCommand(
        0,
        CommandType['LISTEN'],
        ListenParameters(
            interface=IP_SUT,
            srcPort=PORT_SUT
        )
    )
]
