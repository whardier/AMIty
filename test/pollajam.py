import socket
import logging

import tornado.ioloop

import amity.client

if __name__ == "__main__":
    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
        format='%(asctime)s %(process)d %(filename)s %(lineno)d %(levelname)s #| %(message)s',
        datefmt='%H:%M:%S')

    #testingserver = amity.client.AJAMClient(host='testserver1', proxy_host='10.10.0.1', proxy_port=3128)
    testingserver = amity.client.AJAMClient(host='testserver1')

    tornado.ioloop.IOLoop.instance().start()
