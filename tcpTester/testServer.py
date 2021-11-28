#!/usr/bin/env python3

from random import randint
from typing import Optional, List, TextIO

from scapy.all import *
from scapy.layers.inet import TCP, IP

from tcpTester.types import ACK, SEQ, TCPPacket, TCPFlag

class TestServer:
    """
    Implementation of the TestServer.
    """

    def __init__(self, ts_iface: str, sut_ip: str, mbt_client: TextIO):
        """
        Initializes class variables.
        """
        self.logger.info("test server started")

        # Variables used for stubbing a communication partner for a TCP endpoint.
        self.ip = IP(dst=sut_ip)
        self.seq = -1
        self.ack = -1
        self.sport = -1
        self.dport = -1
        self.ts_iface = ts_iface
        self.bg_sniffer = None
        self.lock = Lock()

        self.mbt_client = mbt_client
        self.start_bg_sniffer()

    @property
    def logger(self):
        """
        Returns the logger used for the TestServer.

        :return: The logger for the TestServer.
        """
        return logging.getLogger("TestServer")

    def reset(self) -> None:
        """
        Resets the variables that the TestServer uses for TCP communication.

        :return: None
        """
        self.seq = randint(3000000, 4999999)
        self.ack = -1
        self.sport = -1
        self.dport = -1

    def update_sequence_num(self, packet: Packet) -> None:
        """
        Updates the internal sequence number of the TestServer based on a given packet.
        """
        self.seq += TestServer.packet_length(packet)

    def update_ack_num(self, packet: Packet) -> None:
        """
        Updates the internal acknowledgement number of the TestServer based on a given packet.
        """
        self.ack = packet.seq + TestServer.packet_length(packet)

    @staticmethod
    def packet_length(packet: Packet) -> int:
        """
        Determines the length of a given packet.
        The fin (F) and syn (S) flags are also counted towards the length in case they are present in the packet.

        :param packet: The packet for which to determine the length.

        :return: The length of the packet.
        """
        size = 0
        if Raw in packet:
            size = len(packet[Raw].load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    def validate_packet_seq(self, packet: Packet) -> bool:
        """
        Validates the sequence number of a given packet.
        """
        if self.ack == -1:
            # first packet received in a new connection
            # thus have no previous knowledge about the other
            # party's seq value
            return True

        if packet.seq > self.ack:
            self.logger.info("Received future packet with seq %s != %s", packet.seq, self.ack)
            return False

        if packet.seq < self.ack:
            if packet.seq + TestServer.packet_length(packet) == self.ack:
                # duplicate packet
                self.logger.info("Got duplicate packet %s != %s", packet.seq, self.ack)
                return True
            self.logger.info("Received past packet with seq %s != %s", packet.seq, self.ack)
            return False

        return True

    def validate_packet_ack(self, packet: Packet) -> bool:
        """
        Validates the acknowledgement number of a given packet.
        """
        if self.ack == -1:
            # first packet received in a new connection
            # so the other party does not know our seq
            return True

        if packet.ack > self.seq:
            self.logger.info("Received packet with future ack %s != %s", packet.ack, self.seq)
            return False

        if packet.ack < self.seq:
            self.logger.info("Received packet with past ack %s != %s", packet.ack, self.seq)
            return False
        return True


    def start_bg_sniffer(self, timeout: Optional[int] = None) -> List[Packet]:
        """
        Sniffs a given number of packets.

        """
        self.logger.info("Starting sniffing..")

        def pkt_filter(pkt: Packet) -> bool:
            return TCP in pkt and \
                    pkt.sport >= 10000 and \
                    pkt.sport <= 12000 and \
                    pkt[IP].src == self.ip.dst

        if self.bg_sniffer:
            self.bg_sniffer.stop(join=True)
            self.bg_sniffer = None

        self.bg_sniffer = AsyncSniffer(
            count=0,
            store=False,
            iface=self.ts_iface,
            lfilter=pkt_filter,
            prn=self.handle_receive_command,
            timeout=timeout)

        self.bg_sniffer.start()

    def stop_bg_sniffer(self):
        if self.bg_sniffer:
            self.bg_sniffer.stop(join=True)
            self.bg_sniffer = None

    def send(self, packet: Packet, update_seq: bool = True) -> None:
        """
        Sends a given packet and optionally updates the TestServer's internal sequence number afterwards.

        :param packet: The packet to send.
        :param update_seq: Whether the packet's sequence number should be updated after it is send.

        :return: None
        """
        send(packet)
        if update_seq:
            self.update_sequence_num(packet)

    def make_packet(self,
                    payload: Optional[bytes] = None,
                    seq: Optional[int] = None,
                    ack: Optional[int] = None,
                    flags: Optional[str] = None) -> Packet:
        """
        Creates a new packet from TCP header properties and payload.

        :param payload: Optional payload for the packet.
        :param seq: Optional sequence number for the packet.
        :param ack: Optional acknowledgement number for the packet.
        :param flags: Optional list of flags for the packet.

        :return: The newly created packet.
        """
        packet_ack = self.ack if ack is None else ack
        packet_ack = max(packet_ack, 0)
        pkt = self.ip / TCP(sport=self.sport,
                            dport=self.dport,
                            seq=(self.seq if seq is None else seq),
                            ack=packet_ack,
                            flags=(flags or ""))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handle_send_command(self, packet: TCPPacket):
        with self.lock:
            return self._handle_send_command(packet)

    def _handle_send_command(self, packet: TCPPacket):
        """
        Sends a given packet to the TCP endpoint for which the TestServer stubs a communication partner.
        """
        self.logger.info("Sending packet: %s", packet)

        update_seq=True

        if packet.sport != self.sport or \
           packet.dport != self.dport:
            self.reset()
            self.sport = packet.sport
            self.dport = packet.dport
            time.sleep(2)

        if packet.seq == SEQ.SEQ_VALID:
            sequenceno = self.seq
        else:
            sequenceno = randint(3000000, 5999999)
            update_seq = False

        if packet.ack == ACK.ACK_VALID:
            ackno = self.ack
        else:
            ackno = randint(3000000, 5999999)
            update_seq = False


        pkt = self.make_packet(
            payload=packet.payload,
            seq=sequenceno,
            ack=ackno,
            flags=list(map(lambda f: f.name[0], packet.flags))
        )

        self.send(pkt, update_seq=update_seq)

        self.logger.info("Packet was sent")

    def handle_receive_command(self, packet: Packet):
        with self.lock:
            return self._handle_receive_command(packet)

    def _handle_receive_command(self, packet: Packet):
        """
        Receives a single packet from the TCP endpoint for which the TestServer stubs a communication partner.
        """

        self.logger.info("Received a packet")

        if (self.sport != packet.dport or self.dport != packet.sport) and \
           "S" in packet.sprintf("%TCP.flags%"):
            self.logger.info("Received syn packet %s", packet.__repr__())
            self.reset()
            self.sport = packet.dport
            self.dport = packet.sport

        if packet.dport != self.sport or \
           packet.sport != self.dport:
            self.logger.info("Received packet not intended for us %s", packet.__repr__())
            return

        if self.validate_packet_seq(packet):
            seq_status = SEQ.SEQ_VALID
        else:
            seq_status = SEQ.SEQ_INVALID

        if self.validate_packet_ack(packet):
            ack_status = ACK.ACK_VALID
        else:
            ack_status = ACK.ACK_INVALID

        if ack_status == ACK.ACK_VALID and \
           seq_status == SEQ.SEQ_VALID and \
           packet.seq >= self.ack:
            self.update_ack_num(packet)

        abs_packet = TCPPacket(
            sport=packet["TCP"].sport,
            dport=packet["TCP"].dport,
            seq=seq_status,
            ack=ack_status,
            flags=list(map(TCPFlag, filter(lambda t: t in ["S", "F", "A", "R" ], packet.sprintf("%TCP.flags%")))),
            payload=packet[Raw].load if Raw in packet else b''
        )

        raw = abs_packet.to_torxakis()
        self.logger.info("Forwarding packet: %s", raw)
        self.mbt_client.write(raw + "\n")
