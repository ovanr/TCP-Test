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
                ReceiveParameters(flags="A", payload=PAYLOAD)
            ),
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(flags="A")
            )
            # SYNC(id=1, wait_response=False)
            # SYNC(id=2, wait_response=True)
            # -------------------------------
            ,
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
            # SYNC(id=3, wait_response=False)
            # SYNC(id=4, wait_response=True)
            # -------------------------------
            ,
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
            # SYNC(id=5, wait_response=False)
            # SYNC(id=6, wait_response=True)
            # -------------------------------
        ]
        self.queue_test_sut = [
            # SYNC(id=1, wait_response=False)
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(payload=PAYLOAD)
            )
            # SYNC(id=2, wait_response=True)
            #
            # -------------------------------
            #
            # SYNC(id=3, wait_response=False)
            ,
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(payload=PAYLOAD)
            )
            # SYNC(id=4, wait_response=True)
            #
            # -------------------------------
            #
            # SYNC(id=5, wait_response=False)
            ,
            TestCommand(
                self.test_id,
                CommandType['SEND'],
                SendParameters(payload=PAYLOAD)
            )
            # SYNC(id=6, wait_response=True)
            # -------------------------------
        ]
