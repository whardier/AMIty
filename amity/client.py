#!/usr/bin/env python
#
#Copyright (c) 2012  Shane R. Spencer
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions: 
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software. 
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

"""Client(s) and ClientManager"""

import uuid
import logging
import socket
import operator
import time

import os.path

import tornado.ioloop
import tornado.httpclient
import tornado.httputil
#import tornado.gen

import tornado.stack_context

from copy import copy
from hashlib import md5

from urllib import urlencode
from urllib2 import parse_http_list
from urllib2 import parse_keqv_list

from urlparse import urlsplit
from urlparse import urlunsplit
from urlparse import parse_qs
from urlparse import SplitResult as URL #because I can

from Cookie import SimpleCookie

from errors import InterfaceError
from common import COMMANDALIAS, KEYALIAS, VALUEALIAS, VALUENEVERALIAS

DEBUG = True

tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient") #very sexy

def GenerateActionID():
    return str(uuid.uuid1())

class Request(object):
    def __init__(self, action=None, callback=None, key=None, key_max=1, retry=True, distinct_action=False, distinct_action_kwargs=False, **kwargs):
        assert isinstance(action, (str, unicode, None.__class__))
        assert isinstance(key, (str, unicode, None.__class__))
        assert isinstance(key_max, int)
        assert isinstance(retry, bool)
        assert isinstance(distinct_action, bool)
        assert isinstance(distinct_action_kwargs, bool)

        self.action = action
        self.callback = callback
        self.key = key
        self.key_max = key_max
        self.retry = retry
        self.distinct_action = distinct_action
        self.distinct_action_kwargs = distinct_action_kwargs
        self.actionid = GenerateActionID()
        self.kwargs = {}
        self.timestamp = time.time()

        for kw, value in kwargs.iteritems():
            kw = KEYALIAS.get(kw, kw)
            if kw not in VALUENEVERALIAS:
                value = VALUEALIAS.get(value, value)
            self.kwargs[kw] = value

    def _request_dict(self):
        return dict(list({'Action': self.action, 'ActionID': self.actionid}.items()) + list(self.kwargs.items()))

    def amiencode(self, tail=False):
        assert isinstance(tail, bool)

        return "\r\n".join(["%s: %s" % (k, v) for k, v in self._request_dict().iteritems()]) + ('\r\n' if tail else '')
        
    def urlencode(self):
        return urlencode(self._request_dict())



class ClientManager(object):
    def __init__(self): #add ioloop.stop somehow
        
        self._clients = []
        self._cleaner = tornado.ioloop.PeriodicCallback(self._clean, 1000).start() #will never stop.. mwahaha

    def addclient(self, client):
        assert isinstance(client, (AJAMClient))
        self._clients.append(client)
        return client

    def _clean(self):
        for client in self._clients:
            if not client.active:
                client._cleanup()
                self._clients.remove(client)
                del(client) #will this work?


class BaseClient(object):
    def __init__(self, *args, **kwargs):
        self.__preinit__(*args, **kwargs) #TODO: Am I insane? Please check
        self.__postinit__(*args, **kwargs)

    def __preinit__(self, *args, **kwargs):
        #URL and Digest preferences
        self._host = kwargs.get('host', '127.0.0.1')
        self._port = kwargs.get('port', 8088)
        self._secure = kwargs.get('secure', False)

        #AMI Authentication
        self._username = kwargs.get('username', 'amity')
        self._secret = kwargs.get('secret', 'amity')
        self._digest = kwargs.get('digest', True)

        #AMI interface preferences
        self._keepalive = kwargs.get('keepalive', 1000)
        self._events = kwargs.get('events', True)

        #AJAM Prefix
        self._prefix = kwargs.get('prefix', '')

        #SSL Options
        self._validate_certs = kwargs.get('validate_certs', True)
        self._ca_certs = kwargs.get('ca_certs')
        #IP Preferences
        self._allow_ipv6 = kwargs.get('allow_ipv6', True)
        self._force_ipv6 = kwargs.get('force_ipv6', False)
        #Proxy Preferences
        self._proxy_host = kwargs.get('proxy_host')
        self._proxy_port = kwargs.get('proxy_port')
        self._proxy_username = kwargs.get('proxy_username')
        self._proxy_password = kwargs.get('proxy_password')

        assert isinstance(self._host, (str, unicode))
        assert isinstance(self._port, int)
        assert isinstance(self._secure, bool)
        assert isinstance(self._username, (str, unicode))
        assert isinstance(self._secret, (str, unicode))
        assert isinstance(self._digest, bool)
        assert isinstance(self._prefix, (str, unicode))
        assert isinstance(self._events, bool)
        assert isinstance(self._keepalive, int)
        assert isinstance(self._validate_certs, bool)
        assert isinstance(self._ca_certs, (None.__class__))
        assert isinstance(self._allow_ipv6, bool)
        assert isinstance(self._force_ipv6, bool)
        assert isinstance(self._proxy_host, (str, unicode, None.__class__))
        assert isinstance(self._proxy_port, (int, None.__class__))
        assert isinstance(self._proxy_username, (str, unicode, None.__class__))
        assert isinstance(self._proxy_password, (str, unicode, None.__class__))

        self._requests = [] #going to have to traverse this list if you don't use the map
        self._requests_actionid_map = {} #use this to pop from __requests

        self._alive = False

        self._authenticated = False
        self._authenticating = False
        self._authentication_request = None

        self._digest_nc = 1
        self._digest_last_nonce = None
        self._digest_last_cnonce = None

        self.active = True

    def __postinit__(self, *args, **kwargs):
        self._keepalive_timer = tornado.ioloop.PeriodicCallback(self._keepalive_timer_callback, self._keepalive)
        self._keepalive_timer.start()

    def _keepalive_timer_callback(self):
        pass

    def _make_basic_login_request(self, callback=None):
        return Request(action='Login',
                        callback=callback,
                        username=self._username,
                        secret=self._secret,
                        events=self._events)

    def _make_digest_login_request(self, callback=None):
        return Request(action='Challenge',
                        callback=callback)

    def _request_from_any(self, req):
        assert isinstance(req, (str, unicode, Request))

        if isinstance(req, (str, unicode)): #Is it an actionid (useful for multi part callbacks)
            req = self._requests_actionid_map.get(req)
            if not req:
                raise InterfaceError('Bad Request')                

        return req


###
### BIG FAT WARNING: Digest mode is incomplete until Asterisk is patched.  Version checking will be done in the future 
### once completed
###

###
### TODO: Use digest for every call if 401/200 does not return a session key.
###

class AJAMClient(BaseClient):
    def __init__(self, *args, **kwargs):
        super(AJAMClient, self).__preinit__(*args, **kwargs)

        self._uuid = str(uuid.uuid1()) #TODO: Make sure this is unique and check it later on

        self._access_method = 'arawman' if self._digest else 'rawman'
        self._protocol = 'https' if self._secure else 'http'       

        self._cookie = SimpleCookie()

        super(AJAMClient, self).__postinit__(*args, **kwargs)

        self.login()

        if DEBUG:
            self._connect_timer = tornado.ioloop.PeriodicCallback(self._print_my_status, 2000)
            self._connect_timer.start()

    def _check_authenticated(self):
        if self._authenticated or self._authenticating:
            return

        return self.login()

    def _keepalive_timer_callback(self):
        self._check_authenticated()
        self.command(Request(action='Ping'))

    def _keepalive_timer_ping_callback(self, response):
        self._command_callback(response)

    def _cleanup(self):
        self._keepalive_timer.stop()
        del(self._keepalive_timer)

    def _update_session_cookie(self, response):
        if 'Set-Cookie' in response.headers:
            self._cookie.load(response.headers['Set-Cookie'])

    def _get_session_cookie(self):
        return self._cookie.output(header="", attrs="mansession_id").strip()

    def command(self, req, headers={}):
        assert isinstance(req, Request)

        if not req in self._requests:
            self._requests.append(req)
            self._requests_actionid_map[req.actionid] = req
        
        url = URL(scheme = self._protocol,
                    netloc = '%s:%d' % (self._host, self._port),
                    path = os.path.join('/', self._prefix, self._access_method),
                    query = req.urlencode(),
                    fragment = ''
                    )

        request = tornado.httpclient.HTTPRequest(url = urlunsplit(url),
                    headers = tornado.httputil.HTTPHeaders(headers),
                    proxy_host = self._proxy_host,
                    proxy_port = self._proxy_port,
                    proxy_username = self._proxy_username,
                    proxy_password = self._proxy_password
                    )

        request.headers.add('Cookie', self._get_session_cookie())

        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(request, req.callback or self._command_callback)

        return req

    def _digest_login_callback(self, response):

        self._update_session_cookie(response)

        if response.code == 200:
            self._authenticated = True
            self._alive = True
            print response.headers
            print 'yay'
            return
        elif response.code == 401:
            print 'meh'
        else:
            print 'boo'
            return

        #If 401

        if not 'WWW-Authenticate' in response.headers:
            raise InterfaceError()

        if not 'Digest' in response.headers['WWW-Authenticate']:
            raise InterfaceError()

        param_string = response.headers.get('WWW-Authenticate').partition('Digest')[2]
        param_list = parse_http_list(param_string)
        params = parse_keqv_list(param_list)

        path = urlsplit(response.effective_url) #asterisk throws query into hash
        digest_path = "%s?%s" % (path.path, path.query)

        digest_cnonce = uuid.uuid1().hex
        digest_nc = '%08d' % self._digest_nc 
        digest_qop = "auth"

        digest_response = md5(":".join([md5(":".join((self._username, params['realm'], self._secret))).hexdigest(),
                                 params['nonce'],
                                 digest_nc,
                                 digest_cnonce,
                                 digest_qop,
                                 md5(":".join(('GET', digest_path))).hexdigest()
                                ])).hexdigest()


        headers = {}
        headers['Authorization'] = 'Digest username="%s", realm="%s", nonce="%s", uri="%s", cnonce="%s", nc=%s, qop="%s", response="%s", opaque="%s", algorithm="%s"' % (
                                        self._username,
                                        params['realm'],
                                        params['nonce'],
                                        digest_path,
                                        digest_cnonce,
                                        digest_nc,
                                        digest_qop,
                                        digest_response, 
                                        params['opaque'],
                                        params['algorithm']
                                       )

        self._digest_nc += 1

        self.command(self._authentication_request, headers=headers)

    def _basic_login_callback(self, response):
        self._update_session_cookie(response)
        self._command_callback(response)

    def _make_digest_login_request(self, callback=None):
        return Request(action='UserEvent', userevent='DigestLogin', uuid=self._uuid, callback=callback) #Do a simple ping

    def _command_callback(self, response):
        for packet_text in response.body.strip().split("\r\n\r\n"):
            packet = {}
            for packet_line in packet_text.strip().split("\r\n"):
                packet_line = packet_line.rstrip()
                if ':' not in packet_line:
                    print 'Is weird for now', line
                
                key, val = packet_line.split(':', 1)
                val = val[1:] #quick and dirty left trim value even if it's 0 length
                packet[key] = val

            if not 'ActionID' in packet:
                print 'OHNOES'
                continue

            req = self._request_from_any(packet['ActionID'])

            attr = '_handle_%s_reply' % str(req.action).lower()
            if hasattr(self, attr):
                callable = getattr(self, attr)
                if operator.isCallable(callable):
                    callable(response, req, packet)

            attr = 'handle_%s_reply' % str(req.action).lower()
            if hasattr(self, attr):
                callable = getattr(self, attr)
                if operator.isCallable(callable):
                    callable(response, req, packet)
                    
            self._requests.remove(req)
            del(self._requests_actionid_map[packet['ActionID']])
            
        print req.action, packet

    def handle_login_reply(self, response, req, packet, *args, **kwargs):
        if packet['Response'] == 'Success':
            self._authenticated = True
            self._alive = True

        return

    def _handle_ping_reply(self, response, req, packet, *args, **kwargs):
        if response.code != 200:
            self._authenticated = False
            self._alive = False
            return            

        if not response.body:
            self._alive = False
            return            

        if 'Response: Success' in response.body:
            self._alive = True

        elif 'Message: Permission denied' in response.body:
            self._alive = False
            self._authenticated = False
        else:
            self._alive = False

        return

    def login(self):
        self._alive = False
        self._authenticated = False

        if self._digest:
            self._authentication_request = self._make_digest_login_request(callback=self._digest_login_callback)
        else:
            self._authentication_request = self._make_basic_login_request(callback=self._basic_login_callback)

        return self.command(self._authentication_request)

    def _print_my_status(self):
        logging.info('%s: Alive %s' % (self._uuid, self._alive))
        logging.info('%s: Authenticated %s' % (self._uuid, self._authenticated))
        logging.info('%s: Authenticating %s' % (self._uuid, self._authenticating))
        logging.info('%s: Requests %s' % (self._uuid, [x.actionid for x in self._requests]))



































"""

class AJAMClientOld(object):
    r""""""

    def __init__(self, host='127.0.0.1', port=8088, secure=False, prefix='', digest=True, username='amity', secret='amity', events=True, keepalive=1000, validate_certs=True, ca_certs=None, allow_ipv6=True, force_ipv6=False, proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None):
        assert isinstance(host, (str, unicode))
        assert isinstance(port, int)
        assert isinstance(secure, bool)
        assert isinstance(prefix, (str, unicode))
        assert isinstance(digest, bool)
        assert isinstance(username, (str, unicode))
        assert isinstance(secret, (str, unicode))
        assert isinstance(events, bool)
        assert isinstance(keepalive, int)
        assert isinstance(validate_certs, bool)
        assert isinstance(ca_certs, (bool, None.__class__))
        assert isinstance(allow_ipv6, bool)
        assert isinstance(force_ipv6, bool)
        assert isinstance(proxy_host, (str, unicode, None.__class__))
        assert isinstance(proxy_port, (int, None.__class__))
        assert isinstance(proxy_username, (str, unicode, None.__class__))
        assert isinstance(proxy_password, (str, unicode, None.__class__))

        #Used during logging
        self._uuid = str(uuid.uuid1()) #TODO: Make sure this is unique and check it later on

        #URL and Digest preferences
        self._host = host
        self._port = port
        self._secure = secure
        self._prefix = prefix
        self._digest = digest

        #SSL Options
        self._validate_certs = validate_certs
        self._ca_certs = ca_certs

        #IP Preferences
        self._allow_ipv6 = allow_ipv6
        self._force_ipv6 = force_ipv6

        #Proxy Preferences
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._proxy_username = proxy_username
        self._proxy_password = proxy_password

        #
        self._username = username
        self._secret = secret

        #Run WaitEvent?
        self._events = events

        #Prepare URL
        self._access_method = 'arawman' if self._digest else 'rawman'
        self._protocol = 'https' if self._secure else 'http'       
        self._baseurl = "%s://%s:%d/" % (self._protocol, self._host, self._port)
        self._url = urljoin(self._baseurl, os.path.join('/', self._prefix, self._access_method))

        self._cookie = SimpleCookie()

        self.__requests = [] #going to have to traverse this list if you don't use the map
        self.__requests_actionid_map = {} #use this to pop from __requests

        self._alive = False
        self._authenticated = False
        self._authenticating = False

        self._digest_nc = 1

        self._action = None

        if DEBUG:
            self._connect_timer = tornado.ioloop.PeriodicCallback(self._print_my_status, 1000)
            self._connect_timer.start()

        self._keepalive_timer = tornado.ioloop.PeriodicCallback(self._keepalive, 5000) #use cookie max age
        self._keepalive_timer.start()

        self._check_authenticated()

    def _print_my_status(self):
        logging.info('%s: Alive %s' % (self._uuid, self._alive))
        logging.info('%s: Authenticated %s' % (self._uuid, self._authenticated))
        logging.info('%s: Authenticating %s' % (self._uuid, self._authenticating))

    def _fresh_request(self, url=None):
        request = tornado.httpclient.HTTPRequest(url or self._url)
        request.headers = tornado.httputil.HTTPHeaders()     
        request.headers.add('Cookie', self._get_session_cookie())
        request.proxy_host = self._proxy_host
        request.proxy_port = self._proxy_port
        request.proxy_username = self._proxy_username
        request.proxy_username = self._proxy_password
        return request

    def _send_request(self):
        self._check_authenticated()

        return

    def _login_digest(self):
        self._authenticating = True

        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request()
        client.fetch(request, self._login_digest_challenge_request)
        return

    def _login_digest_challenge_request(self, response):

        if not response.body:
            self._alive = False            
            self._authenticating = False
            return 
    
        if not 'WWW-Authenticate' in response.headers:
            raise InterfaceError()

        if not 'Digest' in response.headers['WWW-Authenticate']:
            raise InterfaceError()

        param_string = response.headers.get('www-authenticate').partition('Digest')[2]
        param_list = parse_http_list(param_string)
        params = parse_keqv_list(param_list)

        digest_path = os.path.join('/', self._prefix, self._access_method)
        digest_cnonce = uuid.uuid1().hex
        digest_nc = '%08d' % self._digest_nc 
        digest_qop = "auth"

        digest_response = md5(":".join([md5(":".join((self._username, params['realm'], self._secret))).hexdigest(),
                                 params['nonce'],
                                 digest_nc,
                                 digest_cnonce,
                                 digest_qop,
                                 md5(":".join(('GET', digest_path))).hexdigest()
                                ])).hexdigest()


        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request()
        request.headers.add('Authorization', 'Digest username="%s", realm="%s", nonce="%s", uri="%s", cnonce="%s", nc=%s, qop="%s", response="%s", opaque="%s", algorithm="%s"' % (self._username, params['realm'], params['nonce'], digest_path, digest_cnonce, digest_nc, digest_qop, digest_response, params['opaque'], params['algorithm']))

        self._digest_nc += 1

        client.fetch(request, self._login_digest_challenge_response)        
        return

    def _login_digest_challenge_response(self, response):

        if not response.body:
            self._alive = False            
            self._authenticating = False
            return 

        if response.code != 200:
            self._authenticating = False
            return

        self._update_session_cookie(response)
    
        self._alive = True #well.. for now
        self._authenticated = True

        self._post_login()

        return

    def _login(self):
        self._authenticating = True

        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request(self._url + '?' + urlencode({'Action': 'Login', 'Username': self._username, 'Secret': self._secret}))

        client.fetch(request, self._login_request)

        return

    def _login_request(self, response):

        if not response.body:
            self._alive = False
            self._authenticating = False
            return

        self._update_session_cookie(response)

        if "Message: Authentication accepted" in response.body: #cheap and effective.. do this before setting _attempting_authentication to avoid race
            self._alive = True
            self._authenticated = True

        self._authenticating = False

        self._post_login()
    
        return

    def _post_login(self):
        self._keepalive_timer.start()

    def _print_response(self, response):
        print response.body

    def _update_session_cookie(self, response):
        if 'Set-Cookie' in response.headers:
            self._cookie.load(response.headers['Set-Cookie'])        

    def _get_session_cookie(self):
        return self._cookie.output(header="", attrs="mansession_id").strip()

    def _check_authenticated(self):
        if self._authenticated or self._authenticating:
            return

        self._login_digest() if self._digest else self._login()

        return

    def _keepalive(self):

        self._check_authenticated()

        client = tornado.httpclient.AsyncHTTPClient()
        request = self._fresh_request(self._url + '?' + urlencode({'Action': 'Ping'}))
        client.fetch(request, self._keepalive_response)

    def _keepalive_response(self, response):

        if not response.body:
            self._alive = False
            return

        if 'Response: Success' in response.body:
            self._alive = True
        elif 'Message: Permission denied' in response.body:
            self._alive = False
            self._authenticated = False
        else:
            self._alive = False

    def _handle_request_queue(self, response):
        pass
"""
