from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    TestCommand, Command, SyncParameters, WaitParameters
)
from tcpTester.baseTestCase import BaseTestCase
from random import randint

PORT_TS = randint(5000, 50000)
PORT_SUT = randint(5000, 50000)


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
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            Command(
                CommandType['WAIT'],
                WaitParameters(
                    seconds=5
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
        self.queue_test_sut = [
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
