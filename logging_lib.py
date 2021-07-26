# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.

from logging import getLogger, StreamHandler, Formatter
from opencensus.ext.azure.log_exporter import AzureLogHandler
import os

import config.config_logging as config_logging


def get_logger(module_name: str):
    """
    ロガー取得
    :param module_name: モジュール名
    :return: ロガー
    """
    formatter = Formatter('[%(levelname)s] %(asctime)s : %(module)s : %(funcName)s %(lineno)s : %(message)s')
    logger = getLogger(module_name)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(config_logging.LOG_LEVEL)
    logger.addHandler(stream_handler)
    azure_handler = AzureLogHandler(
        connection_string=os.environ["AZURE_INSIGHT_CONNECTION"])
    azure_handler.setFormatter(formatter)
    azure_handler.setLevel(config_logging.LOG_LEVEL)
    logger.setLevel(config_logging.LOG_LEVEL)
    logger.addHandler(azure_handler)

    return logger
