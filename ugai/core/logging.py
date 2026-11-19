import logging
import os

def configure_logging() -> None:
    logging.basicConfig(level=os.getenv("UGAI_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
