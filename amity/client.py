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
        self.__uuid = str(uuid.uuid1()) #TODO: Make sure this is unique and check it later on

        #URL and Digest preferences
        self.__host = host
        self.__port = port
        self.__secure = secure
        self.__prefix = prefix
        self.__digest = digest
        #SSL Options
        self.__validate_certs = validate_certs
        self.__ca_certs = ca_certs
        #IP Preferences
        self.__allow_ipv6 = allow_ipv6
        self.__force_ipv6 = force_ipv6
        #Proxy Preferences
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__proxy_username = proxy_username
        self.__proxy_password = proxy_password

        #
        self.__username = username
        self.__secret = secret

        self.__events = events

        #Prepare URL
        self.__access_method = '/arawman' if self.__digest else '/rawman'

        self.__protocol = 'https' if self.__secure else 'http'
        
        self.__baseurl = "%s://%s:%d/" % (self.__protocol, self.__host, self.__port)

        self.__url = self.__baseurl

        if self.__prefix:
            self.__url = urlparse.urljoin(self.__baseurl, self.__prefix)

        self.__url = urlparse.urljoin(self.__url, self.__access_method)

        self.__magic_cookie = None

        self.__callback = None

        self.__alive = False
        self.__authenticated = False
        self.__attempting_login = False
        self.__attempting_digest_authentication = False

        self.__action = None
    
        self.__login()

    def __fresh_request(self):
        request = tornado.httpclient.HTTPRequest(self.__url)
        request.proxy_host = self.__proxy_host
        request.proxy_port = self.__proxy_port
        request.proxy_username = self.__proxy_username
        request.proxy_username = self.__proxy_password

        return request

    def __send_request(self):
        self.__login()

    def __login_digest(self, response=None):
        if response:
            print response
            print response.headers
            print response.code
            return

        self.__attempting_digest_authentication = True

        request = self.__fresh_request()
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(request, self.__login_digest)

        self.__attempting_digest_authentication = False

    def __login(self):

        if self.__authenticated:
            return

        self.__attempting_login = True

        if self.__digest:
            self.__login_digest()
        else:
            return

        self.__attempting_login = False

"""
    def __login_digest(self, request):

    def __login(self, request=None):
        self.__attempting_login = True

        e = None
        digest = False
        
        if not request:
            request = self.__url + '?Action=Ping'    

        try:
            response = tornado.httpclient.HTTPClient().fetch(request)
            self.__attempting_login = False
            self.__attempting_digest_authentication = False
            print response
            print response.body
        except tornado.httpclient.HTTPError, e:
            if code == 401:
                if 'WWW-Authenticate' in e.response.headers:
                    if 'Digest' in e.response.headers['WWW-Authenticate']:
                        self.__perform_digest_login()

            if e:
                raise e

            if self.__attempting_digest_authentication:
                raise e
            else:
               self.__attempting_digest_authentication = True

            try:
                params = urllib2.parse_keqv_list(
                            urllib2.parse_http_list(
                                e.response.headers.get('www-authenticate').partition('Digest')[2]
                            )
                         )
    
                #params['username']
                #params['realm']
                #params['nonce']
                uri = os.path.join(self.__prefix, self.__access_method + '?Action=Ping')
                cnonce = uuid.uuid1().hex
                nc = "00000001"
                qop = "auth"
                #params['opaque']
                #params['algorithm']
                response = md5(":".join([
                            md5(":".join((self.__username, params['realm'], self.__secret))).hexdigest(),
                            params['nonce'],
                            nc,
                            cnonce,
                            qop,
                            md5(":".join(('GET', uri))).hexdigest()
                            ])).hexdigest()

                headers = tornado.httputil.HTTPHeaders()
                headers.add('Authorization', 'Digest username="%s", realm="%s", nonce="%s", uri="%s", cnonce="%s", nc=%s, qop="%s", response="%s", opaque="%s", algorithm="%s"' % (self.__username, params['realm'], params['nonce'], uri, cnonce, nc, qop, response, params['opaque'], params['algorithm']))
                import time
                time.sleep(1)
                print e, e.response
                self.__login(request=tornado.httpclient.HTTPRequest(e.response.effective_url, headers=headers))

            except:
                raise
                pass #make do something                               

        self.__attempting_login = False

#Digest username="admin", realm="pbx01.voip.cda01", nonce="686ce6b9", uri="/arawman?action=ListCommands", cnonce="MDkzMDYw", 
#nc=00000001, qop="auth", response="c42fb64726167d450cc7d6ce63636c34", opaque="686ce6b9", algorithm="MD5"



#'nonce': '2c7b2d3e', 'qop': 'auth', 'realm': 'asterisk', 'opaque': '2c7b2d3e', 'algorithm': 'MD5'
"""
