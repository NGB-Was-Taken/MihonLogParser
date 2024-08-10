import logging
import sys


class Logger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.INFO)

        info_handler = logging.StreamHandler(sys.stdout)
        info_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s %(name)s: [%(levelname)s] - %(message)s"
        )
        info_handler.setFormatter(formatter)
        self.addHandler(info_handler)
