from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendParameters,
    SendReceiveParameters,
    ReceiveParameters,
    TestCommand, Command, SyncParameters, WaitParameters
)
from tcpTester.baseTestCase import BaseTestCase
from random import randint

PORT_TS = randint(5000, 50000)
PORT_SUT = randint(5000, 50000)


class TestFour(BaseTestCase):

    def __init__(self, ts_ip, sut_ip):
        super().__init__(ts_ip, sut_ip)

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
                ListenParameters(
                    interface=self.ts_ip,
                    src_port=PORT_TS,
                    update_ts_ack=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(
                        flags="S",
                        acknowledgement_number=0,
                        update_ts_seq=False),
                    ReceiveParameters(flags="SA")
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(
                        flags="SA"),
                    ReceiveParameters(flags="A")
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(flags="A")
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
            Command(
                CommandType['WAIT'],
                WaitParameters(
                    seconds=2
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(destination=self.ts_ip, src_port=PORT_SUT, dst_port=PORT_TS)
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            )
        ]
