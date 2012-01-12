import socket
import logging

import tornado.ioloop

import amity.client

if __name__ == "__main__":
    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
        format='%(asctime)s %(process)d %(filename)s %(lineno)d %(levelname)s #| %(message)s',
        datefmt='%H:%M:%S')

    #testingserver = amity.client.AJAMClient(host='testserver1', proxy_host='10.10.0.1', proxy_port=3128)
    ##amity.client.AJAMClient(host='testserver2', username='admin', secret='amp111')
    clientmanager = amity.client.ClientManager()

    class PeriodicClient(amity.client.AJAMClient):
        def do_something(self):
            self.command(amity.client.Request(action='CoreStatus'))
        def handle_corestatus_reply(self, response, req, packet, *args, **kwargs):
            pass 
            #print packet

    newclient = clientmanager.addclient(PeriodicClient(host='localhost', username='amity', secret='amity', digest=False))

    ##amity.client.AJAMClient(host='testserver2', username='admin', secret='amp111223344')
    ##amity.client.AJAMClient(host='testserver2', username='admin', secret='amp111223344', digest=False)

    tornado.ioloop.PeriodicCallback(newclient.do_something, 100).start()
            
    tornado.ioloop.IOLoop.instance().start()
