from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    SendReceiveParameters,
    ReceiveParameters,
    TestCommand,
)

DESCRIPTION = "Simultaneous connection establishment"

IP_TS = "192.168.92.38"
PORT_TS = 6004
PORT_SUT = 5004

serverQueue = [
    TestCommand(0, CommandType['LISTEN'], ListenParameters(interface=IP_TS, srcPort=PORT_TS)),
    TestCommand(
        0,
        CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(flags="S"),
            ReceiveParameters(timeout=3600, flags="SA")
        )
    ),
    TestCommand(0, CommandType["SEND"], SendParameters(flags="A"))
]

sutQueue = [
    TestCommand(
        0,
        CommandType['CONNECT'],
        ConnectParameters(destination=IP_TS, srcPort=PORT_SUT, dstPort=PORT_TS)
    )
]
