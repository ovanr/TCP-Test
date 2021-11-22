from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    DisconnectParameters,
    ReceiveParameters,
    SendReceiveParameters,
    TestCommand, Command, SyncParameters,
)
from tcpTester.baseTestCase import BaseTestCase
from random import randint

PORT_TS = randint(5000, 50000)
PORT_SUT = randint(5000, 50000)


class TestNine(BaseTestCase):
    def __init__(self, ts_ip, sut_ip):
        super().__init__(ts_ip, sut_ip)

    @property
    def test_name(self) -> str:
        return "Send data at a half-closed connection"

    @property
    def test_id(self) -> int:
        return 9

    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(
                    destination=self.sut_ip,
                    src_port=PORT_TS,
                    dst_port=PORT_SUT
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(flags="FA")
            ),
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(flags="A")
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=3,
                    wait_for_result=False
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=4,
                    wait_for_result=True
                )
            ),
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(
                    interface=self.sut_ip,
                    src_port=PORT_SUT
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=3,
                    wait_for_result=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['DISCONNECT'],
                DisconnectParameters(half_close=True)
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=4,
                    wait_for_result=True
                )
            )
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(payload=b"deadbeef", flags="A"),
                    ReceiveParameters(flags="A")
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=True
                )
            ),
        ]
        self.queue_test_sut = [
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            )
        ]
