#!/usr/bin/env python

import os
import sys

import uuid

import logging

import urllib2
import urlparse

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

DEBUG = False

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

        self._events = events

        #Prepare URL
        self._access_method = 'arawman' if self._digest else 'rawman'

        self._protocol = 'https' if self._secure else 'http'
        
        self._baseurl = "%s://%s:%d/" % (self._protocol, self._host, self._port)

        self._url = urlparse.urljoin(self._baseurl, os.path.join('/', self._prefix, self._access_method))

        self._magic_cookie = None

        self._callback = None

        self._alive = False
        self._authenticated = False
        self._attempting_login = False
        self._attempting_digest_authentication = False
        self._digest_nc = 1

        self._digest_capable = 1

        self._action = None

        if DEBUG:
            self.__connect_timer = tornado.ioloop.PeriodicCallback(self._print_my_status, 1000)
            self.__connect_timer.start()

        self._login()

    def _print_my_status(self):
        logging.info('%s: Alive %s' % (self._uuid, self._alive))
        logging.info('%s: Authenticated %s' % (self._uuid, self._authenticated))

    def _fresh_request(self):
        request = tornado.httpclient.HTTPRequest(self._url)
        request.proxy_host = self._proxy_host
        request.proxy_port = self._proxy_port
        request.proxy_username = self._proxy_username
        request.proxy_username = self._proxy_password
        return request

    def _send_request(self):
        self._login()

        return

    def _login_digest(self):
        self._attempting_digest_authentication = True

        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request()
        client.fetch(request, self._login_digest_challenge_request)
        return

    def _login_digest_challenge_request(self, response):

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
        print ":".join((self._username, params['realm'], self._secret))
        print ":".join(('GET', digest_path))

        digest_response = md5(":".join([md5(":".join((self._username, params['realm'], self._secret))).hexdigest(),
                                 params['nonce'],
                                 digest_nc,
                                 digest_cnonce,
                                 digest_qop,
                                 md5(":".join(('GET', digest_path))).hexdigest()
                                ])).hexdigest()


        client = tornado.httpclient.AsyncHTTPClient()

        request = self._fresh_request()
        request.headers = tornado.httputil.HTTPHeaders()
        request.headers.add('Authorization', 'Digest username="%s", realm="%s", nonce="%s", uri="%s", cnonce="%s", nc=%s, qop="%s", response="%s", opaque="%s", algorithm="%s"' % (self._username, params['realm'], params['nonce'], digest_path, digest_cnonce, digest_nc, digest_qop, digest_response, params['opaque'], params['algorithm']))

        self._digest_nc += 1

        client.fetch(request, self._login_digest_challenge_response)        
        return

    def _login_digest_challenge_response(self, response):
        self._attempting_digest_authentication = False

        if response.code != 200:
            return
        self._alive = True #well.. for now
        self._authenticated = True
        return

    def _login(self):
        if self._authenticated or self._attempting_login:
            return

        self._attempting_login = True

        if self._digest:
            self._login_digest()
            return

        self._attempting_login = False
        return
