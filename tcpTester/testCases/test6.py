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

PORT_TS = 6005
PORT_SUT = 5005

class TestSix(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Close before reaching ESTABLISHED State"

    @property
    def test_id(self) -> int:
        return 6

    def prepare_queues_setup_test(self):
        pass

    def prepare_queues_test(self):
        self.queue_test_ts = [
            # SYNC(id=1, wait_response=False)
            # WAIT(sec=2)
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(
                    destination=SUT_IP,
                    src_port=PORT_TS,
                    dst_port=PORT_SUT,
                    full_handshake=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['RECEIVE'],
                ReceiveParameters(flags="SA")
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(flags="FA"),
                    ReceiveParameters(flags="A")
                )
            )
        ]
        self.queue_test_sut = [
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
