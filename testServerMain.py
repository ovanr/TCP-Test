#!/usr/bin/env python3
# pylint: disable=duplicate-code

import asyncio
import logging
import sys
from typing import cast

import jsonpickle
import websockets

from tcpTester import set_up_logging
from tcpTester.config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from tcpTester.testCommand import TestCommand
from tcpTester.testServer import TestServer

LOG_PREFIX = "./test_server"

if __name__ == "__main__":

    set_up_logging(LOG_PREFIX)

    test_server_logger = logging.getLogger("TestServer")

    async def runner(server: TestServer):
        uri = f"ws://{TEST_RUNNER_IP}:{str(TEST_RUNNER_PORT)}/server"
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
            test_server_logger.error("Connection to the TestRunner failed - asyncio timeout")
            sys.exit(-1)
        except OSError as exc:
            test_server_logger.error("Connection to the TestRunner failed - %s", exc.strerror)
            sys.exit(-1)
        except BaseException as exc:
            test_server_logger.error("Unexpected error: %s", exc)
            sys.exit(-2)


    asyncio.run(
        runner(
            TestServer()
        )
    )
