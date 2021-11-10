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
    DisconnectParameters,
    SendParameters,
    SendReceiveParameters,
    UserException,
    DEFAULT_TIMEOUT
)

# timeout for the sr1 command (in seconds)
TIMEOUT = 5


class TestServer(BaseRunner):
    """
    Implementation of the TestServer.
    """

    def __init__(self, ts_iface):
        """
        Initializes class variables.
        """
        super().__init__()

        self.logger.info("test server started")

        # Variables used for TCP communication
        self.ip = None
        self.seq = -1
        self.ack = -1
        self.sport = -1
        self.dport = -1
        self.ts_iface = ts_iface

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
        Updates the sequence number of a given packet.

        :param packet: The packet for which to update the sequence number.

        :return: None
        """
        self.seq += TestServer.packet_length(packet)

    def update_ack_num(self, packet: Packet) -> None:
        """
        Updates the acknowledgement number of a given packet.

        :param packet: The packet for which to update the acknowledgement number.

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

    @staticmethod
    def get_missing_flags(packet: Packet, exp_flags: Optional[str]) -> List[str]:
        """
        Returns the TCP flags from a given list of expected flags that are not present in a given packet.

        :param packet: The packet for which to get the missing flags.
        :param exp_flags: The list of expected flags.

        :return: The list of TCP flags that are missing from the packet but present in the list of expected flags.
        """
        if not exp_flags:
            return []

        return list(filter(lambda f: f not in packet.sprintf("%TCP.flags%"), exp_flags))

    @staticmethod
    def validate_payload(packet: Packet, exp_payload: Optional[bytes] = None) -> None:
        """
        Validates that the payload of a given packet is equal to a given expected payload.

        :param packet: The packet of which the payload is validated.
        :param exp_payload: The expected payload with which the payload of the packet is compared.

        :raise UserException: If the packet's payload doesn't match the expected payload.

        :return: None
        """
        payload = packet[Raw].load if Raw in packet else b''
        if exp_payload and exp_payload != payload:
            logging.getLogger("PayloadValidator").warning("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

    def validate_packet_seq(self, packet: Packet) -> None:
        """
        Validates the sequence number of a given packet.

        :param packet: The packet for which to update the sequence number.

        :raise UserException: If the packet's sequence number conflicts with its acknowledgement number.

        :return: None
        """
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
        """
        Validates the acknowledgement number of a given packet.

        :param packet: The packet for which to update the acknowledgement number.

        :raise UserExpection: If the packet's acknowledgement number conflicts with its sequence number.

        :return: None
        """
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
        """
        Sniffs a given number of packets.
        Returns a list of the packets that were destined for the TestServer and that have all of the flags from a given list of flags.

        :param num_packets: The number of packets to sniff.
        :param exp_flags: The list of flags which a packet must have to be included in the result list.
        :param timeout: Optional timeout. Function stops sniffing if this timeout expires before it is done.

        :return: The list of sniffed packets that have all of the expected flags.
        """
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
        """
        Sends a given packet and optionally updates the packet's sequence number afterwards.

        :param packet: The packet to send.
        :param update_seq: Whether the packet's sequence number should be updated after it is send.

        :return: None
        """
        send(packet)
        if update_seq:
            self.update_sequence_num(packet)

    def recv(self,
             exp_flags: Optional[str] = None,
             timeout: Optional[int] = None,
             update_ack: bool = True) -> Optional[Packet]:
        """
        Receives and validates a packet that has all of the flags from a given list of flags.
        Stops waiting for a packet if one doesn't arrive before the given timeout expires.

        :param exp_flags: Optional list of flags, all of which a packet must have.
        :param timeout: Optional timeout.
        :param update_ack: Whether the acknowledgement number of the received packet must be updated.

        :return:
            - The received packet in case one that has all required flags arrives on time.
            - None otherwise.
        """
        packets = self._sniff(1, exp_flags=exp_flags, timeout=timeout)
        if not packets:
            return None

        [packet] = packets
        self.logger.info("Calculated packet length as %s", TestServer.packet_length(packet))

        if exp_flags is not None and "R" in exp_flags:
            self.logger.info("Received package has reset flag. No ACK and SEQ checking.")
            return packet

        self.validate_packet_seq(packet)
        self.validate_packet_ack(packet)

        if update_ack:
            self.update_ack_num(packet)
        return packet

    def sr(self,
           packet: Packet,
           exp_flags: Optional[str] = None,
           timeout: int = DEFAULT_TIMEOUT,
           update_seq: bool = True,
           update_ack: bool = True) -> Packet:
        """
        Sends a packet and then receives and validates the corresponding response packet.

        :param packet: The packet to send.
        :param exp_flags: Optional list of flags that the response packet should have.
        :param timeout: Optional timeout. Function stops listening for a response packet in case this timeout expires before one arrives.
        :param update_seq: (Optional) Whether the sequence number of the incoming response packet should be updated.
        :param update_ack: (Optional) Whether the acknowledgement number of the incoming response packet should be updated.

        :raise UserException: If the timeout is reached before a packet is received.
        :raise UserException: If the any of the expected flags are missing from the response packet.

        :return: The received response packet.
        """
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

        if "R" in exp_flags:
            self.logger.info("Received package has reset flag. No ACK and SEQ checking.")
            return recv_packet

        self.validate_packet_seq(recv_packet)
        self.validate_packet_ack(recv_packet)

        if update_ack:
            self.update_ack_num(recv_packet)

        return recv_packet

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

    def handle_listen_command(self, parameters: ListenParameters) -> TestCommand:
        """
        Handles a TestCommand of type LISTEN.

        :param parameters: The parameters for the LISTEN command.

        :raise UserException: If a timout occurrs while listening for a packet.
        :raise UserException: If the incoming packet does not have the syn (S) flag.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("Listening for Syn packet")
        self.reset()

        self.sport = parameters.src_port
        packet = self.recv(update_ack=parameters.update_ts_ack)

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
        """
        Handles a TestCommand of type CONNECT.

        :param parameters: The parameters for the CONNECT command.

        :return: A TestCommand of type RESULT.
        """
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
        synack = self.sr(syn, exp_flags="SA", timeout=TIMEOUT)
        self.logger.info("response is syn/ack")

        ack = self.make_packet(flags="A")
        self.send(ack)

        self.logger.info("sent ack")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"],
            description=f"Last Packet received: {synack.__repr__()}"
        ))

    def handle_send_command(self, parameters: SendParameters) -> TestCommand:
        """
        Handles a TestCommand of type SEND.

        :param parameters: The parameters for the SEND command.

        :return: A TestCommand of type RESULT.
        """
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
        """
        Handles a TestCommand of type RECEIVE.

        :param parameters: The parameters for the RECEIVE command.

        :raise UserException: If the timeout from the command parameters is reached before a packet is received.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("Receiving packet with expected flags: %s", parameters.flags)

        recv_packet = self.recv(
            exp_flags=parameters.flags,
            timeout=parameters.timeout,
            update_ack=parameters.update_ts_ack)
        self.logger.info("Sniffing finished")

        if not recv_packet:
            self.logger.warning("no packet received due to timeout")
            raise UserException("Timeout reached")

        TestServer.validate_payload(recv_packet, parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Packet received: {recv_packet.__repr__()}"
        ))

    def handle_send_receive_command(self, parameters: SendReceiveParameters) -> TestCommand:
        """
        Handles a TestCommand of type SENDRECEIVE.

        :param parameters: The parameters for the SENDRECEIVE command.

        :return: A TestCommand of type RESULT.
        """
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
                      update_seq=parameters.send_parameters.update_ts_seq,
                      update_ack=parameters.receive_parameters.update_ts_ack)
        self.logger.info("SR completed")

        TestServer.validate_payload(ret, parameters.receive_parameters.payload)

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["SENDRECEIVE"],
            description=f"Packet received: {ret.__repr__()}"
        ))

    def handle_disconnect_command(self, parameters: DisconnectParameters) -> TestCommand:
        """
        Handles a TestCommand of type DISCONNECT.

        :param parameters: The parameters for the DISCONNECT command.

        :return: A TestCommand of type RESULT.
        """
        self.logger.info("graceful disconnect from client")

        fin = self.make_packet(flags="FA")

        if parameters.half_close:
            resp = self.sr(fin, exp_flags="A", timeout=TIMEOUT)
            self.logger.info("fin packet sent")
        else:
            resp = self.sr(fin, exp_flags="FA", timeout=TIMEOUT)
            self.logger.info("fin packet sent")
            self.logger.info("sending ack")
            ack = self.make_packet(flags="A")
            self.send(ack)
            self.logger.info("ack send")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"],
            description=f"Last Packet received: {resp.__repr__()}"
        ))

    def handle_abort_command(self) -> TestCommand:
        """
        Aborts the current connection.

        :return: A TestCommand of type ABORT.
        """
        self.logger.info("aborting connection")
        self.reset()
        self.logger.info("abort done.")

        return self.make_result(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
