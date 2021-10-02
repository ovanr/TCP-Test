#!/usr/bin/env python3

import asyncio
import websockets
import jsonpickle
from testCommand import *
from testServer import TestServer
from typing import Any

async def runner(testServer: TestServer):
    async with websockets.connect("ws://localhost:8765/server") as websocket: #type: ignore
        while True: 
            cmd: Any = jsonpickle.decode(await websocket.recv()) 
            result = testServer.executeCommand(cmd)
            await websocket.send(jsonpickle.encode(result))


asyncio.run(runner(TestServer()))
