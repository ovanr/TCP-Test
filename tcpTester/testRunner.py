import threading
from typing import List

import asyncio
from threading import Thread
from logging import debug

import jsonpickle
import websockets

from tcpTester.testCommand import TestCommand
from tcpTester.config import TEST_RUNNER_PORT


class TestRunner:
    _serverQueue = []
    _sutQueue = []

    _sutThread: threading.Thread
    _serverThread: threading.Thread

    _serverQueueLock: threading.Lock = threading.Lock()
    _sutQueueLock: threading.Lock = threading.Lock()

    _finish_event = asyncio.Event()

    _sut_start_event = asyncio.Event()
    _sut_finished_event = asyncio.Event()

    _ts_start_event = asyncio.Event()
    _ts_finished_event = asyncio.Event()

    _task = None

    @property
    def server_queue(self) -> List[TestCommand]:
        with self._serverQueueLock:
            return self._serverQueue

    @server_queue.setter
    def server_queue(self, queue: List[TestCommand]):
        with self._serverQueueLock:
            self._serverQueue.append(queue)

    @property
    def sut_queue(self) -> List[TestCommand]:
        with self._sutQueueLock:
            return self._sutQueue

    @sut_queue.setter
    def sut_queue(self, queue: List[TestCommand]):
        with self._sutQueueLock:
            self._sutQueue.append(queue)

    @staticmethod
    async def connected_element_thread(queue, websocket, start_event: asyncio.Event, finished_event: asyncio.Event):
        while True:
            await start_event.wait()
            start_event.clear()
            while len(queue) != 0:
                cmd = queue.pop(0)
                await websocket.send(jsonpickle.encode(cmd))
                print(jsonpickle.decode(await websocket.recv()))
            finished_event.set()

    async def run(self):
        self._sut_start_event.set()
        self._ts_start_event.set()

        await self._sut_finished_event.wait()
        self._sut_finished_event.clear()

        await self._ts_finished_event.wait()
        self._ts_finished_event.clear()

    def cleanup(self):
        debug("Cleanup! This currently does nothing.")
        pass

    def start_runner(self):
        async def router(websocket, path):
            if path == '/server':
                await self.connected_element_thread(
                    self._serverQueue,
                    websocket,
                    self._ts_start_event,
                    self._ts_finished_event)
            elif path == '/sut':
                await self.connected_element_thread(
                    self._sutQueue,
                    websocket,
                    self._sut_start_event,
                    self._sut_finished_event
                )

        async def task_main():
            # pylint: disable=no-member
            async with websockets.serve(router, "", TEST_RUNNER_PORT):  # type: ignore
                await self._finish_event.wait()  # run forever

        self._task = Thread(target=lambda: asyncio.run(task_main()))
        self._task.start()

    def finish_runner(self):
        self._finish_event.set()
        self._task.join()

