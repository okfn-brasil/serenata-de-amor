"""This module returns the CA certificate bundle included with the agent.

"""

import os


def where():
    return os.path.join(os.path.dirname(__file__), 'cacert.pem')
