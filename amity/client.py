#!/usr/bin/env python

import uuid
import socket
import logging
import urllib
import Cookie

import tornado.iostream
import tornado.ioloop
import tornado.httpclient


from errors import InterfaceError

command_resolver = {
    'actionid': 'ActionID',
}

class Client(object):
    r""""""

    def __init__(self, ioloop=None, alias=None, host='127.0.0.1', port=5038, username='asterisk', secret='asterisk', events=True):
        self.__ioloop = ioloop
        self.__host = host
        self.__port = port
        self.__username = username
        self.__secret = secret
        self.__events = events
        self.__authenticate = False
        self.__requests = []       
        self.__alias = alias
        self.__attempting_connection = False
        self.__alive = False

        if not self.__alias:
            self.__alias = str(uuid.uuid1())

        self.__callback = None

        self.usage_count = 0

        self.__connect_timer = tornado.ioloop.PeriodicCallback(self.__keepalive, 1000, self.__ioloop)

        self.__connect()


    def __keepalive(self):
        if not self.__alive and not self.__attempting_connection:
            logging.info('%s Reconnecting (Via Periodic Timer)' % (self.__alias))
            self.__connect()

    def __connect(self):
        self.__attempting_connection = True
        self.usage_count = 0
        self.__connect_timer.stop()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.settimeout(10)
            s.connect((self.__host, self.__port))
            s.settimeout(None)
            self.__stream = tornado.iostream.IOStream(s)
            self.__stream.set_close_callback(self.__socket_close)
            self.__alive = True
            self.__attempting_connection = False
            self.__connect_timer = tornado.ioloop.PeriodicCallback(self.__keepalive, 1000, self.__ioloop) #Redifine here to restart the process from current execution date
            self.__connect_timer.start()
        except socket.error, error:
            self.__attempting_connection = False
            self.__connect_timer.start()
            #raise InterfaceError(error)

        self.__connect_timer.start()

        if self.__alive:
            try:
                self.__stream.read_until('\r\n', self.__handle_banner)
            except IOError, e:
                self.__alive = False
                raise

    def __send_complete(self, actionid=None):
        self.__stream.write("\r\n")

    def __send_command(self, auto_actionid=True, send_complete=True, callback=None, **kwargs):

        if not self.__alive:
            return

        if auto_actionid:
            actionid = str(uuid.uuid1())
            kwargs['actionid'] = actionid

        for kw, v in kwargs.iteritems():
            kw = command_resolver.get(kw, kw)
            self.__stream.write("%s: %s\r\n" % (kw, v))
            logging.info('%s Send Command (%s): %s: %s' % (self.__alias, actionid, kw, v))

        try:
            if send_complete:
                self.__send_complete()        
            self.__stream.read_until('\r\n\r\n', callback or self.__handle_message)
        except IOError, e:
            self.__alive = False
            raise

    def __socket_close(self):
        if self.__callback:
            self.__callback(None, InterfaceError('connection closed'))
        self.__callback = None
        self.__alive = False
        self.__stream._close_callback = None
        self.__stream.close()
        self.__connect()

    def __handle_banner(self, data):
        logging.info('%s Parse Banner: %s' % (self.__alias, data.strip()))
        self.__send_login()

    def __send_login(self):
        self.__send_command(action='login',
                            username=self.__username,
                            secret=self.__secret,
                            events=['off', 'on'][self.__events])
        #self.__stream.write("Action: login\r\n")
        #self.__stream.write("Username: %s\r\n" % self.__username)
        #self.__stream.write("Secret: %s\r\n" % self.__secret)
        #self.__stream.write("Events: %s\r\n" % ['off', 'on'][self.__events])
        #self.__stream.write("ActionID: %s\r\n" % uuid.uuid1())
        #self.__stream.write("\r\n")

    def __handle_message(self, data):
        print "ME"
        if data:
            logging.info('%s Print Message (STARTED)' % self.__alias)
            for line in data.strip().split('\r\n'):
                logging.info('%s Print Message: %s' % (self.__alias, line))
    
            logging.info('%s Print Message (ENDED)' % self.__alias)
    
        if self.__events:
            try:
                self.__stream.read_until('\r\n\r\n', self.__handle_message)
            except IOError, e:
                self.__alive = False
                raise

    def ListCommands(self):
        self.__send_command(action='ListCommands')

#invert_op = getattr(self, "invert_op", None)
#if callable(invert_op):
#    invert_op(self.path.parent_op)

class AJAMClient(object):
    r""""""

    def __init__(self, alias=None, host='127.0.0.1', port=8088, username='amity', secret='amity', events=True, ping=10000):
        self.__host = host
        self.__port = port
        self.__username = username
        self.__secret = secret
        self.__events = events
        self.__authenticated = False
        self.__requests = {}
        self.__requests_callbacks = {}
        self.__alias = alias
        self.__alive = False
        self.__attempting_login = False
        self.__cookie = None
        self.__waiting = False
        
        self.__url = "http://%s:%d/rawman?" % (self.__host, self.__port)

        if not self.__alias:
            self.__alias = str(uuid.uuid1())

        self.__keepalive_ping = tornado.ioloop.PeriodicCallback(self.send_ping, ping)
        self.__keepalive_ping.start()

        if self.__events:
            self.__keepalive_waitevent = tornado.ioloop.PeriodicCallback(self.__waitevent, 1000)
            self.__keepalive_waitevent.start()


    def __fetch(self, actionid, callback=None, final_callback=None):
        action = self.__requests[actionid].get('Action', None)

        if action != 'Login' and self.__attempting_login:
            print "Logging in right now hold your horses"
            return

        if action != 'Login' and not self.__authenticated:
            print "Attempting to login"
            self.__login()
            return

        print action

        callback = callback or self.__handle_request
        print self.__encode_request(actionid)

        request = tornado.httpclient.HTTPRequest(url=self.__url + self.__encode_request(actionid))
        #request = tornado.httpclient.HTTPRequest(url=self.__url + self.__encode_request(actionid), headers=[self.__cookie])

        if self.__cookie:
            request.headers = {'Cookie': self.__cookie}
            print request.headers

        self.__requests_callbacks[actionid] = final_callback

        ajam_client = tornado.httpclient.AsyncHTTPClient()
        ajam_client.fetch(request, callback)

    def __prepare_request(self, action, **kwargs):
        actionid = str(uuid.uuid1())

        request = {'Action': action}
        for kw, v in kwargs.iteritems():
            kw = command_resolver.get(kw, kw)
            request[kw] = v
        request['ActionID'] = actionid

        self.__requests[actionid] = request

        return actionid

    def __encode_request(self, actionid):
        return urllib.urlencode(self.__requests[actionid])

    def __login(self):
        print "Login 1"
        self.__attempting_login = True
        actionid = self.__prepare_request('Login', username=self.__username, secret=self.__secret)
        self.__cookie = False
        print "Login 2"
    
        self.__fetch(actionid)
        print "Login 3"

    def __waitevent(self):
        if self.__waiting:
            return

        self.__waiting = True
        print 'WaitEvent'

        actionid = self.__prepare_request('WaitEvent', timeout=10)

        self.__fetch(actionid, final_callback=self.__waitevent_process)

    def __waitevent_process(self, *args, **kwargs):
        print args, kwargs
        self.__waiting = False
        self.__waitevent()

    def __handle_request(self, response):
        if response.error:
            print "Error:", response.error
        else:
            parts = response.body.split('\r\n')
            import pprint
            pprint.pprint(parts)
            r = {}
            for part in parts:
                if not ': ' in part:
                    continue
                print "!!!!!!", part

                if part.strip().endswith(':'):
                    k = part.strip()[:-1]
                    v = ''
                else:
                    k, v = part.strip().split(': ', 1)

                r[k] = v

            if r.get('Response', None) == 'Error' and r.get('Message', None) == 'Permission denied':
                self.__authenticated = False
                self.__login()

            if r.get('Response', None) == 'Success' and r.get('Message', None) == 'Authentication accepted':
                self.__authenticated = True
                cookies = Cookie.SimpleCookie(response.headers['Set-Cookie'])
                self.__cookie = cookies.output('mansession_id', '')
                self.__attempting_login = False
                self.__waiting = False

            print r

            if 'ActionID' in r:
                print "FOUND", self.__requests[r['ActionID']]
                del(self.__requests[r['ActionID']])
                final_callback = self.__requests_callbacks[r['ActionID']]
                if final_callback:
                    final_callback()
                del(self.__requests_callbacks[r['ActionID']])

    def send_ping(self):
        actionid = self.__prepare_request('Ping')

        self.__fetch(actionid)
        pass
