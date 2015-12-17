import asyncore
import logging, logging.handlers
import os
import pickle
import socket
import struct
import sys
import time

class MyFormatter(logging.Formatter):
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

def getLogger(fname):
    format='%(asctime)s:%(levelname)s:%(name)s:%(filename)s %(lineno)d:%(message)s'
    formatter = MyFormatter(format)

    fh = logging.FileHandler(fname)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger = logging.getLogger('sdx')
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

globalLogger = getLogger(sys.argv[1])

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
asyncore.loop()
