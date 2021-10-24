#!/usr/bin/env python3

import asyncio
from threading import Thread

import jsonpickle
import websockets

from config import TEST_RUNNER_PORT

serverQueue = []
sutQueue = []


async def thread(queue, websocket):
    while True:
        if len(queue) == 0:
            await asyncio.sleep(1)
            continue

        cmd = queue.pop(0)
        await websocket.send(jsonpickle.encode(cmd))
        print(jsonpickle.decode(await websocket.recv()))


async def router(websocket, path):
    if path == '/server':
        await thread(serverQueue, websocket)
    elif path == '/sut':
        await thread(sutQueue, websocket)


async def main():
    # pylint: disable=no-member
    async with websockets.serve(router, "", TEST_RUNNER_PORT):  # type: ignore
        await asyncio.Future()  # run forever


task = Thread(target=lambda: asyncio.run(main()))
