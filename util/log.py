import logging, logging.handlers
import pprint

# Use a global LogLevel to get uniform behavior across all python processes.
LogLevel = logging.DEBUG

# PrettyPrint helpful during development, but not good for grepping logs
PrettyPrint = True

# where logging info goes / where logServer.py is running.
HOST = 'localhost'
PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT

socketHandler = logging.handlers.SocketHandler(HOST, PORT)

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LogLevel)
    logger.addHandler(socketHandler)

    return logger

def pformat(json):
    if PrettyPrint == True:
        return "\n" + pprint.pformat(json)
    else:
        return str(json)
