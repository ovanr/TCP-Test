from abc import ABCMeta
from glob import glob
import importlib
import inspect
from typing import Optional, List

from tcpTester.baseTestCase import BaseTestCase

def find_test_case(filename: str) -> Optional[ABCMeta]:
    try:
        module = importlib.import_module(filename)
        for entities in dir(module):
            obj = getattr(module, entities)

            if inspect.isclass(obj) and \
                not obj is BaseTestCase \
                and issubclass(obj, BaseTestCase):
                return obj
    except ImportError:
        return None

def path_to_module(path: str) -> str:
    return path.replace("/", ".")[:-3]

def load_test_cases(test_cases_path: str) -> List[BaseTestCase]:
    all_test_cases = []

    for test_case_path in glob(test_cases_path + "/*.py"):
        if test_case_path == test_cases_path + '/__init__.py':
            continue
        test_case = find_test_case(path_to_module(test_case_path))
        if not test_case:
            continue
        all_test_cases.append(test_case())

    return all_test_cases

if __name__ == '__main__':
    test_cases = load_test_cases("tcpTester/testCases")
    test_cases.sort(key=lambda t: t.test_id)

    for t in test_cases:
        print(t.test_id, t.test_name)
