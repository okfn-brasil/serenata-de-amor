from newrelic.api.external_trace import wrap_external_trace

def instrument(module):

    def tsocket_open_url(socket, *args, **kwargs):
        scheme = 'socket' if socket._unix_socket else 'http'
        if socket.port:
            url = '%s://%s:%s' % (scheme, socket.host, socket.port)
        else:
            url = '%s://%s' % (scheme, socket.host)

        return url

    wrap_external_trace(module, 'TSocket.open', 'thrift', tsocket_open_url)
