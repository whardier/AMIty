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
import tornado.gen

from hashlib import md5

from errors import InterfaceError
from common import COMMANDALIAS

tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient") #very sexy

class AJAMClient(object):
    r""""""

    def __init__(self, host='127.0.0.1', port=8088, secure=False, prefix=None, digest=True, username='amity', secret='amity', events=True, keepalive=1000, validate_certs=True, ca_certs=None, allow_ipv6=True, force_ipv6=False, proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None):
        assert isinstance(host, (str, unicode))
        assert isinstance(port, int)
        assert isinstance(secure, bool)
        assert isinstance(prefix, (str, unicode, None.__class__))
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
        self._access_method = '/arawman' if self._digest else '/rawman'

        self._protocol = 'https' if self._secure else 'http'
        
        self._baseurl = "%s://%s:%d/" % (self._protocol, self._host, self._port)

        self._url = self._baseurl

        if self._prefix:
            self._url = urlparse.urljoin(self._baseurl, self._prefix)

        self._url = urlparse.urljoin(self._url, self._access_method)

        self._magic_cookie = None

        self._callback = None

        self._alive = False
        self._authenticated = False
        self._attempting_login = False
        self._attempting_digest_authentication = False

        self._action = None
    
        self._login()

    def _fresh_request(self):
        request = tornado.httpclient.HTTPRequest(self._url)
        request.proxy_host = self._proxy_host
        request.proxy_port = self._proxy_port
        request.proxy_username = self._proxy_username
        request.proxy_username = self._proxy_password

        return request

    def _send_request(self):
        self._login()

    def _login_digest(self, response=None):
        if response:
            print response
            print response.headers
            print response.code
            return

        self._attempting_digest_authentication = True

        request = self._fresh_request()
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(request, self._login_digest)

        self._attempting_digest_authentication = False

    def _login(self):

        if self._authenticated:
            return

        self._attempting_login = True

        if self._digest:
            self._login_digest()
        else:
            return

        self._attempting_login = False

"""
    def _login_digest(self, request):

    def _login(self, request=None):
        self._attempting_login = True

        e = None
        digest = False
        
        if not request:
            request = self._url + '?Action=Ping'    

        try:
            response = tornado.httpclient.HTTPClient().fetch(request)
            self._attempting_login = False
            self._attempting_digest_authentication = False
            print response
            print response.body
        except tornado.httpclient.HTTPError, e:
            if code == 401:
                if 'WWW-Authenticate' in e.response.headers:
                    if 'Digest' in e.response.headers['WWW-Authenticate']:
                        self._perform_digest_login()

            if e:
                raise e

            if self._attempting_digest_authentication:
                raise e
            else:
               self._attempting_digest_authentication = True

            try:
                params = urllib2.parse_keqv_list(
                            urllib2.parse_http_list(
                                e.response.headers.get('www-authenticate').partition('Digest')[2]
                            )
                         )
    
                #params['username']
                #params['realm']
                #params['nonce']
                uri = os.path.join(self._prefix, self._access_method + '?Action=Ping')
                cnonce = uuid.uuid1().hex
                nc = "00000001"
                qop = "auth"
                #params['opaque']
                #params['algorithm']
                response = md5(":".join([
                            md5(":".join((self._username, params['realm'], self._secret))).hexdigest(),
                            params['nonce'],
                            nc,
                            cnonce,
                            qop,
                            md5(":".join(('GET', uri))).hexdigest()
                            ])).hexdigest()

                headers = tornado.httputil.HTTPHeaders()
                headers.add('Authorization', 'Digest username="%s", realm="%s", nonce="%s", uri="%s", cnonce="%s", nc=%s, qop="%s", response="%s", opaque="%s", algorithm="%s"' % (self._username, params['realm'], params['nonce'], uri, cnonce, nc, qop, response, params['opaque'], params['algorithm']))
                import time
                time.sleep(1)
                print e, e.response
                self._login(request=tornado.httpclient.HTTPRequest(e.response.effective_url, headers=headers))

            except:
                raise
                pass #make do something                               

        self._attempting_login = False

#Digest username="admin", realm="pbx01.voip.cda01", nonce="686ce6b9", uri="/arawman?action=ListCommands", cnonce="MDkzMDYw", 
#nc=00000001, qop="auth", response="c42fb64726167d450cc7d6ce63636c34", opaque="686ce6b9", algorithm="MD5"



#'nonce': '2c7b2d3e', 'qop': 'auth', 'realm': 'asterisk', 'opaque': '2c7b2d3e', 'algorithm': 'MD5'
"""
