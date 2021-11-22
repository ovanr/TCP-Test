import logging
import threading
import time
from typing import List, cast

import asyncio
from threading import Thread

import jsonpickle
import websockets

from tcpTester.testCommand import TestCommand, CommandType, WaitParameters, SyncParameters, ResultParameters


class TestRunner:
    """
    Implementation of the TestRunner.
    """

    # Queues

    _serverQueue = []
    """Server queue for commands that are to be send."""

    _sutQueue = []
    """SUT queue for commands that are to be send."""

    _server_send_queue = []
    """
    Server queue for commands that should be send immediately.
    Commands put in this queue will be consumed by the async websocket task and send to the TestServer.
    """

    _sut_send_queue = []
    """
    SUT queue for commands that should be send immediately.
    Commands put in this queue will be consumed by the async websocket task and send to the SUT.
    """

    _server_response_queue = []
    """
    Queue that will be populated with responses from the TestServer.
    The population is done by the async task.
    """

    _sut_response_queue = []
    """
    Queue that will be populated with responses from the SUT.
    The population is done by the async task.
    """

    # Locks

    _ts_queue_lock: threading.Lock = threading.Lock()
    """Lock used for queues that are populated or consumed by the TestServer"""

    _sut_queue_lock: threading.Lock = threading.Lock()
    """Lock used for queues that are populated or consumed by the SUT"""

    # Events

    _finish_event = threading.Event()
    """Event that is triggered when the test runner should finish"""

    _sut_connected_event = threading.Event()
    """Event that is triggered when the SUT is connected"""

    _sut_disconnected_event = threading.Event()
    """Event that is triggered when the SUT is disconnected"""

    _ts_started_event = threading.Event()
    """Event that is triggered when the TestServer is connected"""

    _ts_finished_event = threading.Event()
    """Event that is triggered when the TestServer is disconnected"""

    # Threads

    _websocket_async_thread = None
    """Thread that contains the async task running the websockets"""

    @property
    def logger(self):
        """
        Returns the logger used for the TestRunner

        :return: The logger for the TestRunner
        """
        return logging.getLogger("TestRunner")

    @property
    def server_queue(self) -> List[TestCommand]:
        """
        Returns the current queue of commands to be send to the TestServer.

        This method is thread save.
        :return: The current queue. Should only be read.
        """
        with self._ts_queue_lock:
            return self._serverQueue

    @server_queue.setter
    def server_queue(self, queue: List[TestCommand]):
        """
        Adds the queue in the parameter to the queues to be send to the TestServer.

        This method is thread save.
        :param queue: The queue to be added to the TestServer queue.
        :return: None
        """
        with self._ts_queue_lock:
            self._serverQueue.extend(queue)

    @property
    def sut_queue(self) -> List[TestCommand]:
        """
        Returns the current queue of commands to be send to the SUT.

        This method is thread save.
        :return: The current queue. Should only be read.
        """
        with self._sut_queue_lock:
            return self._sutQueue

    @sut_queue.setter
    def sut_queue(self, queue: List[TestCommand]):
        """
        Adds the queue in the parameter to the queues to be send to the SUT.

        This method is thread save.
        :param queue: The queue to be added to the SUT queue.
        :return: None
        """
        with self._sut_queue_lock:
            self._sutQueue.extend(queue)

    async def sut_queue_management(self, websocket):
        """
        Async function to manage the SUT send queue.

        :param websocket: The websocket used for talking to the SUT.

        :return: None
        """
        while not self._finish_event.is_set():
            while len(self._sut_send_queue) != 0:
                cmd = self._sut_send_queue.pop(0)
                await websocket.send(jsonpickle.encode(cmd))
                self._sut_response_queue.append(jsonpickle.decode(await websocket.recv()))
            await asyncio.sleep(0.5)
        self.logger.info("Ending SUT websocket!")

    async def ts_queue_management(self, websocket):
        """
        Async function to manage the TestServer send queue.

        :param websocket: The websocket used for talking to the SUT.

        :return: None
        """
        while not self._finish_event.is_set():
            while len(self._server_send_queue) != 0:
                cmd = self._server_send_queue.pop(0)
                await websocket.send(jsonpickle.encode(cmd))
                self._server_response_queue.append(jsonpickle.decode(await websocket.recv()))
            await asyncio.sleep(0.5)
        self.logger.info("Ending TestServer websocket!")

    def run(self) -> bool:
        """
        Function to run the current sut_queue and ts_queue.
        This involves spawning two threads that will check and execute the commands by sending them to the SUT
        and TestServer.
        :return: True if the queue was executed without any test failures.
        """
        # pylint: disable=too-many-statements

        if self._finish_event.is_set():
            self.logger.warning("Finish flag is set! Not executing run function!")
            return False

        simultaneous_start_event = threading.Event()

        sut_last_sync_id = 0
        ts_last_sync_id = 0

        sut_result_failure = False
        ts_result_failure = False

        def sut_run_manager():
            """
            Function to manage the SUT command queue.
            It will check the commands and enqueue them for sending to the SUT.

            :return: None
            """

            # Variables form the outer scope
            nonlocal sut_last_sync_id
            nonlocal ts_last_sync_id
            nonlocal sut_result_failure
            nonlocal ts_result_failure

            # Wait for the sut and ts to be connected.
            self._sut_connected_event.wait()
            self._ts_started_event.wait()
            time.sleep(1)

            # Logger to use in this function.
            sut_manager_logger = self.logger.getChild("SUTQueueManager")

            # Variables used for managing the sync queue.
            send_commands_since_sync = 0
            received_responses_since_sync = 0

            simultaneous_start_event.wait()

            while not self._sut_disconnected_event.is_set() and len(self.sut_queue) > 0:
                next_sut_command: TestCommand = self.sut_queue.pop(0)

                # WAIT command
                if next_sut_command.command_type == CommandType.WAIT:
                    sut_manager_logger.info("WAIT command!")
                    parameters = cast(WaitParameters, next_sut_command.command_parameters)
                    time.sleep(parameters.seconds)
                    continue

                # Non sync commands
                if next_sut_command.command_type != CommandType.SYNC:
                    sut_manager_logger.info("Sending SUT command: %s", next_sut_command)
                    self._sut_send_queue.append(next_sut_command)
                    send_commands_since_sync += 1
                    continue

                # Sync commands.
                sut_manager_logger.info("SYNC command: %s", next_sut_command)
                parameters = cast(SyncParameters, next_sut_command.command_parameters)

                # Check if we need to wait for the results of previous commands.
                if parameters.wait_for_result:
                    while received_responses_since_sync < send_commands_since_sync:
                        # Process all available responses
                        while len(self._sut_response_queue) > 0:
                            response: TestCommand = self._sut_response_queue.pop(0)
                            if self._finish_event.is_set() or ts_result_failure:
                                return

                            response_parameters = cast(ResultParameters, response.command_parameters)
                            if response_parameters.status != 0:
                                sut_manager_logger.warning("Invalid SUT result: %s, test failed!", response)
                                sut_result_failure = True
                                return
                            sut_manager_logger.info("Received sut result: %s", response)
                            received_responses_since_sync += 1
                    send_commands_since_sync = 0
                    received_responses_since_sync = 0
                sut_last_sync_id = parameters.sync_id
                while sut_last_sync_id > ts_last_sync_id:
                    if self._finish_event.is_set() or ts_result_failure:
                        return

                    time.sleep(0.5)
            sut_manager_logger.info("Finished SUT command enqueuing!")
            return

        def ts_run_manager():
            """
            Function to manage the TestServer command queue.
            It will check the commands and enqueue them for sending to the SUT.

            :return: None
            """

            # Variables form the outer scope
            nonlocal sut_last_sync_id
            nonlocal ts_last_sync_id
            nonlocal ts_result_failure
            nonlocal sut_result_failure

            # Wait for the sut and ts to be connected.
            self._ts_started_event.wait()
            self._sut_connected_event.wait()
            time.sleep(1)

            # Logger to use in this function.
            ts_manager_logger = self.logger.getChild("TSQueueManager")

            # Variables used for managing the sync queue.
            send_commands_since_sync = 0
            received_responses_since_sync = 0

            simultaneous_start_event.wait()

            while not self._ts_finished_event.is_set() and len(self.server_queue) > 0:
                next_ts_command: TestCommand = self.server_queue.pop(0)

                # WAIT commands
                if next_ts_command.command_type == CommandType.WAIT:
                    ts_manager_logger.info("WAIT command!")
                    parameters = cast(WaitParameters, next_ts_command.command_parameters)
                    time.sleep(parameters.seconds)
                    continue

                # Non SYNC commands.
                if next_ts_command.command_type != CommandType.SYNC:
                    ts_manager_logger.info("Sending TestServer command: %s", next_ts_command)
                    self._server_send_queue.append(next_ts_command)
                    send_commands_since_sync += 1
                    continue

                ts_manager_logger.info("SYNC command: %s", next_ts_command)
                parameters = cast(SyncParameters, next_ts_command.command_parameters)

                if parameters.wait_for_result:
                    while received_responses_since_sync < send_commands_since_sync:
                        while len(self._server_response_queue) > 0:
                            response: TestCommand = self._server_response_queue.pop(0)
                            if self._finish_event.is_set() or sut_result_failure:
                                return

                            response_parameters = cast(ResultParameters, response.command_parameters)
                            if response_parameters.status != 0:
                                ts_manager_logger.warning("Invalid TestServer result: %s, test failed!", response)
                                ts_result_failure = True
                                return

                            ts_manager_logger.info("Received TestServer result: %s", response)
                            received_responses_since_sync += 1
                    send_commands_since_sync = 0
                    received_responses_since_sync = 0
                ts_last_sync_id = parameters.sync_id
                while ts_last_sync_id > sut_last_sync_id:
                    if self._finish_event.is_set() or sut_result_failure:
                        return
                    time.sleep(0.5)

            ts_manager_logger.info("Finished TestServer command enqueuing!")
            return

        sut_thread = threading.Thread(name="SUT queue manager", target=sut_run_manager, args=())
        ts_thread = threading.Thread(name="TestServer queue manager", target=ts_run_manager, args=())

        ts_thread.start()
        sut_thread.start()

        time.sleep(1)
        simultaneous_start_event.set()

        ts_thread.join()
        sut_thread.join()

        return not sut_result_failure and not ts_result_failure

    def cleanup(self):
        self.logger.debug("Cleanup started!")

        # self._sut_send_queue.append(TestCommand(
        #     test_number=-2,
        #     command_type=CommandType["ABORT"]
        # ))
        # self._server_send_queue.append(TestCommand(
        #     test_number=-2,
        #     command_type=CommandType["ABORT"]
        # ))
        # time.sleep(5)

        self.logger.debug("Cleanup finished!")

    def start_runner(self, test_runner_port: int):
        # pylint: disable=no-member
        self._sut_connected_event.clear()
        self._ts_started_event.clear()

        async def router(websocket, path):
            if path == '/server':
                self.logger.info("TestServer connected!")
                self._ts_started_event.set()
                try:
                    await self.ts_queue_management(websocket=websocket)
                except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exc: # type: ignore
                    self.logger.error("TestServer websocket closed: %s!", exc)
                    self._ts_finished_event.set()
                    self._finish_event.set()
            elif path == '/sut':
                self.logger.info("SUT connected!")
                self._sut_connected_event.set()
                try:
                    await self.sut_queue_management(websocket=websocket)
                except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exc: # type: ignore
                    self.logger.error("SUT websocket closed: %s!", exc)
                    self._sut_disconnected_event.set()
                    self._finish_event.set()

        async def task_main():
            # pylint: disable=no-member

            async with websockets.serve(router, "", test_runner_port, ping_timeout=None):  # type: ignore
                while not self._finish_event.is_set():
                    await asyncio.sleep(0.5)
                return 0

        self._websocket_async_thread = Thread(target=lambda: asyncio.run(task_main()))
        self._websocket_async_thread.start()

    def finish_runner(self):
        self._finish_event.set()
        if self._websocket_async_thread:
            self._websocket_async_thread.join()
