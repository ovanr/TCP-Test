import logging
from logging import Formatter, StreamHandler, INFO, WARNING, DEBUG
from logging.handlers import RotatingFileHandler


def set_up_logging(log_dir_prefix: str):
    log_file_format = "%(asctime)s - [%(levelname)s] - %(name)s -> %(message)s"
    log_console_format = "[%(levelname)s] - %(name)s -> %(message)s"

    # Main logger
    main_logger = logging.getLogger()
    main_logger.setLevel(DEBUG)

    console_handler = StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(Formatter(log_console_format))

    exp_file_handler = RotatingFileHandler('{}_debug.log'.format(log_dir_prefix),
                                           maxBytes=10 ** 6,
                                           backupCount=5)
    exp_file_handler.setLevel(INFO)
    exp_file_handler.setFormatter(Formatter(log_file_format))

    exp_errors_file_handler = RotatingFileHandler('{}_error.log'.format(log_dir_prefix),
                                                  maxBytes=10 ** 6,
                                                  backupCount=5)
    exp_errors_file_handler.setLevel(WARNING)
    exp_errors_file_handler.setFormatter(Formatter(log_file_format))

    main_logger.addHandler(console_handler)
    main_logger.addHandler(exp_file_handler)
    main_logger.addHandler(exp_errors_file_handler)
