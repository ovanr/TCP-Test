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

PORT_TS = 6008
PORT_SUT = 5008

class TestNine(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Send data at a half-closed connection"

    @property
    def test_id(self) -> int:
        return 9

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
            ),
            # SYNC(id=2, wait_response=True)
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
            # SYNC(id=3, wait_response=False)
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(
                    interface=SUT_IP,
                    src_port=PORT_SUT
                )
            ),
            # SYNC(id=1, wait_response=False)
            # SYNC(id=2, wait_response=True)
            # SYNC(id=3, wait_response=False)
            TestCommand(
                self.test_id,
                CommandType['DISCONNECT']
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
        ]
        self.queue_test_sut = []
