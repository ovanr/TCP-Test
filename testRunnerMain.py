#!/usr/bin/env python3
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from tcpTester import TestCaseLoader, TestRunner, set_up_logging

LOG_DIR_PREFIX = "./test_runner"

if __name__ == "__main__":
    set_up_logging(LOG_DIR_PREFIX)

    test_loader = TestCaseLoader()
    no_of_loaded_test_cases = test_loader.load_test_cases()
    if no_of_loaded_test_cases == 0:
        test_loader.logger.error("No testCases loaded! Please check the tcpTester.testCases module!")
        exit(-1)
    else:
        test_loader.logger.info("Loaded {} test cases!".format(no_of_loaded_test_cases))

    test_runner = TestRunner()
    test_runner.start_runner()

    asyncio.run(test_runner.run())

    test_runner.finish_runner()
