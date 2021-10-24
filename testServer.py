#!/usr/bin/env python3

import logging
from random import randint
from typing import Optional, cast

from scapy.layers.inet import IP, TCP
from scapy.packet import Packet, Raw
from scapy.sendrecv import send, sniff

from baseRunner import BaseRunner
from config import TEST_SERVER_INTERFACE
#pylint: disable=duplicate-code
from testCommand import (
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
TIMEOUT=20

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

    def updateSequenceNum(self, packet: Packet):
        self.seq += TestServer.packetLength(packet)

    def updateAckNum(self, packet: Packet):
        packetAck = packet.seq + TestServer.packetLength(packet)
        if packetAck > self.ack:
            self.ack = packetAck
        else:
            logging.info("Received packet with duplicate Ack %s", packetAck)

    @staticmethod
    def packetLength(packet: Packet):
        size = 0
        if Raw in packet:
            size = len(packet[Raw].load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    @staticmethod
    def missingFlags(packet: Packet, expFlags: Optional[str]):
        if not expFlags:
            return []

        missingFlags = filter(lambda f: f not in packet.sprintf("%TCP.flags%"), expFlags)

        return list(missingFlags)

    @staticmethod
    def validatePayload(packet: Packet, expPayload: Optional[bytes] = None):
        payload = packet[Raw].load if Raw in packet else b''
        if (expPayload and expPayload != payload):
            logging.warning("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

    def _sniff(self, numPackets: int, expFlags: Optional[str], timeout: Optional[int] = None):
        queue = []
        logging.info("Starting sniffing..")

        pktFilter = lambda pkt: TCP in pkt and \
                                pkt.dport == self.sport and \
                                len(TestServer.missingFlags(pkt, expFlags)) == 0
        sniff(count=numPackets,
              store=False,
              iface=TEST_SERVER_INTERFACE,
              lfilter=pktFilter,
              prn=queue.append,
              timeout=timeout)

        return queue

    def send(self, packet: Packet):
        send(packet)
        self.updateSequenceNum(packet)

    def recv(self, expFlags: Optional[str] = None, timeout: Optional[int] = None):
        packets = self._sniff(1, expFlags=expFlags, timeout=timeout)
        if not packets:
            return None
        [packet] = packets
        logging.info("Calculated packet length as %s", TestServer.packetLength(packet))
        self.updateAckNum(packet)
        return packet


    def sr(self, packet: Packet, expFlags: Optional[str] = None):
        self.send(packet)
        logging.info('first packet sent')
        ret = self.recv(expFlags=expFlags, timeout=TIMEOUT)
        logging.info('packet received')

        if not ret:
            logging.info("timeout reached, could not detect packet with flags %s", expFlags)
            raise UserException("Got no response to packet")

        return ret

    def makePacket(self,
                   payload: Optional[bytes] = None,
                   seq: Optional[int] = None,
                   ack: Optional[int] = None,
                   flags: Optional[str] = None,
                   window: Optional[int] = None,
                   chksum: Optional[int] = None,
                   urgentPointer: Optional[int] = None):

        pkt = self.ip / TCP(sport=self.sport,
                            dport=self.dport,
                            seq=(self.seq if seq is None else seq),
                            ack=(self.ack if ack is None else ack),
                            flags=(flags or ""),
                            window=(8192 if window is None else window),
                            chksum=chksum,
                            urgptr=(urgentPointer or 0))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handleListenCommand(self, parameters: ListenParameters):
        logging.info("Listening for Syn packet")
        self.reset()

        self.sport = parameters.srcPort
        packet = cast(Packet, self.recv())

        logging.info("Packet received from %s", packet[IP].src)
        self.ip = IP(dst=packet[IP].src)

        flags = packet.sprintf("%TCP.flags%")
        if "S" not in flags:
            raise UserException(f"Invalid flags received: expected 'S' got {flags}")

        self.dport = packet.sport

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["LISTEN"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handleConnectCommand(self, parameters: ConnectParameters):
        logging.info("connecting to %s", parameters.dstPort)
        self.reset()

        self.ip = IP(dst=parameters.destination)
        self.sport = parameters.srcPort
        self.dport = parameters.dstPort

        syn = self.makePacket(flags="S")

        if not parameters.fullHandshake:
            self.send(syn)
            logging.info("single syn sent")
            return self.makeResult(ResultParameters(
                status=0,
                operation=CommandType["CONNECT"]
            ))

        logging.info("sending first syn")
        synack = self.sr(syn, expFlags="SA")
        logging.info("response is syn/ack")

        ack = self.makePacket(flags="A")
        send(ack)

        logging.info("sent ack")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"],
            description=f"Last Packet received: {synack.__repr__()}"
        ))

    def handleSendCommand(self, parameters: SendParameters):
        logging.info("Sending packet with flags: %s", parameters.flags)

        pkt = self.makePacket(
            payload=parameters.payload,
            seq=parameters.sequenceNumber,
            ack=parameters.acknowledgementNumber,
            flags=parameters.flags,
            window=parameters.windowSize,
            chksum=parameters.checksum,
            urgentPointer=parameters.urgentPointer,
        )

        self.send(pkt)
        logging.info("Packet was sent")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
            description=f"Sent this payload: {parameters.payload}"
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        logging.info("Receiving packet with expected flags: %s", parameters.flags)

        packet = self.recv(expFlags=parameters.flags, timeout=parameters.timeout)
        logging.info("Sniffing finished")

        if not packet:
            logging.warning("no packet received due to timeout")
            raise UserException("Timeout reached")

        TestServer.validatePayload(packet, parameters.payload)

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handleSendReceiveCommand(self, parameters: SendReceiveParameters):
        sendParams = parameters.sendParameters
        logging.info("Sending packet with flags: %s", sendParams.flags)

        pkt = self.makePacket(
            payload=sendParams.payload,
            seq=sendParams.sequenceNumber,
            ack=sendParams.acknowledgementNumber,
            flags=sendParams.flags,
            window=sendParams.windowSize,
            chksum=sendParams.checksum,
            urgentPointer=sendParams.urgentPointer,
        )
        logging.info("Created packet")

        ret = self.sr(pkt, expFlags=parameters.receiveParameters.flags)
        logging.info("SR completed")

        TestServer.validatePayload(ret, parameters.receiveParameters.payload)

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SENDRECEIVE"],
            description=f"Packet received: {ret.__repr__()}"
        ))

    def handleDisconnectCommand(self):
        logging.info("graceful disconnect from client")

        fin = self.makePacket(flags="FA")
        finack = self.sr(fin)
        logging.info("send fin packet")

        finackFlags = finack.sprint("%TCP.flags%")
        if "F" not in finackFlags or "A" not in finackFlags:
            logging.warning("response did not contain FA")
            raise UserException(f"Invalid flags received: expected 'FA' got {finackFlags}")

        logging.info("sending ack")
        ack = self.makePacket(flags="A")
        send(ack)
        logging.info("ack send")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"],
            description=f"Last Packet received: {finack.__repr__()}"
        ))

    def handleAbortCommand(self):
        logging.info("aborting connection")
        self.reset()
        logging.info("abort done.")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
