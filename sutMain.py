#!/usr/bin/env python3

import asyncio
from typing import cast

import jsonpickle
import websockets

from config import TEST_RUNNER_IP, TEST_RUNNER_PORT
from sut import SUT
from testCommand import TestCommand

async def runner(sut: SUT):
    #pylint: disable=no-member,line-too-long
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
