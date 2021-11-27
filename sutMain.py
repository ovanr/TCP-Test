#!/usr/bin/env python3
# pylint: disable=duplicate-code

import sys
import socket

import configparser
import logging
from termcolor import colored

from tcpTester import set_up_logging
from tcpTester.sut import SUT
from tcpTester.types import UserCall

LOG_PREFIX = "./sut"

def runner(ts_ip: str, mbt_port: int):
    try:
        mbt_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mbt_server.bind(("", mbt_port))
        mbt_server.listen(1)

        (mbt_client, _) = mbt_server.accept()
        sut = SUT(ts_ip)

        while True:
            raw = mbt_client.recv(1000).decode()
            logging.getLogger("SUTMain").info("Got input: %s", raw)
            user_call = UserCall.from_torxakis(raw)
            resp = sut.handle_user_call(user_call).to_torxakis()
            logging.getLogger("SUTMain").info("Sending response: %s", resp)
            mbt_client.send((resp + "\n").encode())

    except OSError as os_err:
        logging.getLogger("SUTMain").error("Connection to the TestRunner failed - OSError: %s", os_err.strerror)
        sys.exit(-1)
    except Exception as err:
        logging.getLogger("SUTMain").error("Unexpected error: %s", err)
        sys.exit(-2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        sys.exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does not contain logging settings!", "red"))
        sys.exit(-1)
    if "mbt" not in config:
        print(colored("Config file does not contain mbt settings!", "red"))
        sys.exit(-1)
    if "test_server" not in config:
        print(colored("Config file does not contain test server settings!", "red"))
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
        ts_ip = config["test_server"]["ip"]
    except KeyError as exc:
        print(colored("Config file does no contain test server ip setting!", "red"))
        sys.exit(-1)

    runner(ts_ip, mbt_port)
