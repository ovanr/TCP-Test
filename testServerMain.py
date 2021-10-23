#!/usr/bin/env python3

import asyncio
import websockets
import jsonpickle
from testCommand import *
from config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from testServer import TestServer
from typing import cast

async def runner(server: TestServer):
    async with websockets.connect(f"ws://{TEST_RUNNER_IP}:{str(TEST_RUNNER_PORT)}/server") as websocket: #type: ignore
        while True: 
            cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
            result = server.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(
    runner(
        TestServer()
    )
)
