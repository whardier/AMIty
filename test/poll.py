import amity
import socket
import logging


import tornado.ioloop

if __name__ == "__main__":
    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
        format='%(asctime)s %(process)d %(filename)s %(lineno)d %(levelname)s #| %(message)s',
        datefmt='%H:%M:%S')

    ioloop = tornado.ioloop.IOLoop.instance()
    events = True
    testingserver1 = amity.Client(host='testserver1', username='monast', secret='tsanom', events=events)
    #testingserver2 = amity.Client(host='testserver2', username='admin', secret='amp111', events=events)

    #tornado.ioloop.PeriodicCallback(testingserver1.ListCommands, 10000).start()

    ioloop.start()
