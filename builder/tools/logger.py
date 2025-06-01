import sys
import logging
import inspect
import threading


class Colours:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


class Logger:
    """Singleton logger."""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        raise RuntimeError("Call get_logger() instead.")

    def __new__(cls, *args, **kwargs) -> object:
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init(*args, **kwargs)

        return cls._instance

    def _init(self, level = logging.DEBUG) -> None:
        """Custom singleton logger initializer.

        :param level: Logging level.
        :return: None
        """
        self.logger = logging.getLogger("ZeroKernelLogger")
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            #formatter = logging.Formatter("[%(asctime)s] [%(levelname).1s] %(message)s")
            formatter = self._get_coloured_formatter()

            # direct DEBUG and INFO to stdout; WARNING, ERROR and CRITICAL to stderr
            h_stdout = logging.StreamHandler(sys.stdout)
            h_stdout.setLevel(logging.DEBUG)
            h_stdout.addFilter(lambda record: record.levelno <= logging.INFO)
            h_stdout.setFormatter(formatter)

            h_stderr = logging.StreamHandler(sys.stderr)
            h_stderr.setLevel(logging.WARNING)
            h_stderr.setFormatter(formatter)

            self.logger.addHandler(h_stdout)
            self.logger.addHandler(h_stderr)

    def _get_coloured_formatter(self) -> logging.Formatter:
        """Get log formatter.

        :return: Custom log formatter.
        :rtype: logging.Formatter
        """
        class ColouredFormatter(logging.Formatter):
            def format(self, record):
                # adjust index to reach the caller
                frame = inspect.stack()[8]
                module = inspect.getmodule(frame[0])
                module_name = module.__name__ if module else ""

                class_name = ""
                if "self" in frame[0].f_locals:
                    class_name = frame[0].f_locals["self"].__class__.__name__

                function_name = frame[3]
                caller_name = f"{module_name}.{class_name}.{function_name}".strip(".")

                # default colour to white
                colour = Colours.WHITE
                match record.levelno:
                    case logging.DEBUG:
                        colour = Colours.CYAN
                    case logging.INFO:
                        colour = Colours.GREEN
                    case logging.WARNING:
                        colour = Colours.YELLOW
                    case logging.ERROR:
                        colour = Colours.RED
                    case logging.CRITICAL:
                        colour = Colours.PURPLE

                record.msg = f"{colour}{record.msg}{Colours.RESET}"
                record.name = caller_name

                return super().format(record)

        return ColouredFormatter("[%(asctime)s] [%(levelname).1s] %(message)s")

    def set_level(self, level) -> None:
        """Set logging level.

        :param level: Logging level.
        :return: None
        """
        self.logger.setLevel(level)

    def get_logger(self) -> logging.Logger:
        """Get logger.

        :return: Logger.
        :rtype: logging.Logger
        """
        return self.logger
