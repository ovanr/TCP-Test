from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand,
)
from tcpTester.config import SUT_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6010
PORT_SUT = 5010
PAYLOAD = b"x" * 100

class TestEleven(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Sending data segments"

    @property
    def test_id(self) -> int:
        return 11

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
        for _ in range(0,3):
            self.queue_test_ts.extend([
                TestCommand(
                    self.test_id,
                    CommandType['RECEIVE'],
                    ReceiveParameters(flags="A", payload=PAYLOAD)
                ),
                TestCommand(
                    self.test_id,
                    CommandType['SEND'],
                    SendParameters(flags="A")
                )
            ])
            self.queue_test_sut.append(
                TestCommand(
                    self.test_id,
                    CommandType['SEND'],
                    SendParameters(payload=PAYLOAD)
                )
            )
