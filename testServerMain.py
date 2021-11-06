#!/usr/bin/env python3

import asyncio
import logging
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
                    cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
                    result = server.execute_command(cmd)
                    await websocket.send(jsonpickle.encode(result))
        except OSError as exc:
            test_server_logger.error("Connection to the TestRunner failed - OSError: {}".format(exc.strerror))
            exit(-1)
        except Exception as exc:
            test_server_logger.error("Unexpected error: {}".format(exc))
            exit(-2)


    asyncio.run(
        runner(
            TestServer()
        )
    )

