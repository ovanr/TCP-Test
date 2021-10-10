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
        if hasattr(packet, "load"):
            size = len(packet.load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    @staticmethod
    def validatePacket(packet, 
                       expPayload: Optional[bytes] = None, 
                       expFlags: Optional[str] = None):

        payload = packet if hasattr(packet, 'load') else b''

        if (expPayload and expPayload != payload):
            logging.warn("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

        if expFlags:
            missingFlags = ''.join(
                filter(lambda f: f not in packet.sprintf("%TCP.flags%"),
                       expFlags.split(''))
            )
            if missingFlags:
                logging.warn("packet contained incorrect flags")
                raise UserException(f"Flags are missing: {missingFlags}")

        logging.info("received packet passed validations")

    def _sniff(self, numPackets: int, timeout: Optional[int] = None):
        queue = []
        logging.info("Starting sniffing..")
        sniff(count=numPackets,
              store=False,
              lfilter=lambda pkt: TCP in pkt and \
                                  pkt.dport == self.sport,
              prn=lambda p: queue.append(p),
              timeout=timeout)

        return queue

    def send(self, packet):
        send(packet)
        self.seq += TestServer.packetLength(packet)

    def recv(self, timeout: Optional[int] = None):
        packets = self._sniff(1, timeout)
        if not packets:
            return None
        [packet] = packets
        self.ack = packet.seq + TestServer.packetLength(packet)
        return packet

    def sr(self, packet):
        self.send(packet)
        logging.info('first packet sent')
        ret = self.recv(TIMEOUT)
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
        self._ip = IP(dst=packet.src)
        logging.info(f"Packet received")

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

        logging.info("sending first syn")
        synack = self.sr(syn)
        logging.info("received response")

        synackFlags = synack.sprintf("%TCP.flags%")
        if "S" not in synackFlags or "A" not in synackFlags:
            raise UserException(f"Invalid flags received: expected 'SA' got {synackFlags}")

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

        packet = self.recv(timeout=parameters.timeout)
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

        ret = self.sr(pkt)
        logging.info("SR completed")

        # TestServer.validatePacket(ret, 
        #                           parameters.receiveParameters.bytes, 
        #                           parameters.receiveParameters.flags)
        
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
