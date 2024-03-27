import logging

def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('app_log.txt')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    return logger
