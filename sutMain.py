#!/usr/bin/env python3
# pylint: disable=duplicate-code

import asyncio
import sys
from typing import cast

import configparser
import jsonpickle
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
    if "test_runner" not in config:
        print(colored("Config file does no contain test runner settings!", "red"))
        sys.exit(-1)

    try:

        set_up_logging(LOG_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        sys.exit(-1)

    try:
        test_runner_ip = config["test_runner"]["ip"]
        test_runner_port = config["test_runner"]["port"]
    except KeyError as exc:
        print(colored("Config file does no contain test runner ip and port setting!", "red"))
        sys.exit(-1)

    async def runner(sut: SUT):
        uri = f"ws://{test_runner_ip}:{test_runner_port}/sut"
        # pylint: disable=no-member
        try:
            async with websockets.connect(uri) as websocket:  # type: ignore
                while True:
                    recv_data = jsonpickle.decode(await websocket.recv())
                    cmd = cast(TestCommand, recv_data)
                    sut.logger.info("Received command: %s!", cmd)
                    result = sut.execute_command(cmd)
                    await websocket.send(jsonpickle.encode(result))
        except OSError as os_err:
            sut.logger.error("Connection to the TestRunner failed - OSError: %s", os_err.strerror)
            sys.exit(-1)
        except Exception as err:
            sut.logger.error("Unexpected error: %s", err)
            sys.exit(-2)

    asyncio.run(
        runner(
            SUT()
        )
    )
