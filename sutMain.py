#!/usr/bin/env python3

import asyncio
import logging
from typing import cast

import jsonpickle
import websockets

from tcpTester import set_up_logging
from tcpTester.config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from tcpTester.sut import SUT
from tcpTester.testCommand import TestCommand

LOG_PREFIX = "./sut"


if __name__ == "__main__":

    set_up_logging(LOG_PREFIX)

    async def runner(sut: SUT):
        uri = f"ws://{TEST_RUNNER_IP}:{str(TEST_RUNNER_PORT)}/sut"
        # pylint: disable=no-member
        try:
            async with websockets.connect(uri) as websocket:  # type: ignore
                while True:
                    cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
                    result = sut.execute_command(cmd)
                    await websocket.send(jsonpickle.encode(result))
        except OSError as exc:
            sut.logger.error("Connection to the TestRunner failed - OSError: {}".format(exc.strerror))
            exit(-1)
        except Exception as exc:
            sut.logger.error("Unexpected error: {}".format(exc))
            exit(-2)


    asyncio.run(
        runner(
            SUT()
        )
    )
