from testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    TestCommand,
)

DESCRIPTION = "Connection establishment with passive host"

IP_TS = "192.168.92.38"
PORT_TS = 6000
PORT_SUT = 5000

serverQueue = [
    TestCommand(0, CommandType['LISTEN'], ListenParameters(interface=IP_TS, srcPort=PORT_TS)),
    TestCommand(0, CommandType['SEND'], SendParameters(flags="SA"))
]

sutQueue = [
    TestCommand(
        0,
        CommandType['CONNECT'],
        ConnectParameters(destination=IP_TS, srcPort=PORT_SUT, dstPort=PORT_TS)
    )
]
