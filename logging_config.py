import logging


def setup_logging():
    logger = logging.getLogger("ser")
    handler = logging.FileHandler('C:/secure_erase/history.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logger.setLevel(logging.INFO)

    handler.setFormatter(formatter)
    logger.addHandler(handler)