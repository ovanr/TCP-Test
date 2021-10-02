#!/usr/bin/env python3

from re import error
from scapy.packet import Raw
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import sr1, send, sniff
from random import randint
from baseRunner import BaseRunner

from testCommand import *

class TestServer(BaseRunner):
    def __init__(self):
        self.testNumber = -1

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

        ret = sr1(packet)
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
        return self._ip / \
               TCP(sport=self.sport, 
                   dport=self.dport,
                   seq=(seq or self.seq),
                   ack=(ack or self.ack),
                   flags=(flags or ""),
                   window=(window or 8192),
                   chksum=chksum,
                   urgptr=(urgentPointer or 0))

    def handleConnectCommand(self, parameters: ConnectParameters):
        self.reset()
        
        self.sport = parameters.srcPort
        self.dport = parameters.dstPort
        self._ip = IP(dst=parameters.destination) 

        try:
            syn = self.makePacket(flags="S")
            synack = self.sr(syn)

            synackFlags = synack.sprint("%TCP.flags%")
            if "S" not in synackFlags or "A" not in synackFlags:
                return self.makeResult(ResultParameters(
                    status=1,
                    operation=CommandType["CONNECT"],
                    errorMessage=f"Invalid flags received: expected 'SA' got {synackFlags}"
                ))

            ack = self.makePacket(flags="A")
            send(ack)

        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["CONNECT"],
                errorMessage=str(e)
            ))

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["CONNECT"],
        ))

    def handleSendCommand(self, parameters: SendParameters):
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

        try:
            self.send(pkt)
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["SEND"],
                errorMessage=str(e)
            ))

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["SEND"],
        ))

    def handleReceiveCommand(self, parameters: ReceiveParameters):
        queue = []
        sniff(count=1,
              store=True,
              lfilter=lambda pkt: TCP in pkt and \
                                  pkt.sport == self.dport and \
                                  pkt.dport == self.sport,
              prn=lambda p: queue.append(p),
              timeout=parameters.timeout)

        if len(queue) == 0:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["RECEIVE"],
                errorMessage="Timeout reached."
            ))

        [packet] = queue
        payload = packet if hasattr(packet, 'load') else b''

        if (parameters.bytes and parameters.bytes != payload):
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["RECEIVE"],
                errorMessage=f"Invalid data received: '{payload}'"
            ))

        if (parameters.flags):
            missingFlags = ''.join(
                filter(lambda f: f not in packet.sprintf("%TCP.flags%"),
                       parameters.flags.split(''))
            )
            if missingFlags:
                return self.makeResult(ResultParameters(
                    status=1,
                    operation=CommandType["RECEIVE"],
                    errorMessage=f"Flags are missing: {missingFlags}"
                ))


        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["RECEIVE"],
        ))

    def handleDisconnectCommand(self):
        try:
            fin = self.makePacket(flags="F")
            finack = self.sr(fin)
            finackFlags = finack.sprint("%TCP.flags%")
            if "F" not in finackFlags or "A" not in finackFlags:
                return self.makeResult(ResultParameters(
                    status=1,
                    operation=CommandType["DISCONNECT"],
                    errorMessage=f"Invalid flags received: expected 'FA' got {finackFlags}"
                ))

            ack = self.makePacket(flags="A")
            send(ack)

        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["DISCONNECT"],
                errorMessage=str(e)
            ))

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["DISCONNECT"],
        ))

    def handleAbortCommand(self):
        try:
            self.reset()
        except Exception as e:
            return self.makeResult(ResultParameters(
                status=1,
                operation=CommandType["ABORT"],
                errorMessage=str(e)
            ))

        return self.makeResult(ResultParameters(
            status=0,
            operation=CommandType["ABORT"],
        ))


