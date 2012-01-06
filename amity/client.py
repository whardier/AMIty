#!/usr/bin/env python

import uuid
import socket
import logging

import tornado.iostream

from errors import InterfaceError

class Client(object):
    r""""""

    def __init__(self, host='127.0.0.1', port=5038, username='asterisk', secret='asterisk', events=True):
        self.__host = host
        self.__port = port
        self.__username = username
        self.__secret = secret
        self.__events = events
        self.__authenticate = False

        self.__callback = None

        self.usage_count = 0
        self.__connect()

    def __connect(self):
        self.usage_count = 0
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((self.__host, self.__port))
            self.__stream = tornado.iostream.IOStream(s)
            self.__stream.set_close_callback(self._socket_close)
            self.__alive = True
        except socket.error, error:
            raise InterfaceError(error)

        self.__stream.read_until('\r\n', self._parse_banner)

    def _socket_close(self):
        if self.__callback:
            self.__callback(None, InterfaceError('connection closed'))
        self.__callback = None
        self.__alive = False
        self.__stream._close_callback = None
        self.__stream.close()

    def _parse_banner(self, data):
        logging.info('Parse Banner: %s' % (data.strip()))
        self._send_login()

    def _send_login(self):
        self.__stream.write("Action: login\r\n")
        self.__stream.write("Username: %s\r\n" % self.__username)
        self.__stream.write("Secret: %s\r\n" % self.__secret)
        self.__stream.write("Events: %s\r\n" % ['off', 'on'][self.__events])
        self.__stream.write("ActionID: %s\r\n" % uuid.uuid1())
        self.__stream.write("\r\n")

        self.__stream.read_until('\r\n\r\n', self._print_message)

    def _print_message(self, data):
        logging.info('Print Message (STARTED)')
        for line in data.strip().split('\r\n'):
            logging.info('Print Message: %s' % (line))

        logging.info('Print Message (ENDED)')

        self.__stream.read_until('\r\n\r\n', self._print_message)

