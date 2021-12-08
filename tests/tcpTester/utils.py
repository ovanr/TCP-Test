import logging
from datetime import datetime
from logging import Formatter, StreamHandler, INFO, WARNING
from logging.handlers import RotatingFileHandler


def set_up_logging(log_dir_prefix: str, console_level, enable_file_logging: bool):
    log_file_format = "%(asctime)s - [%(levelname)s] - %(name)s -> %(message)s"
    log_console_format = "[%(levelname)s] - %(name)s -> %(message)s"

    # Main logger
    main_logger = logging.getLogger()
    main_logger.setLevel(INFO)

    console_handler = StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(Formatter(log_console_format))
    main_logger.addHandler(console_handler)

    if enable_file_logging:
        log_file_prefix = datetime.now().strftime(f'{log_dir_prefix}_%H:%M:%S_%d-%m-%Y')

        exp_file_handler = RotatingFileHandler(f'{log_file_prefix}_debug.log',
                                               maxBytes=10 ** 6,
                                               backupCount=5)
        exp_file_handler.setLevel(INFO)
        exp_file_handler.setFormatter(Formatter(log_file_format))

        exp_errors_file_handler = RotatingFileHandler(f'{log_file_prefix}_error.log',
                                                      maxBytes=10 ** 6,
                                                      backupCount=5)
        exp_errors_file_handler.setLevel(WARNING)
        exp_errors_file_handler.setFormatter(Formatter(log_file_format))

        main_logger.addHandler(exp_file_handler)
        main_logger.addHandler(exp_errors_file_handler)
