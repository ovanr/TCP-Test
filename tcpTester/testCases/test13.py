from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendReceiveParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand,
)
from tcpTester.config import SUT_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6012
PORT_SUT = 5012
PAYLOAD = b"x" * 100

class TestThirteen(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Duplicate packet detection"

    @property
    def test_id(self) -> int:
        return 13

    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(destination=SUT_IP, src_port=PORT_TS, dst_port=PORT_SUT)
            )
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(interface=SUT_IP, src_port=PORT_SUT)
            )
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(
                    payload=PAYLOAD,
                    flags="A",
                    update_ts_seq=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(
                        payload=PAYLOAD,
                        flags="A"),
                    ReceiveParameters(flags="A")
                )
            )
        ]
