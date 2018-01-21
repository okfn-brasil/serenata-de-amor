"""Internal exceptions that can be generated in network interface code.
These are use to control what the upper levels should do when different
types of errors occur.

"""

class NetworkInterfaceException(Exception): pass
class ForceAgentRestart(NetworkInterfaceException): pass
class ForceAgentDisconnect(NetworkInterfaceException): pass
class DiscardDataForRequest(NetworkInterfaceException): pass
class RetryDataForRequest(NetworkInterfaceException): pass
class ServerIsUnavailable(RetryDataForRequest): pass
