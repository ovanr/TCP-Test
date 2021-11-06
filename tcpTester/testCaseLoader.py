import inspect
from typing import List, Type

from baseTestCase import BaseTestCase


class TestCaseLoader:
    _test_cases: List[Type[BaseTestCase]]

    @property
    def test_cases(self):
        return self._test_cases

    def load_test_cases(self) -> int:

        test_cases_module = __import__("testCases/__init__", locals(), globals())
        for name, obj in inspect.getmembers(test_cases_module):
            if inspect.isclass(obj) and not obj is BaseTestCase and issubclass(obj, BaseTestCase):
                self._test_cases.append(obj)
        return len(self._test_cases)
