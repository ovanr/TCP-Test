#!/usr/bin/env python3

import asyncio
import websockets
import jsonpickle
from testCommand import *
from sut import SUT
from typing import cast

async def runner(sut: SUT):
    async with websockets.connect("ws://192.168.92.112:8765/sut") as websocket: #type: ignore
        while True: 
            cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
            result = sut.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(
    runner(
        SUT()
    )
)
