"""Utility functions for calculating URLs of data collector and proxes.

"""

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

def platform_url(host='platform-api.newrelic.com', port=None, ssl=True):
    """Returns the URL for talking to the data collector when reporting
    platform metrics.

    """

    url = '%s://%s/platform/v1/metrics'

    scheme = ssl and 'https' or 'http'
    server = port and '%s:%d' % (host, port) or host

    return url % (scheme, server)

def proxy_details(proxy_scheme, proxy_host, proxy_port, proxy_user,
        proxy_pass):
    """Returns the dictionary of proxy server settings. This is returned
    in form as expected by the 'requests' library when making requests.

    """

    # If no proxy_host defined at all, then nothing to do.

    if not proxy_host:
        return

    # If there is a proxy_host and it isn't a URL then we also require a
    # proxy_port to be separately defined.

    components = urlparse.urlparse(proxy_host)

    if not components.scheme and not proxy_port:
        return

    # If a URL was provided for proxy_host which included a port then
    # proxy_port should not also be set. Similarly, if the proxy user
    # and password were supplied within the URL passed as proxy_host,
    # they should not be set separately. We don't give an error if they
    # are also set separately and will just concatenate them together
    # anyway. Not sure if the trailing path for a proxy is ever
    # significant so always leave in intact.

    path = ''

    if components.scheme:
        proxy_scheme = components.scheme
        netloc = components.netloc
        path = components.path

    elif components.path:
        netloc = components.path

    else:
        netloc = proxy_host

    if proxy_port:
        netloc = '%s:%s' % (netloc, proxy_port)

    if proxy_user:
        proxy_user = proxy_user or ''
        proxy_pass = proxy_pass or ''

        if proxy_pass:
            netloc = '%s:%s@%s' % (proxy_user, proxy_pass, netloc)
        else:
            netloc = '%s@%s' % (proxy_user, netloc)

    if proxy_scheme is None:
        proxy_scheme = 'http'

    proxy = '%s://%s%s' % (proxy_scheme, netloc, path)

    return { 'http': proxy, 'https': proxy }
