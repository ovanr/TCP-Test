#!/usr/bin/env python3

import asyncio
import websockets
import jsonpickle
from testCommand import *
from testServer import TestServer
from typing import cast

async def runner(server: TestServer):
    async with websockets.connect("ws://192.168.92.112:8765/server") as websocket: #type: ignore
        while True: 
            cmd = cast(TestCommand, jsonpickle.decode(await websocket.recv()))
            result = server.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(
    runner(
        TestServer()
    )
)
