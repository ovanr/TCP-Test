from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    ReceiveParameters,
    SendReceiveParameters,
    TestCommand,
)
from tcpTester.config import SUT_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6009
PORT_SUT = 5009
PAYLOAD = b"x" * 100
EXPECTED_PAYLOAD = b"x" * 300

class TestTen(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Receiving data segments"

    @property
    def test_id(self) -> int:
        return 10

    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            # SYNC(id=1, wait_response=False)
            # WAIT(sec=2)
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(
                    destination=SUT_IP,
                    src_port=PORT_TS,
                    dst_port=PORT_SUT
                )
            )
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(
                    interface=SUT_IP,
                    src_port=PORT_SUT
                )
            )
            # SYNC(id=1, wait_response=False)
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(payload=PAYLOAD, flags="A"),
                    ReceiveParameters(flags="A")
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(payload=PAYLOAD, flags="A"),
                    ReceiveParameters(flags="A")
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(payload=PAYLOAD, flags="A"),
                    ReceiveParameters(flags="A")
                )
            )
            # SYNC(id=1, wait_response=True)
        ]
        self.queue_test_sut = [
            # SYNC(id=1, wait_response=False)
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(payload=EXPECTED_PAYLOAD)
            )
        ]
