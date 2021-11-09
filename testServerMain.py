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
from tcpTester.testCommand import TestCommand
from tcpTester.testServer import TestServer

LOG_PREFIX = "./test_server"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does no contain logging settings!", "red"))
        exit(-1)
    if "test_runner" not in config:
        print(colored("Config file does no contain test runner settings!", "red"))
        exit(-1)

    try:

        set_up_logging(LOG_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        exit(-1)

    try:
        test_runner_ip = config["test_runner"]["ip"]
        test_runner_port = config["test_runner"]["port"]
    except KeyError as exc:
        print(colored("Config file does no contain test runner ip and port setting!", "red"))
        exit(-1)

    try:
        test_server_iface = config["test_server"]["iface"]
    except KeyError as exc:
        print(colored("Config file does no contain test server iface setting!", "red"))
        exit(-1)

    async def runner(server: TestServer):
        uri = f"ws://{test_runner_ip}:{str(test_runner_port)}/server"
        # pylint: disable=no-member
        try:
            async with websockets.connect(uri) as websocket:  # type: ignore
                while True:
                    recv_data =  jsonpickle.decode(await websocket.recv())
                    cmd = cast(TestCommand,recv_data)
                    server.logger.info("Received command: %s!", cmd)
                    result = server.execute_command(cmd)
                    await websocket.send(jsonpickle.encode(result))
        except asyncio.exceptions.TimeoutError as exc:
            server.logger.error("Connection to the TestRunner failed - asyncio timeout")
            sys.exit(-1)
        except OSError as exc:
            server.logger.error("Connection to the TestRunner failed - %s", exc.strerror)
            sys.exit(-1)
        except BaseException as exc:
            server.logger.error("Unexpected error: %s", exc)
            sys.exit(-2)


    asyncio.run(
        runner(
            TestServer(ts_iface=test_server_iface)
        )
    )
