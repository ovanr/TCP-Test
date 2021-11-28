#!/usr/bin/env python3
# pylint: disable=duplicate-code

import sys
import socket

import configparser
import logging
from termcolor import colored

from tcpTester import set_up_logging
from tcpTester.testServer import TestServer
from tcpTester.types import TCPPacket

LOG_PREFIX = "./test_server"

def runner(ts_iface: str, sut_ip: str, mbt_port: int):
    try:
        mbt_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mbt_server.bind(("", mbt_port))
        mbt_server.listen(1)

        (mbt_client, _) = mbt_server.accept()
        mbt_file_client = mbt_client.makefile('wr')

        ts = TestServer(ts_iface=ts_iface, sut_ip=sut_ip, mbt_client=mbt_file_client)

        while True:
            raw = mbt_file_client.readline()
            if not raw.strip():
                continue

            logging.getLogger("TestServer").info("Got input: %s", raw)

            packet = TCPPacket.from_torxakis(raw)
            ts.handle_send_command(packet)

    except OSError as os_err:
        logging.getLogger("TestServer").error("Connection to the wbt failed - OSError: %s", os_err.strerror)
        sys.exit(-1)
    except Exception as err:
        raise err
        logging.getLogger("TestServer").error("Unexpected error: %s", err)
        sys.exit(-2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        sys.exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)
    if "mbt" not in config:
        print(colored("Config file does no contain mbt settings!", "red"))
        sys.exit(-1)
    if "test_server" not in config:
        print(colored("Config file does no contain test server settings!", "red"))
        sys.exit(-1)
    if "sut" not in config:
        print(colored("Config file does no contain sut settings!", "red"))
        sys.exit(-1)

    try:
        set_up_logging(LOG_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)

    try:
        mbt_port = int(config["mbt"]["port"])
    except KeyError as exc:
        print(colored("Config file does no contain mbt port setting!", "red"))
        sys.exit(-1)

    try:
        test_server_iface = config["test_server"]["iface"]
    except KeyError as exc:
        print(colored("Config file does no contain test server iface setting!", "red"))
        sys.exit(-1)

    try:
        sut_ip = config["sut"]["ip"]
    except KeyError as exc:
        print(colored("Config file does no contain sut ipsetting!", "red"))
        sys.exit(-1)

    runner(test_server_iface, sut_ip, mbt_port)
