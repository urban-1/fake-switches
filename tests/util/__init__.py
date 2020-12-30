import socket

from fake_switches.switch_configuration import Port, AggregatedPort

_unique_port_index = 20000


def _unique_port():
    global _unique_port_index
    _unique_port_index += 1
    return _unique_port_index


def unique_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def _juniper_ports_with_less_ae():
    return [Port("ge-0/0/{}".format(i)) for i in range(1, 5)] + [
        AggregatedPort("ae{}".format(i)) for i in range(1, 5)
    ]
