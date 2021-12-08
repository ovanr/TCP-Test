import configparser
import random
import sys
import socket
import time

import jsonpickle
from termcolor import colored

from tests import UserCall, CommandType, ListenParameters, TCPPacket, SEQ, ACK, TCPFlag
from tests.tcpTester.types import UserCallResult, UserCallResultType, ConnectParameters


class TCPModel:

    _test_ts_port: int = 0
    _test_sut_port: int = 0
    _port_history: set[int] = set()

    def get_random_unique_port(self) -> int:
        a = random.randint(10000, 12000)
        while a in self._port_history:
            a = random.randint(10000, 12000)
        self._port_history.add(a)
        return a

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("altwalker.ini")

        if "sut" not in config:
            print(colored("Config file does no contain sut settings!", "red"))
            sys.exit(-1)

        if "test_server" not in config:
            print(colored("Config file does no contain test server settings!", "red"))
            sys.exit(-1)

        try:
            self.sut_ip = config["sut"]["ip"]
            self.sut_port = int(config["sut"]["port"])
        except KeyError as err:
            print(colored("Config file does no contain sut ip setting: %s", "red"), err)
            sys.exit(-1)

        try:
            self.ts_ip = config["test_server"]["ip"]
            self.ts_port = int(config["test_server"]["port"])
        except KeyError as err:
            print(colored("Config file does no contain ts ip setting: %s", "red"), err)
            sys.exit(-1)

        self.sut_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ts_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def setUpModel(self):
        self.sut_client.connect((self.sut_ip,self.sut_port))
        self.ts_client.connect((self.ts_ip, self.ts_port))
        self.sut_file_client = self.sut_client.makefile('wr')
        self.ts_file_client  = self.ts_client.makefile('wr')

    def tearDownModel(self):
        self.sut_client.close()
        self.ts_client.close()

    # State functions

    def established(self):
        pass

    def start(self):
        self._test_sut_port = self.get_random_unique_port()
        print(f"Test SUT port: {self._test_sut_port}")
        self._test_ts_port = self.get_random_unique_port()
        print(f"Test TS port: {self._test_ts_port}")

    def sut_active_close(self):
        pass

    def sut_active_connect(self):
        pass

    def sut_fin_ack_received(self):
        pass

    def sut_fin_ack_send(self):
        pass

    def sut_listen(self):
        pass

    def sut_passive_close(self):
        pass

    def sut_passive_connect(self):
        pass

    def sut_payload_received(self):
        self.sut_file_client.write(
            jsonpickle.encode(
                UserCall(
                    command_type=CommandType.RECEIVE
                )
            ) + "\n"
        )
        self.sut_file_client.flush()

        package: UserCallResult = jsonpickle.decode(self.sut_file_client.readline())
        print("SUT usercall result: %s", package)

        if package.status != UserCallResultType.RECEIVE:
            raise AssertionError(f"Expected success response, got: {package}")
        if package.payload != b"AltwalkerSaysHi":
            raise AssertionError(f"Expected payload \"AltwalkerSaysHi\", got: {package}")

    def sut_syn_ack_send(self):
        pass

    def sut_syn_recvd_send_ack(self):
        pass

    def sut_wait_for_ack(self):
        pass

    # Transition functions

    def sut_enter_listen_state(self):
        self.sut_file_client.write(
            jsonpickle.encode(UserCall(
                command_type=CommandType.LISTEN,
                command_parameters=ListenParameters(self._test_sut_port))
            ) + "\n"
        )
        self.sut_file_client.flush()
        time.sleep(0.05)

    def sut_payload_receive(self):
        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.ACK],
                    payload=b"AltwalkerSaysHi"
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

    def sut_receive_ack(self):
        pass

    def sut_receive_ack_2(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.ACK in package.flags and TCPFlag.FIN in package.flags):
            raise AssertionError(f"Expected ack package, got: {package}")
        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.ACK],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

        package: UserCallResult = jsonpickle.decode(self.sut_file_client.readline())
        print("SUT usercall result: %s", package)

        if package.status != UserCallResultType.SUCCESS:
            raise AssertionError(f"Expected success response, got: {package}")

    def sut_receive_fin(self):
        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.FIN, TCPFlag.ACK],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

    def sut_receive_fin_ack(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.ACK in package.flags and TCPFlag.FIN in package.flags) :
            raise AssertionError(f"Expected fin package, got: {package}")

        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.FIN, TCPFlag.ACK],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

    def sut_receive_handshake_ack(self):
        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.ACK],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()
        time.sleep(0.05)

        package: UserCallResult = jsonpickle.decode(self.sut_file_client.readline())
        print("SUT usercall result: %s", package)

        if package.status != UserCallResultType.SUCCESS:
            raise AssertionError(f"Expected success response, got: {package}")

    def sut_receive_syn(self):
        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.SYN],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

    def sut_receive_syn_ack(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.SYN in package.flags):
            raise AssertionError(f"Expected syn package, got: {package}")

        self.ts_file_client.write(
            jsonpickle.encode(
                TCPPacket(
                    sport=self._test_ts_port,
                    dport=self._test_sut_port,
                    seq=SEQ.SEQ_VALID,
                    ack=ACK.ACK_VALID,
                    flags=[TCPFlag.SYN, TCPFlag.ACK],
                    payload=bytes()
                )
            ) + "\n"
        )
        self.ts_file_client.flush()

    def sut_ack_send(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.ACK in package.flags):
            raise AssertionError(f"Expected ack package, got: {package}")

        package: UserCallResult = jsonpickle.decode(self.sut_file_client.readline())
        print("SUT usercall result: %s", package)

        if package.status != UserCallResultType.SUCCESS:
            raise AssertionError(f"Expected success response, got: {package}")

    def sut_ack_send_2(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.ACK in package.flags):
            raise AssertionError(f"Expected ack package, got: {package}")

    def sut_send_fin(self):
        self.sut_file_client.write(
            jsonpickle.encode(
                UserCall(
                    command_type=CommandType.CLOSE
                )
            ) + "\n"
        )
        self.sut_file_client.flush()

    def sut_send_fin_ack(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if (TCPFlag.ACK not in package.flags) or TCPFlag.FIN in package.flags:
            raise AssertionError(f"Expected ack package, got: {package}")

        self.sut_file_client.write(
            jsonpickle.encode(
                UserCall(
                    command_type=CommandType.CLOSE
                )
            ) + "\n"
        )
        self.sut_file_client.flush()

    def sut_send_payload(self):
        pass

    def sut_send_syn(self):
        self.sut_file_client.write(
            jsonpickle.encode(
                UserCall(
                    command_type=CommandType.CONNECT,
                    command_parameters=ConnectParameters(dst_port=self._test_ts_port, src_port=self._test_sut_port)
                )
            )+ "\n"
        )
        self.sut_file_client.flush()
        time.sleep(0.05)

    def sut_send_syn_ack(self):
        package: TCPPacket = jsonpickle.decode(self.ts_file_client.readline())
        print("SUT Send: %s", package)

        if not (TCPFlag.ACK in package.flags and TCPFlag.SYN in package.flags):
            raise AssertionError(f"Expected syn ack package, got: {package}")

