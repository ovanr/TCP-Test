from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    TestCommand,
)
from tcpTester.config import SUT_IP
from tcpTester.baseTestCase import BaseTestCase

PORT_TS = 6004
PORT_SUT = 5004

class TestFive(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Connection Establishment with active Host"

    @property
    def test_id(self) -> int:
        return 5

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
                    dst_port=PORT_SUT
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
