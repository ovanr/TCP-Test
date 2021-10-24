#!/usr/bin/env python3

import asyncio
from typing import cast

import jsonpickle
import websockets

from config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from testCommand import TestCommand
from testServer import TestServer

async def runner(server: TestServer):
    uri = f"ws://{TEST_RUNNER_IP}:{str(TEST_RUNNER_PORT)}/server"
    #pylint: disable=no-member
    async with websockets.connect(uri) as websocket: #type: ignore
        while True:
            cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
            result = server.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(
    runner(
        TestServer()
    )
)
