#!/usr/bin/env python3
import configparser
import sys

from termcolor import colored

from tcpTester import TestCaseLoader, TestRunner, set_up_logging

LOG_DIR_PREFIX = "./test_runner"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(colored("Please provide one config file via CLI!", "red"))
        exit(-1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    if "logging" not in config:
        print(colored("Config file does no contain logging settings!", "red"))
        exit(-1)
    if "test_runner" not in config:
        print(colored("Config file does no contain test runner settings!", "red"))
        exit(-1)

    if "sut" not in config:
        print(colored("Config file does no contain sut settings!", "red"))
        exit(-1)

    if "test_server" not in config:
        print(colored("Config file does no contain test server settings!", "red"))
        exit(-1)

    try:

        set_up_logging(LOG_DIR_PREFIX,
                       console_level=config["logging"]["console"],
                       enable_file_logging=bool(config["logging"]["file_logging"]))
    except KeyError as exc:
        print(colored("Config file does no contain logging settings!", "red"))
        exit(-1)

    try:
        test_runner_port = config["test_runner"]["port"]
    except KeyError as err:
        print(colored("Config file does no contain test runner ip and port settings!", "red"))
        exit(-1)

    try:
        sut_ip = config["sut"]["ip"]
    except KeyError as err:
        print(colored("Config file does no contain sut ip setting!", "red"))
        exit(-1)

    try:
        ts_ip = config["test_server"]["ip"]
    except KeyError as err:
        print(colored("Config file does no contain ts ip setting!", "red"))
        exit(-1)

    test_loader = TestCaseLoader()
    no_of_loaded_test_cases = test_loader.load_test_cases(ts_ip=ts_ip, sut_ip=sut_ip)
    if no_of_loaded_test_cases == 0:
        test_loader.logger.error("No testCases loaded! Please check the tcpTester.testCases module!")
        exit(-1)
    else:
        test_loader.logger.info("Loaded %s test cases!", no_of_loaded_test_cases)

    test_runner = TestRunner()
    test_runner.start_runner(test_runner_port=int(test_runner_port))

    for test in test_loader.test_cases:
        test.setup_test(runner=test_runner)
        result = test.run_test(runner=test_runner)
        if result:
            print(f"[Test {test.test_id}] {test.test_name}...".ljust(80, "."), colored("PASS", "green"))
        else:
            print(f"[Test {test.test_id}] {test.test_name}...".ljust(80, "."), colored("FAIL", "red"))

    test_runner.finish_runner()