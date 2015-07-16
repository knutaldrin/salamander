"""
Api functions for Saleae Logic
"""

import socket

__all__ = ['connect', 'SaleaeError', 'NAKError', 'ResponseError']


def connect(host='127.0.0.1', port=10429):
    """

    :param host: Hostname/IP of the Logic instance to connect to
    :type  host: str
    :param port: Port to connect to
    :type  port: int
    :return:     A socket instance
    """

    return _SaleaeSocket(host, port)


class SaleaeError(Exception):
    pass


class NAKError(SaleaeError):
    pass


class ResponseError(SaleaeError):
    pass


class _SaleaeSocket(object):

    #: Receive buffer size
    _BUFSIZE = 1024

    # Possible responses from Logic
    _ACK = 'ACK'
    _NAK = 'NAK'

    def __init__(self, host, port):
        """
        Abstraction of the Saleae Logic socket API

        :param host: Hostname/IP of the Logic instance to connect to
        :type  host: str
        :param port: Port to connect to
        :type  port: int
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((host, port))
            self._sock.settimeout(2)

        except socket.error:
            # TODO: Handle error
            raise

    def request(self, cmd):

        try:
            self._sock.send(cmd + '\0')

            response = self._sock.recv(self._BUFSIZE).split('\n')

            result = response.pop()

            if result == 'NAK':
                raise NAKError
            elif result != 'ACK':
                raise ResponseError('Response neither "ACK" nor "NAK"')

            return response

        except socket.error:
            # TODO: Handle error
            raise

        except SaleaeError:
            # TODO: Handle error
            raise

    def get_connected_devices(self):
        """
        Fetches a list of all connected Saleae devices.

        :return: A list of dicts, containing:
            * 'index':      Device index (starting from one)
            * 'name':       Device name
            * 'type':       Device type
            * 'device_id':  64-bit device ID
            * 'active':     If device is currently active
        """

        devices = []

        for line in self.request('get_connected_devices'):

            fields = line.split(', ')

            if len(fields) < 4:
                raise ResponseError('get_connected_devices returned < 4 fields')

            active = (len(fields) == 5 and fields[4] == 'ACTIVE')

            devices.append({
                'index':     int(fields[0]),
                'name':      fields[1],
                'type':      fields[2],
                'device_id': int(fields[3], base=0),
                'active':    active
            })

        return devices
