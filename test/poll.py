import amity
import socket
import logging


import tornado.ioloop

if __name__ == "__main__":
    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
        format='%(asctime)s %(process)d %(filename)s %(lineno)d %(levelname)s #| %(message)s',
        datefmt='%H:%M:%S')

    amity.Client(host='testserver1', username='monast', secret='tsanom', events=True)
    amity.Client(host='testserver2', username='admin', secret='amp111', events=True)

    tornado.ioloop.IOLoop.instance().start()

