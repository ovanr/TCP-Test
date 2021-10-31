#!/usr/bin/env python3

import logging
from random import randint
from typing import Optional

from scapy.layers.inet import IP, TCP
from scapy.packet import Packet, Raw
from scapy.sendrecv import send, sniff

from tcpTester.baseRunner import BaseRunner
from tcpTester.config import TEST_SERVER_INTERFACE
from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    ReceiveParameters,
    ResultParameters,
    SendParameters,
    SendReceiveParameters,
    UserException,
)

# timeout for the sr1 command (in seconds)
TIMEOUT = 20


class TestServer(BaseRunner):
    def __init__(self):
        super().__init__()

        logging.getLogger("").setLevel(logging.INFO)
        logging.info("test server started")

        self.ip = None
        self.seq = -1
        self.ack = -1
        self.sport = -1
        self.dport = -1

    def reset(self):
        self.seq = randint(3000000, 5999999)
        self.ack = 0
        self.sport = 0
        self.dport = 0

    def update_sequence_num(self, packet: Packet):
        self.seq += TestServer.packet_length(packet)

    def update_ack_num(self, packet: Packet):
        packet_ack = packet.seq + TestServer.packet_length(packet)
        if packet_ack > self.ack:
            self.ack = packet_ack
        else:
            logging.info("Received packet with duplicate Ack %s", packet_ack)

    @staticmethod
    def packet_length(packet: Packet):
        size = 0
        if Raw in packet:
            size = len(packet[Raw].load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    @staticmethod
    def missing_flags(packet: Packet, exp_flags: Optional[str]):
        if not exp_flags:
            return []

        missing_flags = filter(lambda f: f not in packet.sprintf("%TCP.flags%"), exp_flags)

        return list(missing_flags)

    @staticmethod
    def validate_payload(packet: Packet, exp_payload: Optional[bytes] = None):
        payload = packet[Raw].load if Raw in packet else b''
        if exp_payload and exp_payload != payload:
            logging.warning("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

    def _sniff(self, num_packets: int, exp_flags: Optional[str], timeout: Optional[int] = None):
        queue = []
        logging.info("Starting sniffing..")

        def pkt_filter(pkt):
            return TCP in pkt and pkt.dport == self.sport and len(TestServer.missing_flags(pkt, exp_flags)) == 0

        sniff(count=num_packets,
              store=False,
              iface=TEST_SERVER_INTERFACE,
              lfilter=pkt_filter,
              prn=queue.append,
              timeout=timeout)

        return queue

    def send(self, packet: Packet):
        send(packet)
        self.update_sequence_num(packet)

    def recv(self, exp_flags: Optional[str] = None, timeout: Optional[int] = None):
        packets = self._sniff(1, exp_flags=exp_flags, timeout=timeout)
        if not packets:
            return None
        [packet] = packets
        logging.info("Calculated packet length as %s", TestServer.packet_length(packet))
        self.update_ack_num(packet)
        return packet

    def sr(self, packet: Packet, exp_flags: Optional[str] = None):
        self.send(packet)
        logging.info('first packet sent')
        ret = self.recv(exp_flags=exp_flags, timeout=TIMEOUT)
        logging.info('packet received')

        if not ret:
            logging.info("timeout reached, could not detect packet with flags %s", exp_flags)
            raise UserException("Got no response to packet")

        return ret

    def make_packet(self,
                    payload: Optional[bytes] = None,
                    seq: Optional[int] = None,
                    ack: Optional[int] = None,
                    flags: Optional[str] = None):

        pkt = self.ip / TCP(sport=self.sport,
                            dport=self.dport,
                            seq=(self.seq if seq is None else seq),
                            ack=(self.ack if ack is None else ack),
                            flags=(flags or ""))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handle_listen_command(self, parameters: ListenParameters):
        logging.info("Listening for Syn packet")
        self.reset()

        self.sport = parameters.src_port
        packet = self.recv()

        if not packet:
            raise UserException("Listen timed out")

        logging.info("Packet received from %s", packet[IP].src)
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

    def handle_connect_command(self, parameters: ConnectParameters):
        logging.info("connecting to %s", parameters.dst_port)
        self.reset()

        self.ip = IP(dst=parameters.destination)
        self.sport = parameters.src_port
        self.dport = parameters.dst_port

        syn = self.make_packet(flags="S")

        if not parameters.full_handshake:
            self.send(syn)
            logging.info("single syn sent")
            return self.make_result(ResultParameters(
                status=0,
                operation=CommandType["CONNECT"]
            ))

        logging.info("sending first syn")
        synack = self.sr(syn, exp_flags="SA")
        logging.info("response is syn/ack")

        ack = self.make_packet(flags="A")
        send(ack)

        logging.info("sent ack")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"],
            description=f"Last Packet received: {synack.__repr__()}"
        ))

    def handle_send_command(self, parameters: SendParameters):
        logging.info("Sending packet with flags: %s", parameters.flags)

        pkt = self.make_packet(
            payload=parameters.payload,
            seq=parameters.sequence_number,
            ack=parameters.acknowledgement_number,
            flags=parameters.flags
        )

        self.send(pkt)
        logging.info("Packet was sent")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
            description=f"Sent this payload: {parameters.payload}"
        ))

    def handle_receive_command(self, parameters: ReceiveParameters):
        logging.info("Receiving packet with expected flags: %s", parameters.flags)

        packet = self.recv(exp_flags=parameters.flags, timeout=parameters.timeout)
        logging.info("Sniffing finished")

        if not packet:
            logging.warning("no packet received due to timeout")
            raise UserException("Timeout reached")

        TestServer.validate_payload(packet, parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handle_send_receive_command(self, parameters: SendReceiveParameters):
        send_params = parameters.send_parameters
        logging.info("Sending packet with flags: %s", send_params.flags)

        pkt = self.make_packet(
            payload=send_params.payload,
            seq=send_params.sequence_number,
            ack=send_params.acknowledgement_number,
            flags=send_params.flags
        )
        logging.info("Created packet")

        ret = self.sr(pkt, exp_flags=parameters.receive_parameters.flags)
        logging.info("SR completed")

        TestServer.validate_payload(ret, parameters.receive_parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SENDRECEIVE"],
            description=f"Packet received: {ret.__repr__()}"
        ))

    def handle_disconnect_command(self):
        logging.info("graceful disconnect from client")

        fin = self.make_packet(flags="FA")
        finack = self.sr(fin, exp_flags="FA")
        logging.info("send fin packet")

        logging.info("sending ack")
        ack = self.make_packet(flags="A")
        send(ack)
        logging.info("ack send")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"],
            description=f"Last Packet received: {finack.__repr__()}"
        ))

    def handle_abort_command(self):
        logging.info("aborting connection")
        self.reset()
        logging.info("abort done.")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
