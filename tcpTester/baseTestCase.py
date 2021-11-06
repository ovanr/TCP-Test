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
        self.logger.info("[%s] Preparing setup queues!", self.test_name)
        self.prepare_queues_setup_test()
        self.logger.info("[%s] Finished setup queues!", self.test_name)
        runner.server_queue = self.queue_test_setup_ts
        runner.sut_queue = self.queue_test_setup_sut
        self.logger.info("[%s] Running test setup!", self.test_name)
        if runner.run():
            runner.cleanup()
            self.logger.info("[%s] Finished test setup successfully!", self.test_name)
            return True
        runner.cleanup()
        self.logger.warning("[%s] Failed to run test setup!", self.test_name)
        return False

    def run_test(self, runner: TestRunner):
        """
        Enqueues the commands necessary for the test in the test runner and runs the sequence.

        :param runner: The test runner to use for communication with the test components.

        :return: True on success, False otherwise.
        """
        self.logger.info("[%s] Preparing test queues!", self.test_name)
        self.prepare_queues_test()
        self.logger.info("[%s] Finished test queues!", self.test_name)
        runner.server_queue = self.queue_test_ts
        runner.sut_queue = self.queue_test_sut
        if runner.run():
            runner.cleanup()
            self.logger.warning("[%s] Running test!", self.test_name)
            return True
        runner.cleanup()
        self.logger.warning("[%s] Finished test!", self.test_name)
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
