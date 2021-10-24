from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    SendReceiveParameters,
    TestCommand,
)

DESCRIPTION = "Receiving data"

IP_SUT = "192.168.92.112"
PORT_TS = 6011
PORT_SUT = 5011

PAYLOAD = b"x" * 100
EXPECTED_PAYLOAD = b"x" * 300

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
    TestCommand(0, CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(payload=PAYLOAD, flags="A"),
            ReceiveParameters(flags="A", timeout=34600)
        )
    ),
    TestCommand(0, CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(payload=PAYLOAD, flags="A"),
            ReceiveParameters(flags="A", timeout=34600)
        )
    ),
    TestCommand(0, CommandType['SENDRECEIVE'],
        SendReceiveParameters(
            SendParameters(payload=PAYLOAD, flags="A"),
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
    ),
    TestCommand(
        0,
        CommandType['RECEIVE'],
        ReceiveParameters(timeout=34444, payload=EXPECTED_PAYLOAD)
    )
]
