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

PORT_TS = 6013
PORT_SUT = 5013
PAYLOAD = b"x" * 100

class TestFourteen(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Lost packet detection"

    @property
    def test_id(self) -> int:
        return 14

    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            # SYNC(id=1, wait_response=False)
            # WAIT(sec=2)
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
            # SYNC(id=1, wait_response=False)
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(
                    payload=PAYLOAD,
                    flags="A"
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
            )
            # SYNC(id=1, wait_response=False)
        ]
        self.queue_test_sut = [
            # SYNC(id=1, wait_response=False)
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(payload=PAYLOAD)
            )
        ]
