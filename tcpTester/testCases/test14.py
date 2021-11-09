from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand, Command, SyncParameters,
)
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 5013
PORT_SUT = 6013
PAYLOAD = b"x" * 100


class TestFourteen(BaseTestCase):
    def __init__(self, ts_ip, sut_ip):
        super().__init__(ts_ip, sut_ip)

    @property
    def test_name(self) -> str:
        return "Lost packet detection"

    @property
    def test_id(self) -> int:
        return 14

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
            )
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
            )
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(
                    payload=PAYLOAD,
                    flags="A",
                    update_ts_ack=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(
                    timeout=10,
                    payload=PAYLOAD,
                    flags="A"
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(flags="A")
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
        ]
        self.queue_test_sut = [
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(payload=PAYLOAD)
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            ),
        ]
