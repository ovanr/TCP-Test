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
from tcpTester.sut import SUT
from tcpTester.testCommand import TestCommand

LOG_PREFIX = "./sut"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        sys.exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)
    if "sut" not in config:
        print(colored("Config file does no contain sut websocket settings!", "red"))
        sys.exit(-1)

    try:

        set_up_logging(LOG_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)

    try:
        sut_ws_ip = config["sut"]["ip"]
        sut_ws_port = config["sut"]["port"]
    except KeyError as exc:
        print(colored("Config file does no contain test runner ip and port setting!", "red"))
        sys.exit(-1)

    async def mbt_command_execution(websocket):
        sut: SUT = SUT()

        async for message in websocket:
            pass

    async def runner():
        # pylint: disable=no-member
        try:
            async with websockets.serve(mbt_command_execution, f"{sut_ws_ip}", int(sut_ws_port)):
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
