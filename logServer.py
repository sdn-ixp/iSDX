import asyncore
import datetime
import logging, logging.handlers
import os
import pickle
import socket
import struct
import sys

class MyFormatter(logging.Formatter):
    "Custom logging formatter to return usecs as part of time"
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)

    def formatTime(self, record, datefmt=None):
	return datetime.datetime.fromtimestamp(record.created).strftime('%Y%m%d %H%M%S.%f')

def getLogger(fname=None):
    format='%(asctime)s:%(process)d:%(threadName)s:%(levelname)s:%(name)s:%(pathname)s %(lineno)d:%(message)s'
    formatter = MyFormatter(format)

    logger = logging.getLogger('sdx')

    if fname:
        fh = logging.FileHandler(fname)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

fname = None
if len(sys.argv) > 1:
    fname = sys.argv[1]
globalLogger = getLogger(fname)

class LogRecordHandler(asyncore.dispatcher):

    def __init__(self, sock):
        asyncore.dispatcher.__init__(self, sock)
        self.data = ''
        self.rlen = 0
        self.dlen = 4

    def handle_read(self):
        try:
            data = self.recv(self.dlen)
            if len(data) == 0:
                return
        except socket.error as e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return

        self.data += data
        self.dlen -= len(data)
        if self.dlen > 0:
            # don't have complete record yet. wait for more data to read
            return

        if self.rlen == 0:
            self.dlen = self.rlen = struct.unpack('>L', self.data)[0]
            self.data = ''
            # got record length. now read record
            return

        # got complete record
        obj = pickle.loads(self.data)
        record = logging.makeLogRecord(obj)

        # Note: EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering.
        # Filter (e.g., only WARNING or higher)
        # at the sender to save network bandwidth.
        globalLogger.handle(record)

        # reset for next record
        self.data = ''
        self.rlen = 0
        self.dlen = 4

    def writable(self):
        return False


class LogRecordServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            LogRecordHandler(sock)


LogRecordServer('', logging.handlers.DEFAULT_TCP_LOGGING_PORT)
asyncore.loop(timeout=None, use_poll=True)
