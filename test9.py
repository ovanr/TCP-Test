from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    SendReceiveParameters,
    TestCommand,
)

DESCRIPTION = "Initiating Connection Termination"

IP_SUT = "192.168.92.112"
PORT_TS = 6010
PORT_SUT = 5010

serverQueue = [
    TestCommand(
        0,
        CommandType['CONNECT'],
        ConnectParameters(
            destination=IP_SUT,
            srcPort=PORT_TS,
            dstPort=PORT_SUT
        )
    ),
    TestCommand(0, CommandType['RECEIVE'], ReceiveParameters(flags="FA", timeout=34444)),
    TestCommand(0, CommandType['SEND'], SendParameters(flags="A")),
    TestCommand(0, CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(payload=b"deadbeef", flags="A"),
            ReceiveParameters(flags="A", timeout=34600)
        )
    ),
]

sutQueue = [
    TestCommand(
        0,
        CommandType['LISTEN'],
        ListenParameters(
            interface=IP_SUT,
            srcPort=PORT_SUT
        )
    ),
    TestCommand(0, CommandType['DISCONNECT'])
]
