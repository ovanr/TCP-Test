import logging
from abc import ABC, abstractmethod
from tcpTester.testRunner import TestRunner


class BaseTestCase(ABC):
    """
    Base class for all test cases.

    New test cases should implement the required abstract methods.
    Then they can be loaded by the test runner for execution.
    """
    queue_test_setup_sut = []
    queue_test_setup_ts = []

    queue_test_sut = []
    queue_test_ts = []

    def __init__(self, ts_ip, sut_ip):
        self._ts_ip = ts_ip
        self._sut_ip = sut_ip

    @property
    def sut_ip(self):
        return self._sut_ip

    @property
    def ts_ip(self):
        return self._ts_ip

    @property
    def logger(self):
        return logging.getLogger(self.test_name)

    @property
    @abstractmethod
    def test_name(self) -> str:
        """
        Read-only property containing the name of the test case.
        This should be human readable and is used for logging outputs.

        :return: Name of the test case
        """

    @property
    @abstractmethod
    def test_id(self) -> int:
        """
        Read-only property containing the unique id of the test case.

        :return: Unique random id for the test case.
        """

    def setup_test(self, runner: TestRunner) -> bool:
        """
        Enqueues the commands necessary for test setup in the test runner and runs the sequence.
        After this method the test setup should be in a stable state from where the actual tests can run.

        :param runner: The test runner to use for communication with the test components.

        :return: True on success, False otherwise.
        """
        self.logger.info("Preparing setup queues!")
        self.prepare_queues_setup_test()
        self.logger.info("Finished setup queues!")
        runner.server_queue = self.queue_test_setup_ts
        runner.sut_queue = self.queue_test_setup_sut
        self.logger.info("Running test setup!")
        if runner.run():
            runner.cleanup()
            self.logger.info("Finished test setup successfully!")
            return True
        runner.cleanup()
        self.logger.warning("Failed to run test setup!")
        return False

    def run_test(self, runner: TestRunner):
        """
        Enqueues the commands necessary for the test in the test runner and runs the sequence.

        :param runner: The test runner to use for communication with the test components.

        :return: True on success, False otherwise.
        """
        self.logger.info("Preparing test queues!")
        self.prepare_queues_test()
        self.logger.info("Finished test queues!")
        runner.server_queue = self.queue_test_ts
        runner.sut_queue = self.queue_test_sut
        if runner.run():
            runner.cleanup()
            self.logger.warning("Running test!")
            return True
        runner.cleanup()
        self.logger.warning("Finished test!")
        return False

    @abstractmethod
    def prepare_queues_setup_test(self):
        """
        Abstract method that should fill the internal queues with the required commands for the test setup.

        :return: Nothing
        """

    @abstractmethod
    def prepare_queues_test(self):
        """
        Abstract method that should fill the internal queues with the required commands for the test.

        :return: Nothing
        """
