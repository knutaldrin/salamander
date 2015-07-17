"""
Api functions for Saleae Logic
"""

import socket

__all__ = ['connect', 'SaleaeError', 'NAKError', 'ResponseError']

# Possible responses from Logic
_ACK = 'ACK'
_NAK = 'NAK'

#: Receive buffer size
_BUFSIZE = 1024

#: Timeout length
_TIMEOUT = 2


def connect(host='127.0.0.1', port=10429):
    """
    Create a new connection to Saleae Logic.

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
            self._sock.settimeout(_TIMEOUT)

        except socket.error:
            # TODO: Handle error
            raise

    def request(self, cmd, *args):
        """
        Make a request to the Saleae Logic socket API.

        :param   cmd: API command
        :param   args: Command arguments
        :return: List of lines returned from Logic. Does not return ACK/NAK.
        :rtype:  [str]
        """

        try:
            # Filter function for properly formatting the command with/without arguments
            def filter_param(param):
                if param is None:
                    return ''
                elif type(param) is list:
                    return ','.join(filter_param(field) for field in param)
                else:
                    return str(param)

            params = ','.join(filter_param(param) for param in args)

            self._sock.send(''.join([
                cmd,
                ',' if params else '',
                params,
                '\0'
            ]))

            response = self._sock.recv(_BUFSIZE).split('\n')

            result = response.pop()

            if result == _NAK:
                raise NAKError
            elif result != _ACK:
                raise ResponseError('Response neither "ACK" nor "NAK"')

            return response

        except socket.error:
            # TODO: Handle error
            raise

        except SaleaeError:
            # TODO: Handle error
            raise

    def set_trigger(self, params):
        """
        Set triggers for active channels.

        Number of values must match number of channels in Logic.

        :param params: list of values
        """

        edge = False

        for param in params:
            if param not in (None, 'high', 'low', 'negedge', 'posedge'):
                raise ValueError('Trigger values must be high|low|negedge|posedge')

            if param in ('negedge', 'posedge'):
                if edge:
                    raise ValueError('Cannot have more than one edge trigger')
                edge = True

        self.request('set_trigger', *params)

    def set_num_samples(self, samples):
        """
        Sets number of samples to capture.

        :param samples: Number of samples
        """

        self.request('set_num_samples', samples)

    def set_sample_rate(self, digital_sample_rate, analog_sample_rate):
        """
        Sets digital and analog sample rates.

        The sample rates must be valid for the current performance level and channel combination.
        :see: get_all_sample_rates

        :param digital_sample_rate:
        :param analog_sample_rate:
        """

        self.request('set_sample_rate', digital_sample_rate, analog_sample_rate)

    def get_all_sample_rates(self):
        """
        Get all valid digital/analog sample rate combinations
        for the current performance level and channel combination.

        :return: list of (digital_sample_rate, analog_sample_rate)
        :rtype: [(int, int)]
        """

        sample_rates = []

        response = self.request('get_all_sample_rates')

        for line in response:
            (digital, analog) = line.split(', ')
            sample_rates.append((int(digital), int(analog)))

        return sample_rates

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

    def get_performance(self):
        """
        The currently selected performance level.

        :return: Performance value
        :rtype:  int
        """
        return int(self.request('get_performance')[0])

    def set_performance(self, performance):
        """
        Sets the performance level. Valid options are: 20, 25, 33, 50 and 100.

        Note: This call will change the sample rate currently selected.

        :param performance: Wanted performance level
        """

        self.request('set_performance', performance)

    def get_capture_pretrigger_buffer_size(self):
        """
        Current pretrigger buffer size.

        :return int: Buffer size
        """

        return int(self.request('get_capture_pretrigger_buffer_size')[0])

    def set_capture_pretrigger_buffer_size(self, size):
        """
        Sets pretrigger buffer size.

        :param size: Buffer size
        """

        self.request('set_capture_pretrigger_buffer_size', size)

    def select_active_device(self, index):
        """
        Make the selected device active.
        NOTE: index starts at one, not zero.

        :param index: Device index, starting from one
        """

        self.request('select_active_device', index)

    def get_active_channels(self):
        """
        Get active digital and analog channels
        :return: Tuple containing (digital, analog)
        :rtype:  [int], [int]
        """

        response = self.request('get_active_channels')[0].split(',')
        response = [field.strip() for field in response]

        analog_pos = response.index('analog_channels')

        digital = [int(ch) for ch in response[1:analog_pos]]
        analog = [int(ch) for ch in response[analog_pos+1:]]

        return digital, analog

    def set_active_channels(self, digital, analog):
        """
        Sets the specified channels to be active, and the ones not specified as inactive.

        :param digital: Channels to record digital
        :param analog:  Channels to record analog
        """

        self.request('set_active_channels', 'digital_channels', digital, 'analog_channels', analog)

