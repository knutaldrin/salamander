"""
Api functions for Saleae Logic
"""

import socket

__all__ = ['connect']

# Possible responses from Logic
ACK = 'ACK'
NAK = 'NAK'


def connect(host='127.0.0.1', port=10429):
    """

    :param host: Hostname/IP of the Logic instance to connect to
    :type  host: str
    :param port: Port to connect to
    :type  port: int
    :return:     A socket instance
    """

    return _SaleaeSocket(host, port)


class _SaleaeSocket(object):

    def __init__(self, host, port):
        """
        Abstraction of the Saleae Logic socket API

        :param host: Hostname/IP of the Logic instance to connect to
        :type  host: str
        :param port: Port to connect to
        :type  port: int
        """
        try:
            self.sock = socket.create_connection((host, port))
        except socket.error:
            # TODO: Handle error
            raise
