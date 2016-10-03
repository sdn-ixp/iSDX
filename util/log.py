import logging, logging.handlers
import pprint
import json

# Use a global LogLevel to get uniform behavior across all python processes.
LogLevel = logging.DEBUG

# where logging info goes / where logServer.py is running.
HOST = 'localhost'
PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT

socketHandler = logging.handlers.SocketHandler(HOST, PORT)

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LogLevel)
    logger.addHandler(socketHandler)

    return logger
