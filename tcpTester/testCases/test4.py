from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    SendReceiveParameters,
    ReceiveParameters,
    TestCommand,
)
from tcpTester.config import TEST_SERVER_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6003
PORT_SUT = 5003

class TestFour(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Simultaneous connection establishment"

    @property
    def test_id(self) -> int:
        return 4

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
                    SendParameters(flags="S"),
                    ReceiveParameters(timeout=3600, flags="SA")
                )
            ),
            TestCommand(
                self.test_id,
                CommandType["SEND"],
                SendParameters(flags="A"))
        ]
        self.queue_test_sut = [
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(destination=TEST_SERVER_IP, src_port=PORT_SUT, dst_port=PORT_TS)
            )
        ]
