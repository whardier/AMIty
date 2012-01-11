#!/usr/bin/env python

import os
import sys

import uuid

import logging

import urllib #I know right
import urllib2 #whaaat?
import urlparse #hey now

import Cookie

import socket

import tornado.ioloop
import tornado.httpclient
import tornado.httputil
#import tornado.gen

import tornado.stack_context

from hashlib import md5

from errors import InterfaceError
from common import COMMANDALIAS

DEBUG = True

tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient") #very sexy

class AJAMClient(object):
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
        self._url = urlparse.urljoin(self._baseurl, os.path.join('/', self._prefix, self._access_method))

        self._cookie = Cookie.SimpleCookie()

        self.__requests = []

        self._alive = False
        self._authenticated = False
        self._attempting_authentication = False

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
        logging.info('%s: Authenticating %s' % (self._uuid, self._attempting_authentication))

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
        self._attempting_authentication = True

        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request()
        client.fetch(request, self._login_digest_challenge_request)
        return

    def _login_digest_challenge_request(self, response):

        if not response.body:
            self._alive = False            
            self._attempting_authentication = False
            return 
    
        if not 'WWW-Authenticate' in response.headers:
            raise InterfaceError()

        if not 'Digest' in response.headers['WWW-Authenticate']:
            raise InterfaceError()

        param_string = response.headers.get('www-authenticate').partition('Digest')[2]
        param_list = urllib2.parse_http_list(param_string)
        params = urllib2.parse_keqv_list(param_list)

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
            self._attempting_authentication = False
            return 

        if response.code != 200:
            self._attempting_authentication = False
            return

        self._update_session_cookie(response)
    
        self._alive = True #well.. for now
        self._authenticated = True

        self._post_login()

        return

    def _login(self):
        self._attempting_authentication = True

        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request(self._url + '?' + urllib.urlencode({'Action': 'Login', 'Username': self._username, 'Secret': self._secret}))

        client.fetch(request, self._login_request)

        return

    def _login_request(self, response):

        if not response.body:
            self._alive = False
            self._attempting_authentication = False
            return

        self._update_session_cookie(response)

        if "Message: Authentication accepted" in response.body: #cheap and effective.. do this before setting _attempting_authentication to avoid race
            self._alive = True
            self._authenticated = True

        self._attempting_authentication = False

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
        if self._authenticated or self._attempting_authentication:
            return

        self._login_digest() if self._digest else self._login()

        return

    def _keepalive(self):

        self._check_authenticated()

        client = tornado.httpclient.AsyncHTTPClient()
        request = self._fresh_request(self._url + '?' + urllib.urlencode({'Action': 'Ping'}))
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
