import logging
import threading
import time
from typing import List

import asyncio
from threading import Thread

import jsonpickle
import websockets

from tcpTester.testCommand import TestCommand, CommandType
from tcpTester.config import TEST_RUNNER_PORT


class TestRunner:
    _serverQueue = []
    _sutQueue = []

    _serverSendQueue = []
    _sutSendQueue = []

    _serverResponseQueue = []
    _sutResponseQueue = []

    _sutThread: threading.Thread
    _serverThread: threading.Thread

    _serverQueueLock: threading.Lock = threading.Lock()
    _sutQueueLock: threading.Lock = threading.Lock()

    _finish_event = threading.Event()

    _sut_start_event = asyncio.Event()
    _sut_finished_event = threading.Event()

    _ts_start_event = asyncio.Event()
    _ts_finished_event = threading.Event()

    _task = None

    @property
    def logger(self):
        return logging.getLogger("TestRunner")

    @property
    def server_queue(self) -> List[TestCommand]:
        with self._serverQueueLock:
            return self._serverQueue

    @server_queue.setter
    def server_queue(self, queue: List[TestCommand]):
        with self._serverQueueLock:
            self._serverQueue.extend(queue)

    @property
    def sut_queue(self) -> List[TestCommand]:
        with self._sutQueueLock:
            return self._sutQueue

    @sut_queue.setter
    def sut_queue(self, queue: List[TestCommand]):
        with self._sutQueueLock:
            self._sutQueue.extend(queue)

    async def sut_queue_management(self, websocket):
        while not self._finish_event.is_set():
            while len(self._sutSendQueue) != 0:
                cmd = self._sutSendQueue.pop(0)
                await websocket.send(jsonpickle.encode(cmd))
                self._sutResponseQueue.append(jsonpickle.decode(await websocket.recv()))
        self.logger.info("Ending SUT websocket!")

    async def ts_queue_management(self, websocket):
        while not self._finish_event.is_set():
            while len(self._serverSendQueue) != 0:
                cmd = self._serverSendQueue.pop(0)
                await websocket.send(jsonpickle.encode(cmd))
                self._serverResponseQueue.append(jsonpickle.decode(await websocket.recv()))
        self.logger.info("Ending TestServer websocket!")

    def run(self):
        # pylint: disable=too-many-statements

        if self._finish_event.is_set():
            self.logger.warning("Finish flag is set! Not executing run function!")
            return

        sut_last_sync_id = 0
        ts_last_sync_id = 0

        self._sut_start_event.set()
        self._ts_start_event.set()

        def sut_run_manager():

            send_commands_since_sync = 0
            received_responses_since_sync = 0

            while not self._sut_finished_event.is_set() and len(self.sut_queue) > 0:
                next_sut_command: TestCommand = self.sut_queue.pop(0)

                if next_sut_command.command_type == CommandType.WAIT:
                    time.sleep(next_sut_command.command_parameters.seconds)
                    continue

                if next_sut_command.command_type != CommandType.SYNC:
                    self.logger.info("Sending SUT command: %s", next_sut_command)
                    self._sutSendQueue.append(next_sut_command)
                    send_commands_since_sync += 1
                    continue

                if next_sut_command.command_parameters.wait_for_result:
                    while received_responses_since_sync < send_commands_since_sync:
                        while len(self._sutResponseQueue) > 0:
                            response = self._sutResponseQueue.pop(0)
                            if response.command_parameters.status != 0:
                                self.logger.error("Invalid SUT result: %s, test failed!", response)
                                self._finish_event.set()
                                return
                            self.logger.info("Received sut result: %s", response)
                            received_responses_since_sync += 1
                sut_last_sync_id = next_sut_command.command_parameters.sync_id
                while sut_last_sync_id != ts_last_sync_id:
                    time.sleep(0.5)
                send_commands_since_sync = 0
                received_responses_since_sync = 0
            self.logger.info("Finished SUT command enqueuing!")

        def ts_run_manager():


            send_commands_since_sync = 0
            received_responses_since_sync = 0

            while not self._ts_finished_event.is_set() and len(self.server_queue) > 0:
                next_ts_command: TestCommand = self.server_queue.pop(0)

                if next_ts_command.command_type == CommandType.WAIT:
                    time.sleep(next_ts_command.command_parameters.seconds)
                    continue

                if next_ts_command.command_type != CommandType.SYNC:
                    self.logger.info("Sending TestServer command: %s", next_ts_command)
                    self._sutSendQueue.append(next_ts_command)
                    send_commands_since_sync += 1
                    continue

                if next_ts_command.command_parameters.wait_for_result:
                    while received_responses_since_sync < send_commands_since_sync:
                        while len(self._serverResponseQueue) > 0:
                            response = self._serverResponseQueue.pop(0)
                            if response.command_parameters.status != 0:
                                self.logger.error("Invalid TestServer result: %s, test failed!", response)
                                self._finish_event.set()
                                return

                            self.logger.info("Received TestServer result: %s", response)
                            received_responses_since_sync += 1
                ts_last_sync_id = next_ts_command.command_parameters.sync_id
                while ts_last_sync_id != sut_last_sync_id:
                    time.sleep(0.5)
                send_commands_since_sync = 0
                received_responses_since_sync = 0
            self.logger.info("Finished TestServer command enqueuing!")

        sut_thread = threading.Thread(name="SUT queue manager", target=sut_run_manager, args=())
        ts_thread = threading.Thread(name="TestServer queue manager", target=ts_run_manager, args=())

        sut_thread.start()
        ts_thread.start()

        sut_thread.join()
        ts_thread.join()

        self._sut_finished_event.clear()
        self._ts_finished_event.clear()

    def cleanup(self):
        self.logger.debug("Cleanup! This currently does nothing.")

    def start_runner(self):
        # pylint: disable=no-member
        self._sut_start_event.clear()
        self._ts_start_event.clear()

        async def router(websocket, path):
            if path == '/server':
                self.logger.info("TestServer connected!")
                try:
                    await self.ts_queue_management(websocket=websocket)
                except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exc:
                    self.logger.error("TestServer websocket closed: %s!", exc)
                    self._ts_finished_event.set()
                    self._finish_event.set()
            elif path == '/sut':
                self.logger.info("SUT connected!")
                try:
                    await self.sut_queue_management(websocket=websocket)
                except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exc:
                    self.logger.error("SUT websocket closed: %s!", exc)
                    self._sut_finished_event.set()
                    self._finish_event.set()

        async def task_main():
            # pylint: disable=no-member

            async with websockets.serve(router, "", TEST_RUNNER_PORT):  # type: ignore
                while not self._finish_event.is_set():
                    try:
                        await asyncio.wait_for(asyncio.Future(), timeout=0.5)
                    except asyncio.exceptions.TimeoutError:
                        continue
                return 0
        self._task = Thread(target=lambda: asyncio.run(task_main()))
        self._task.start()

    def finish_runner(self):
        self._finish_event.set()
        self._task.join()
