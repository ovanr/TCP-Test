#!/usr/bin/env python3
import sys

from tcpTester import TestCaseLoader, TestRunner, set_up_logging

LOG_DIR_PREFIX = "./test_runner"

if __name__ == "__main__":
    set_up_logging(LOG_DIR_PREFIX)

    test_loader = TestCaseLoader()
    no_of_loaded_test_cases = test_loader.load_test_cases()
    if no_of_loaded_test_cases == 0:
        test_loader.logger.error("No testCases loaded! Please check the tcpTester.testCases module!")
        sys.exit(-1)
    else:
        test_loader.logger.info("Loaded %s test cases!", no_of_loaded_test_cases)

    test_runner = TestRunner()
    test_runner.start_runner()

    test_case = test_loader.test_cases[0]()

    test_case.setup_test(runner=test_runner)
    test_case.run_test(runner=test_runner)

    # test_runner.finish_runner()
    input()
