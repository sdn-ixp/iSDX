import datetime
import logging, logging.handlers

# Use a global LogLevel to get uniform behavior across all python processes.
LogLevel = logging.DEBUG

# where logging info goes / where logServer.py is running.
HOST = 'localhost'
#HOST = '10.0.0.5'
PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT

class UsecsFormatter(logging.Formatter):
    "Custom logging formatter to return usecs as part of time"
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)

    def formatTime(self, record, datefmt=None):
	return datetime.datetime.now().strftime('%Y%m%d %H%M%S.%f')

format='%(asctime)s:%(levelname)s:%(name)s:%(filename)s %(lineno)d:%(message)s'
formatter = UsecsFormatter(format)

socketHandler = logging.handlers.SocketHandler(HOST, PORT)
socketHandler.setFormatter(formatter)

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LogLevel)
    logger.addHandler(socketHandler)

    return logger
