#!/usr/bin/env python3
# pylint: disable=duplicate-code

import asyncio
import sys
from typing import cast

import configparser
import logging
import websockets
from termcolor import colored

from tcpTester import set_up_logging
from tcpTester.testServer import TestServer

LOG_PREFIX = "./test_server"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        sys.exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)
    if "test_server" not in config:
        print(colored("Config file does no contain test server settings!", "red"))
        sys.exit(-1)

    try:

        set_up_logging(LOG_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)

    try:
        test_server_ws_ip = config["test_server"]["ip"]
        test_server_ws_port = config["test_server"]["port"]
    except KeyError as exc:
        print(colored("Config file does no contain test server ip and port setting!", "red"))
        sys.exit(-1)

    try:
        test_server_iface = config["test_server"]["iface"]
    except KeyError as exc:
        print(colored("Config file does no contain test server iface setting!", "red"))
        sys.exit(-1)

    async def mbt_command_execution(websocket):
        test_server = TestServer(ts_iface=test_server_iface)
        for message in websocket:
            pass

    async def runner(server: TestServer):
        # pylint: disable=no-member
        try:
            async with websockets.serve(mbt_command_execution, f"{test_server_ws_ip}", int(test_server_ws_port)):
                await asyncio.Future()
        except OSError as os_err:
            logging.getLogger("SUTMain").error("Connection to the TestRunner failed - OSError: %s", os_err.strerror)
            sys.exit(-1)
        except Exception as err:
            logging.getLogger("SUTMain").error("Unexpected error: %s", err)
            sys.exit(-2)

    asyncio.run(
        runner()
    )
