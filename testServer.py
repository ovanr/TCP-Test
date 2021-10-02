#!/usr/bin/env python3

from scapy.packet import Raw
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import sr1, send, sniff
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

    @staticmethod
    def packetLength(packet):
        size = 0
        if hasattr(packet, "load"):
            size = len(packet.load)
        for f in ["F", "S"]:
            if f in packet.sprintf("%TCP.flags%"):
                size += 1
        return size

    def send(self, packet):
        send(packet)
        self.seq += TestServer.packetLength(packet)

    def sr(self, packet):
        size = TestServer.packetLength(packet)

        ret = sr1(packet, timeout=TIMEOUT)

        if not ret:
            logging.info("timeout reached")
            raise UserException("Got no response to packet")

        self.seq += size
        self.ack = ret.seq + TestServer.packetLength(ret)

        return ret

    def reset(self):
        self.seq = randint(3000000, 5999999)
        self.ack = 0

    def makePacket(self,
                   seq: Optional[int] = None,
                   ack: Optional[int] = None,
                   flags: Optional[str] = None,
                   window: Optional[int] = None,
                   chksum: Optional[int] = None,
                   urgentPointer: Optional[int] = None):

        return self._ip / TCP(sport=self.sport, 
                              dport=self.dport,
                              seq=(seq if ack != None else self.seq),
                              ack=(ack if ack != None else self.ack),
                              flags=(flags or ""),
                              window=(window if window != None else 8192),
                              chksum=chksum,
                              urgptr=(urgentPointer or 0))

    def handleConnectCommand(self, parameters: ConnectParameters):
        logging.info(f"connecting to {parameters.destination}")
        self.reset()
        
        self.sport = parameters.srcPort
        self.dport = parameters.dstPort
        self._ip = IP(dst=parameters.destination) 

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
        ))

    def handleSendCommand(self, parameters: SendParameters):
        logging.info(f"Sending packet with flags: {parameters.flags}")

        pkt = self.makePacket(
            seq=parameters.sequenceNumber,
            ack=parameters.acknowledgementNumber,
            flags=parameters.flags,
            window=parameters.windowSize,
            chksum=parameters.checksum,
            urgentPointer=parameters.urgentPointer
        )

        if parameters.bytes:
            pkt = pkt / Raw(load=parameters.bytes)

        self.send(pkt)
        logging.info("Packet was sent")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        logging.info(f"Receiving packet with expected flags: {parameters.flags}")

        queue = []
        sniff(count=1,
              store=True,
              lfilter=lambda pkt: TCP in pkt and \
                                  pkt.sport == self.dport and \
                                  pkt.dport == self.sport,
              prn=lambda p: queue.append(p),
              timeout=parameters.timeout)

        logging.info("Sniffing finished")

        if len(queue) == 0:
            logging.warn("no packet received due to timeout")
            raise UserException("Timeout reached")

        [packet] = queue
        payload = packet if hasattr(packet, 'load') else b''

        if (parameters.bytes and parameters.bytes != payload):
            logging.warn("packet contained incorrect bytes")
            raise UserException(f"Invalid data received: '{payload}'")

        if (parameters.flags):
            missingFlags = ''.join(
                filter(lambda f: f not in packet.sprintf("%TCP.flags%"),
                       parameters.flags.split(''))
            )
            if missingFlags:
                logging.warn("packet contained incorrect flags")
                raise UserException(f"Flags are missing: {missingFlags}")

        logging.info("received packet passed validations")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
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
        ))

    def handleAbortCommand(self):
        logging.info(f"aborting connection")
        self.reset()
        logging.info(f"abort done.")

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))
