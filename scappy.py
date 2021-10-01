#!/usr/bin/env python3

from sys import argv
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import sr1, send, AsyncSniffer
from random import randint


class TCPClient():
    def __init__(self, dst: str, dport: int):
        self.seq = randint(3000000, 5999999)
        self.ack = 0
        
        self.sport = randint(10000, 30000)
        self.dport = dport
        self._ip = IP(dst=dst) 

        print(f"Host {dst} with src {self.sport} and dst {dport}")

        self.sniffer = AsyncSniffer(iface="tun0",
                                    lfilter=lambda pkt: TCP in pkt and \
                                                        pkt.sport == dport and \
                                                        pkt.dport == self.sport,
                                    prn=self.handlePacket)
        self.snifferAnalyze = True
        self.sniffer.start()

    def handlePacket(self, p):
        if self.snifferAnalyze:
            p.show2()

    def makePacket(self, flags = ""):
        return self._ip / \
               TCP(sport=self.sport, 
                   dport=self.dport,
                   seq=self.seq,
                   ack=self.ack,
                   flags=flags)


    def connect(self):
        syn = self.makePacket(flags="S")
        synack = self.sr(syn)

        ack = self.makePacket(flags="A")
        send(ack)

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
        self.seq += TCPClient.packetLength(packet)

    def sr(self, packet):
        size = TCPClient.packetLength(packet)

        self.snifferAnalyze = False
        ret = sr1(packet)
        self.seq += size
        self.ack = ret.seq + TCPClient.packetLength(ret)
        self.snifferAnalyze = True

        return ret


if __name__ == "__main__":
    dst = argv[1]
    port = argv[2]
    
    c = TCPClient(dst, int(port))
    c.connect()

    while True:
        input()
