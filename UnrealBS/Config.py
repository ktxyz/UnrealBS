from threading import Event

import argparse
import logging
import sys


class Config:
    __instance = None
    LOG_VERBOSITY_CHOICES = ['debug', 'info', 'warning', 'error', 'critical']

    def __init__(self):
        self.universal_timeout = 1

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = object.__new__(cls)
            Config.__instance.singleton_init()
        return Config.__instance

    def singleton_init(self):
        self.universal_kill_ct = 0
        self.universal_kill_ev = Event()

        # TODO
        # figure out more pythonic way
        # of handling this shit
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-v", "--log_verbosity", type=str, choices=Config.LOG_VERBOSITY_CHOICES,
                                 default="info",
                                 help="Log verbosity level")
        self.parser.add_argument("-rd", "--recipe-dir", type=str, default='Examples/Linux',
                                 help="Path to search for recipes. Relative to CWD is best!")
        self.parser.add_argument("-f", "--log_file", type=str, default=None,
                                 help="Path to log file. If not specified, logs will be output only to console.")
        self.parser.add_argument("-sp", "--server_port", type=int, default=2137,
                                 help="Port for server to listen on")
        self.parser.add_argument("-sh", "--server_host", type=str, default="localhost",
                                 help="Host for server to bind to")
        self.parser.add_argument("-wp", "--worker_port", type=int, default=2138,
                                 help="Port for worker to listen on")
        self.parser.add_argument("-wh", "--worker_host", type=str, default="localhost",
                                 help="Host for worker to bind to")
        self.parser.add_argument("-rs", "--run_server", action="store_true", default=False,
                                 help="Flag to indicate if server should run")
        self.parser.add_argument("-rw", "--run_worker", action="store_true", default=False,
                                 help="Flag to indicate if worker should run")
        self.parser.add_argument("-k", "--secret-key", type=str, default='chujowy-klucz',
                                 help="Secret key for authentication")
        self.args = self.parser.parse_args(sys.argv[1:])

        log_level = getattr(logging, self.args.log_verbosity.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError("Invalid log verbosity level: %s" % self.args.log_verbosity)

        loggerFmt = logging.Formatter(fmt='[%(name)s]::[%(levelname)s]::: %(message)s')
        self.server_logger = logging.getLogger("SERVER")
        self.server_logger.setLevel(log_level)

        self.worker_logger = logging.getLogger("WORKER")
        self.worker_logger.setLevel(log_level)

        if self.args.log_file:
            file_handler = logging.FileHandler(self.args.log_file)
            file_handler.setFormatter(loggerFmt)
            file_handler.setLevel(log_level)
            self.server_logger.addHandler(file_handler)
            self.worker_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(loggerFmt)
        console_handler.setLevel(log_level)
        self.server_logger.addHandler(console_handler)
        self.worker_logger.addHandler(console_handler)
