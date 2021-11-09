#!/usr/bin/env python3

from random import randint

from scapy.all import *

from tcpTester.baseRunner import BaseRunner
from tcpTester.testCommand import (
    TestCommand,
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    SendParameters,
    SendReceiveParameters,
    UserException,
    DEFAULT_TIMEOUT
)

class TestServer(BaseRunner):
    def __init__(self, ts_iface):
        super().__init__()

        self.logger.info("test server started")

        self.ip = None
        self.seq = -1
        self.ack = -1
        self.sport = -1
        self.dport = -1
        self.ts_iface = ts_iface

    @property
    def logger(self):
        return logging.getLogger("TestServer")

    def reset(self) -> None:
        self.seq = randint(3000000, 5999999)
        self.ack = -1
        self.sport = -1
        self.dport = -1

    def update_sequence_num(self, packet: Packet) -> None:
        self.seq += TestServer.packet_length(packet)

    def update_ack_num(self, packet: Packet) -> None:
        self.ack = packet.seq + TestServer.packet_length(packet)

    @staticmethod
    def packet_length(packet: Packet) -> int:
        size = 0
        if Raw in packet:
            size = len(packet[Raw].load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    @staticmethod
    def get_missing_flags(packet: Packet, exp_flags: Optional[str]) -> List[str]:
        if not exp_flags:
            return []

        return list(filter(lambda f: f not in packet.sprintf("%TCP.flags%"), exp_flags))

    @staticmethod
    def validate_payload(packet: Packet, exp_payload: Optional[bytes] = None) -> None:
        payload = packet[Raw].load if Raw in packet else b''
        if exp_payload and exp_payload != payload:
            logging.getLogger("PayloadValidator").warning("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

    def validate_packet_seq(self, packet: Packet) -> None:
        if self.ack == -1:
            # first packet received in a new connection
            # thus have no previous knowledge about the other
            # party's seq value
            return

        if packet.seq > self.ack:
            self.logger.info("Received future packet with seq %s != %s", packet.seq, self.ack)
            raise UserException(f"Received future packet with seq {packet.seq} != {self.ack}")

        if packet.seq < self.ack:
            self.logger.info("Received past packet with seq %s != %s", packet.seq, self.ack)
            raise UserException(f"Received past packet with seq {packet.seq} != {self.ack}")

    def validate_packet_ack(self, packet: Packet) -> None:
        if self.ack == -1:
            # first packet received in a new connection
            # so the other party does not know our seq
            return

        if packet.ack > self.seq:
            self.logger.info("Received packet with future ack %s != %s", packet.ack, self.seq)
            raise UserException(f"Received packet with future ack {packet.ack} != {self.seq}")

        if packet.ack < self.seq:
            self.logger.info("Received packet with past ack %s != %s", packet.ack, self.seq)
            raise UserException(f"Received packet with past ack {packet.ack} != {self.seq}")

    def _sniff(self,
               num_packets: int,
               exp_flags: Optional[str],
               timeout: Optional[int] = None) -> List[Packet]:
        queue = []
        self.logger.info("Starting sniffing..")

        def pkt_filter(pkt: Packet) -> bool:
            return TCP in pkt and \
                   pkt.dport == self.sport and \
                   len(TestServer.get_missing_flags(pkt, exp_flags)) == 0

        sniff(count=num_packets,
              store=False,
              iface=self.ts_iface,
              lfilter=pkt_filter,
              prn=queue.append,
              timeout=timeout)

        return queue

    def send(self, packet: Packet, update_seq: bool = True) -> None:
        send(packet)
        if update_seq:
            self.update_sequence_num(packet)

    def recv(self,
             exp_flags: Optional[str] = None,
             timeout: Optional[int] = None) -> Optional[Packet]:

        packets = self._sniff(1, exp_flags=exp_flags, timeout=timeout)
        if not packets:
            return None

        [packet] = packets
        self.logger.info("Calculated packet length as %s", TestServer.packet_length(packet))
        self.validate_packet_seq(packet)
        self.validate_packet_ack(packet)

        self.update_ack_num(packet)
        return packet

    def sr(self,
           packet: Packet,
           exp_flags: Optional[str] = None,
           timeout: int = DEFAULT_TIMEOUT,
           update_seq: bool = True) -> Packet:

        recv_packet = sr1(packet, iface=self.ts_iface, timeout=timeout)
        if update_seq:
            self.update_sequence_num(packet)
        self.logger.info('first packet sent')

        if not recv_packet:
            self.logger.info("timeout reached, could not detect packet ")
            raise UserException("Got no response to packet")

        missing_flags = self.get_missing_flags(recv_packet, exp_flags=exp_flags)
        if missing_flags:
            self.logger.info('packet received with missing flags: %s', missing_flags)
            raise UserException(f"Received packet with invalid flags {str(missing_flags)}")

        self.logger.info('packet received')

        self.validate_packet_seq(recv_packet)
        self.validate_packet_ack(recv_packet)
        self.update_ack_num(recv_packet)

        return recv_packet

    def make_packet(self,
                    payload: Optional[bytes] = None,
                    seq: Optional[int] = None,
                    ack: Optional[int] = None,
                    flags: Optional[str] = None) -> Packet:

        packet_ack = (0 if self.ack == -1 else self.ack) if ack is None else ack
        pkt = self.ip / TCP(sport=self.sport,
                            dport=self.dport,
                            seq=(self.seq if seq is None else seq),
                            ack=packet_ack,
                            flags=(flags or ""))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handle_listen_command(self, parameters: ListenParameters) -> TestCommand:
        self.logger.info("Listening for Syn packet")
        self.reset()

        self.sport = parameters.src_port
        packet = self.recv()

        if not packet:
            raise UserException("Listen timed out")

        self.logger.info("Packet received from %s", packet[IP].src)
        self.ip = IP(dst=packet[IP].src)

        flags = packet.sprintf("%TCP.flags%")
        if "S" not in flags:
            raise UserException(f"Invalid flags received: expected 'S' got {flags}")

        self.dport = packet.sport

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["LISTEN"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handle_connect_command(self, parameters: ConnectParameters) -> TestCommand:
        self.logger.info("connecting to %s", parameters.dst_port)
        self.reset()

        self.ip = IP(dst=parameters.destination)
        self.sport = parameters.src_port
        self.dport = parameters.dst_port

        syn = self.make_packet(flags="S")

        if not parameters.full_handshake:
            self.send(syn)
            self.logger.info("single syn sent")
            return self.make_result(ResultParameters(
                status=0,
                operation=CommandType["CONNECT"]
            ))

        self.logger.info("sending first syn")
        synack = self.sr(syn, exp_flags="SA")
        self.logger.info("response is syn/ack")

        ack = self.make_packet(flags="A")
        send(ack)

        self.logger.info("sent ack")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"],
            description=f"Last Packet received: {synack.__repr__()}"
        ))

    def handle_send_command(self, parameters: SendParameters) -> TestCommand:
        self.logger.info("Sending packet with flags: %s", parameters.flags)

        pkt = self.make_packet(
            payload=parameters.payload,
            seq=parameters.sequence_number,
            ack=parameters.acknowledgement_number,
            flags=parameters.flags
        )

        self.send(pkt, update_seq=parameters.update_ts_seq)
        self.logger.info("Packet was sent")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
            description=f"Sent this payload: {parameters.payload}"
        ))

    def handle_receive_command(self, parameters: ReceiveParameters) -> TestCommand:
        self.logger.info("Receiving packet with expected flags: %s", parameters.flags)

        packet = self.recv(exp_flags=parameters.flags, timeout=parameters.timeout)
        self.logger.info("Sniffing finished")

        if not packet:
            self.logger.warning("no packet received due to timeout")
            raise UserException("Timeout reached")

        TestServer.validate_payload(packet, parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handle_send_receive_command(self, parameters: SendReceiveParameters) -> TestCommand:
        send_params = parameters.send_parameters
        self.logger.info("Sending packet with flags: %s", send_params.flags)

        pkt = self.make_packet(
            payload=send_params.payload,
            seq=send_params.sequence_number,
            ack=send_params.acknowledgement_number,
            flags=send_params.flags
        )
        self.logger.info("Created packet")

        ret = self.sr(pkt,
                      exp_flags=parameters.receive_parameters.flags,
                      timeout=parameters.receive_parameters.timeout,
                      update_seq=parameters.send_parameters.update_ts_seq)
        self.logger.info("SR completed")

        TestServer.validate_payload(ret, parameters.receive_parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SENDRECEIVE"],
            description=f"Packet received: {ret.__repr__()}"
        ))

    def handle_disconnect_command(self) -> TestCommand:
        self.logger.info("graceful disconnect from client")

        fin = self.make_packet(flags="FA")
        finack = self.sr(fin, exp_flags="FA")
        self.logger.info("send fin packet")

        self.logger.info("sending ack")
        ack = self.make_packet(flags="A")
        send(ack)
        self.logger.info("ack send")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"],
            description=f"Last Packet received: {finack.__repr__()}"
        ))

    def handle_abort_command(self) -> TestCommand:
        self.logger.info("aborting connection")
        self.reset()
        self.logger.info("abort done.")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
