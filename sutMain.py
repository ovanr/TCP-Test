#!/usr/bin/env python3

import asyncio
import websockets
import jsonpickle
from config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from testCommand import *
from sut import SUT
from typing import cast

async def runner(sut: SUT):
    async with websockets.connect(f"ws://{TEST_RUNNER_IP}:{str(TEST_RUNNER_PORT)}/sut") as websocket: #type: ignore
        while True: 
            cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
            result = sut.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(
    runner(
        SUT()
    )
)
