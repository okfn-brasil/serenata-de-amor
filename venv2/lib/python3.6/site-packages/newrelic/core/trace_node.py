from collections import namedtuple

RootNode = namedtuple('RootNode',
        ['start_time', 'empty0', 'empty1', 'root', 'attributes'])

def root_start_time(root):
    return root.start_time * 1000.0

TraceNode = namedtuple('TraceNode',
        ['start_time', 'end_time', 'name', 'params', 'children', 'label'])

def node_start_time(root, node):
    return (node.start_time - root.start_time) * 1000.0

def node_end_time(root, node):
    return (node.end_time - root.start_time) * 1000.0
