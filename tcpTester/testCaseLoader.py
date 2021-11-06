import importlib
import inspect
import logging
from typing import List, Type

from .baseTestCase import BaseTestCase


class TestCaseLoader:
    _test_cases: List[Type[BaseTestCase]] = []
    _logger: logging.Logger = logging.getLogger("TestCaseLoader")

    @property
    def logger(self):
        return self._logger

    @property
    def test_cases(self):
        return self._test_cases

    def load_test_cases(self) -> int:
        try:
            test_cases_module = importlib.import_module(".testCases", package="tcpTester")
        except ImportError as exc:
            self.logger.error("Could not load tcpTester.testCases module: %s", exc.msg)
            self._test_cases = []
            return len(self._test_cases)
        try:
            for name, obj in inspect.getmembers(test_cases_module):
                if inspect.isclass(obj) and (obj is not BaseTestCase) and (issubclass(obj, BaseTestCase)):
                    self.logger.debug("Loaded testCase: %s!", name)
                    self._test_cases.append(obj)
        except ImportError as exc:
            self.logger.error("Could not load testCase: %s! Error message: %s", exc.path, exc.msg)
            self._test_cases = []
        return len(self._test_cases)
