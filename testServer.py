#!/usr/bin/env python3

from scapy.packet import Raw
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import send, sniff
from random import randint
from baseRunner import BaseRunner
import logging

from testCommand import *

# timeout for the sr1 command (in seconds)
TIMEOUT=20

class TestServer(BaseRunner):
    def __init__(self):
        self.testNumber = -1
        logging.getLogger("").setLevel(logging.INFO)
        logging.info("test server started")

    def reset(self):
        self.seq = randint(3000000, 5999999)
        self.ack = 0
        self.sport = 0
        self.dport = 0

    @staticmethod
    def packetLength(packet):
        size = 0
        if Raw in packet:
            size = len(packet[Raw].load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    @staticmethod
    def validateFlags(packet, expFlags):
        if not expFlags:
            return True

        missingFlags = ''.join(
            filter(lambda f: f not in packet.sprintf("%TCP.flags%"), expFlags)
        )
        if missingFlags:
            return False

        return True

    @staticmethod
    def validatePacket(packet, 
                       expPayload: Optional[bytes] = None, 
                       expFlags: Optional[str] = None):

        payload = packet[Raw].load if Raw in packet else b''

        if (expPayload and expPayload != payload):
            logging.warn("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

        if TestServer.validateFlags(packet, expFlags):
            logging.warn("packet contained incorrect flags")
            raise UserException(f"Flags are missing")

        logging.info("received packet passed validations")

    def _sniff(self, numPackets: int, expFlags: Optional[str], timeout: Optional[int] = None):
        queue = []
        logging.info("Starting sniffing..")
        
        pktFilter = lambda pkt: TCP in pkt and \
                                pkt.dport == self.sport and \
                                TestServer.validateFlags(pkt, expFlags)
        sniff(count=numPackets,
              store=False,
              iface="enp4s0",
              lfilter=pktFilter,
              prn=lambda p: queue.append(p),
              timeout=timeout)

        return queue

    def send(self, packet):
        send(packet)
        self.seq += TestServer.packetLength(packet)

    def recv(self, expFlags: Optional[str] = None, timeout: Optional[int] = None):
        packets = self._sniff(1, expFlags=expFlags, timeout=timeout)
        if not packets:
            return None
        [packet] = packets
        logging.info(f"Calculated packet length as {TestServer.packetLength(packet)}")
        self.ack = packet.seq + TestServer.packetLength(packet)
        return packet

    def sr(self, packet, expFlags: Optional[str] = None):
        self.send(packet)
        logging.info('first packet sent')
        ret = self.recv(expFlags=expFlags, timeout=TIMEOUT)
        logging.info('packet received')

        if not ret:
            logging.info("timeout reached")
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

        pkt = self._ip / TCP(sport=self.sport, 
                             dport=self.dport,
                             seq=(seq if seq != None else self.seq),
                             ack=(ack if ack != None else self.ack),
                             flags=(flags or ""),
                             window=(window if window != None else 8192),
                             chksum=chksum,
                             urgptr=(urgentPointer or 0))
        if payload:
            pkt = pkt / Raw(load=payload)

        return pkt

    def handleListenCommand(self, parameters: ListenParameters):
        logging.info(f"Listening for Syn packet")
        self.reset()

        self.sport = parameters.srcPort
        packet = self.recv()

        logging.info(f"Packet received from {packet[IP].src}")
        self._ip = IP(dst=packet[IP].src)

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
        logging.info(f"connecting to {parameters.dstPort}")
        self.reset()
        
        self._ip = IP(dst=parameters.destination)
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
        logging.info(f"Sending packet with flags: {parameters.flags}")

        pkt = self.makePacket(
            payload=parameters.bytes,
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
            description=f"Sent this payload: {parameters.bytes}"
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        logging.info(f"Receiving packet with expected flags: {parameters.flags}")

        packet = self.recv(expFlags=parameters.flags, timeout=parameters.timeout)
        logging.info("Sniffing finished")

        if not packet:
            logging.warn("no packet received due to timeout")
            raise UserException("Timeout reached")

        TestServer.validatePacket(packet, parameters.bytes, parameters.flags)

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
            description=f"Packet received: {packet.__repr__()}"
        ))

    def handleSendReceiveCommand(self, parameters: SendReceiveParameters):
        sendParams = parameters.sendParameters
        logging.info(f"Sending packet with flags: {sendParams.flags}")

        pkt = self.makePacket(
            payload=sendParams.bytes,
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

        TestServer.validatePacket(ret, 
                                  parameters.receiveParameters.bytes, 
                                  parameters.receiveParameters.flags)
        
        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SENDRECEIVE"],
            description=f"Packet received: {ret.__repr__()}"
        ))
        
    def handleDisconnectCommand(self):
        logging.info(f"graceful disconnect from client")

        fin = self.makePacket(flags="FA")
        finack = self.sr(fin)
        logging.info("send fin packet")

        finackFlags = finack.sprint("%TCP.flags%")
        if "F" not in finackFlags or "A" not in finackFlags:
            logging.warn("response did not contain FA")
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
        logging.info(f"aborting connection")
        self.reset()
        logging.info(f"abort done.")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
