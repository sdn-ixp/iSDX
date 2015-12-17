import logging, logging.handlers
import time

# Use a global LogLevel to get uniform behavior across all python processes.
LogLevel = logging.DEBUG

# where logging info goes.
HOST = 'localhost'
#HOST = '192.4.12.175'
PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT

class UsecsFormatter(logging.Formatter):
    "Custom logging formatter to return usecs as part of time"
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)

    def formatTime(self, record, datefmt=None):
        t = time.time()
        ts = time.localtime()
        ti = int(t)
        tf = t - ti
        return '%04d%02d%02d %02d%02d%02d.%06d' % (
                ts.tm_year,
                ts.tm_mon,
                ts.tm_mday,
                ts.tm_hour,
                ts.tm_min,
                ts.tm_sec,
                int(tf*1000000))

format='%(asctime)s:%(levelname)s:%(name)s:%(filename)s %(lineno)d:%(message)s'
formatter = UsecsFormatter(format)

socketHandler = logging.handlers.SocketHandler(HOST, PORT)
socketHandler.setFormatter(formatter)

def getLogger(name):
    # we use - as sep instead of . because with . we sometimes get duplicate
    # logging (when we register name sdx.x and sdx.x.y and print for sdx.x.y)
    lname = 'sdx-'+name
    logger = logging.getLogger(lname)
    logger.setLevel(LogLevel)
    logger.addHandler(socketHandler)

    return logger
