#!/usr/bin/env python3

from random import randint
from struct import pack
from sys import flags
from typing import Optional, List

from scapy.all import *

from tcpTester.types import ACK, SEQ, TCPPacket

class TestServer:
    """
    Implementation of the TestServer.
    """

    def __init__(self, ts_iface, mbt_port: int):
        """
        Initializes class variables.
        """
        super().__init__()

        self.logger.info("test server started")

        # Variables used for stubbing a communication partner for a TCP endpoint.
        self.ip = None
        self.seq = -1
        self.ack = -1
        self.sport = -1
        self.dport = -1
        self.ts_iface = ts_iface
        self.bg_sniffer = None

        self.mbt_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mbt_server.bind(("", mbt_port))
        self.mbt_server.listen(1)
        (self.mbt_client, _) = self.mbt_server.accept()

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
        self.seq = randint(3000000, 5999999)
        self.ack = -1
        self.sport = -1
        self.dport = -1

    def update_sequence_num(self, packet: Packet) -> None:
        """
        Updates the internal sequence number of the TestServer based on a given packet.

        :param packet: The packet from which the new sequence number is to be determined.

        :return: None
        """
        self.seq += TestServer.packet_length(packet)

    def update_ack_num(self, packet: Packet) -> None:
        """
        Updates the internal acknowledgement number of the TestServer based on a given packet.

        :param packet: The packet from which the new acknowledgement number is to be determined.

        :return: None
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

        :param packet: The packet for which to update the sequence number.

        :raise UserException: If the packet's sequence number conflicts with the TestServer's internal acknowledgement number tracking.

        :return: None
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
            self.logger.info("Received past packet with seq %s != %s", packet.seq, self.ack)
            return False
        return True

    def validate_packet_ack(self, packet: Packet) -> bool:
        """
        Validates the acknowledgement number of a given packet.

        :param packet: The packet for which to update the acknowledgement number.

        :raise UserExpection: If the packet's acknowledgement number conflicts with the TestServer's internal sequence number tracking.

        :return: None
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
                   pkt.dport == self.sport and \
                   pkt.sport == self.dport

        if self.bg_sniffer:
            self.bg_sniffer.stop(join=True)
            self.bg_sniffer = None

        self.bg_sniffer = AsyncSniffer(
            count=0,
            store=False,
            iface=self.ts_iface,
            lfilter=pkt_filter,
            prn=lambda p: self.handle_receive_command(p),
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
        packet_ack = (0 if self.ack == -1 else self.ack) if ack is None else ack
        pkt = self.ip / TCP(sport=self.sport,
                            dport=self.dport,
                            seq=(self.seq if seq is None else seq),
                            ack=packet_ack,
                            flags=(flags or ""))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handle_send_command(self, packet: TCPPacket):
        """
        Handles a TestCommand of type SEND.
        Sends a given payload to the TCP endpoint for which the TestServer stubs a communication partner.

        :param parameters: The parameters for the SEND command.

        :return: A TestCommand of type SEND.
        """
        self.logger.info("Sending packet with flags: %s", packet.flags)

        
        # TODO: Update sequence numbers
        if packet.seq == SEQ.SEQ_VALID:
            sequenceno = self.seq
        else:
            sequenceno = randint(3000000, 5999999)

        # TODO: Update acknowledgement numbers
        if packet.ack == ACK.ACK_VALID:
            ackno = self.ack
        else:
            ackno = randint(3000000, 5999999)


        pkt = self.make_packet(
            payload=packet.payload,
            seq=sequenceno,
            ack=ackno,
            flags=packet.flags
        )

        self.send(pkt, update_seq=True)
        self.logger.info("Packet was sent")

    def handle_receive_command(self, packet):
        """
        Handles a TestCommand of type RECEIVE.
        Receives a single packet from the TCP endpoint for which the TestServer stubs a communication partner.

        :param parameters: The parameters for the RECEIVE command.

        :raise UserException: If the timeout from the command parameters is reached before a packet is received.

        :return: A TestCommand of type RECEIVE.
        """
        
        
        if self.validate_packet_seq(packet):
            seq_status = SEQ.SEQ_VALID
        else:
            seq_status = SEQ.SEQ_INVALID

        if self.validate_packet_ack(packet):
            ack_status = ACK.ACK_VALID
        else:
            ack_status = ACK.ACK_INVALID

        if ack_status == ACK.ACK_VALID and seq_status == SEQ.SEQ_VALID:
            self.update_ack_num(packet)

        return TCPPacket(
            sport=packet["TCP"].sport,
            dport=packet["TCP"].dport,
            seq=seq_status,
            ack=ack_status,
            flags=packet["flags"],
            payload=packet[Raw].load
        )
