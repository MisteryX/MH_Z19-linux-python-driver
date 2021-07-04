#!/usr/bin/python3
import serial
import datetime as dt
import time

__version__ = '1.0.0'
__author__ = 'Morskov Maksim'
__license__ = "Apache License 2.0. https://www.apache.org/licenses/LICENSE-2.0"

DEFAULT_PORT = '/dev/ttyAMA0'
DEFAULT_BAUD_RATE = 9600
DEFAULT_TIMEOUT = 2  # seconds
SENSOR_CMD_WORD_SIZE = 9  # bytes
SENSOR_READ_DELAY = 0.1  # seconds
CRC8_SUM_BYTE_INDEX = 8
CMD_GET_CO2_LEVEL = b'\xff\x01\x86\x00\x00\x00\x00\x00\x79'
CMD_AUTO_ZERO_POINT_CALIBRATION_ON = b'\xff\x01\x79\xa0\x00\x00\x00\x00\xe6'
CMD_AUTO_ZERO_POINT_CALIBRATION_OFF = b'\xff\x01\x79\x00\x00\x00\x00\x00\x86'
REQUEST_CMD_HEADER_BYTE_INDEX = 0
REQUEST_CMD_CODE_BYTE_INDEX = 2
RESPONSE_CMD_CODE_BYTE_INDEX = 1
RESPONSE_HIGH_BYTE_INDEX = 2
RESPONSE_LOW_BYTE_INDEX = 3


class MH_Z19:

    def __init__(self, port=DEFAULT_PORT, baud_rate=DEFAULT_BAUD_RATE, timeout=DEFAULT_TIMEOUT):
        self.__port = port
        self.__baud_rate = baud_rate
        self.__timeout = timeout
        self.__log('Driver inited')

    def is_plugged(self) -> bool:
        return bool(self.measure())

    def __get_log_name(self):
        return self.__class__.__name__ + '.log'

    def __log(self, message):
        now = dt.datetime.now()
        prefix = '%0.4d-%0.2d-%0.2dZ%0.2d:%0.2d:%0.2d: ' % (
        now.year, now.month, now.day, now.hour, now.minute, now.second)
        with open(self.__get_log_name(), 'a') as log:
            log.write(prefix + message + '\n')

    @staticmethod
    def __get_crc8(data):
        crc = 0x00
        if len(data) != SENSOR_CMD_WORD_SIZE:
            raise MH_Z19Error(MH_Z19Error.DATA_ERROR, 'response={}'.format(data))
        count = 1
        while count < (SENSOR_CMD_WORD_SIZE - 1):
            crc += data[count]
            count = count + 1
        # Truncate to 8 bit
        crc %= 256
        # Invert number with xor
        crc = ~crc & 0xFF
        crc += 1
        return crc

    def __send_cmd(self, command: bytes, response_size=SENSOR_CMD_WORD_SIZE, read_delay=SENSOR_READ_DELAY) -> bytes:
        try:
            with serial.Serial(self.__port, self.__baud_rate, timeout=self.__timeout) as uart:
                uart.write(command)
                time.sleep(read_delay)
                response = uart.read(response_size)
                crc8 = self.__get_crc8(response)
                if crc8 != response[CRC8_SUM_BYTE_INDEX]:
                    raise MH_Z19Error(MH_Z19Error.CRC_ERROR,
                                      'Wrong CRC8! Calculated = {}, but response = {}'.format(crc8, response))
                return response
        except Exception as ex:
            errors = ', '.join([str(x) for x in ex.args])
            raise MH_Z19Error(MH_Z19Error.BUS_ERROR, 'Exception - ' + errors)

    def measure(self) -> int:
        data = self.__send_cmd(CMD_GET_CO2_LEVEL)
        if data[REQUEST_CMD_HEADER_BYTE_INDEX] != CMD_GET_CO2_LEVEL[REQUEST_CMD_HEADER_BYTE_INDEX] or \
                data[RESPONSE_CMD_CODE_BYTE_INDEX] != CMD_GET_CO2_LEVEL[REQUEST_CMD_CODE_BYTE_INDEX]:
            raise MH_Z19Error(MH_Z19Error.DATA_ERROR, 'cmd={}, response={}'.format(CMD_GET_CO2_LEVEL, data))
        return data[RESPONSE_HIGH_BYTE_INDEX] * 256 + data[RESPONSE_LOW_BYTE_INDEX]


class MH_Z19Error(Exception):
    """
    Custom exception for errors on sensor management
    """
    BUS_ERROR = 0x01
    DATA_ERROR = 0x02
    CRC_ERROR = 0x03

    def __init__(self, error_code=None, message=''):
        self.__error_code = error_code
        self.__message = message
        super().__init__(self.get_message())

    def get_message(self):
        if self.__error_code == MH_Z19Error.BUS_ERROR:
            return "Bus error: " + self.__message
        elif self.__error_code == MH_Z19Error.DATA_ERROR:
            return "Data error: " + self.__message
        elif self.__error_code == MH_Z19Error.CRC_ERROR:
            return "CRC error: " + self.__message
        else:
            return "Unknown error: " + self.__message

    def get_code(self):
        return self.__error_code
