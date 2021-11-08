from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendReceiveParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand, Command, SyncParameters,
)
from tcpTester.config import TEST_SERVER_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6002
PORT_SUT = 5002

class TestThree(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Reply to first SYN with an invalid Ack"

    @property
    def test_id(self) -> int:
        return 3

    def prepare_queues_setup_test(self):
        pass

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(interface=TEST_SERVER_IP, src_port=PORT_TS)
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(acknowledgement_number=543, flags="A"),
                    ReceiveParameters(flags="R")
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
                CommandType['CONNECT'],
                ConnectParameters(destination=TEST_SERVER_IP, src_port=PORT_SUT, dst_port=PORT_TS)
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            )
        ]
