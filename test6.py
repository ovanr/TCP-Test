from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    SendReceiveParameters,
    TestCommand,
)

DESCRIPTION = "Close before reaching ESTABLISHED State"

IP_SUT = "192.168.92.112"
PORT_TS = 6007
PORT_SUT = 5007

serverQueue = [
    TestCommand(
        0,
        CommandType['CONNECT'],
        ConnectParameters(
            destination=IP_SUT,
            srcPort=PORT_TS,
            dstPort=PORT_SUT,
            fullHandshake=False
        )
    ),
    TestCommand(0, CommandType['RECEIVE'], ReceiveParameters(flags="SA", timeout=36000)),
    TestCommand(0, CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(flags="FA"),
            ReceiveParameters(flags="A", timeout=34600)
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
