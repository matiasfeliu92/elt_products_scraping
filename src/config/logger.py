import logging
import os

class LoggerConfig:
    _logger = None

    @classmethod
    def get_logger(cls, name: str = "pipeline") -> logging.Logger:
        if cls._logger is None:
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "pipeline.log")
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            cls._logger = logging.getLogger("pipeline")  # logger raíz único
            cls._logger.setLevel(logging.INFO)
            cls._logger.addHandler(console_handler)
            cls._logger.addHandler(file_handler)
            cls._logger.propagate = False
        return logging.LoggerAdapter(cls._logger, {"classname": name})