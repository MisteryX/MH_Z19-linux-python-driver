#!/usr/bin/python3
import serial

__version__ = '1.0.0'
__author__ = 'Morskov Maksim'
__license__ = "Apache License 2.0. https://www.apache.org/licenses/LICENSE-2.0"

DEFAULT_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD_RATE = 9600


class MH_Z19:

    def __init__(self, port=DEFAULT_PORT, baud_rate=DEFAULT_BAUD_RATE):
        self.__port = port
        self.__baud_rate = DEFAULT_BAUD_RATE
        pass

    def is_plugged(self) -> bool:
        pass

    @staticmethod
    def __check_crc(data):
        crc = 0x00
        count = 1
        b = bytearray(data)
        while count < 8:
            crc += b[count]
            count = count + 1
        # Truncate to 8 bit
        crc %= 256
        # Invert number with xor
        crc = ~crc & 0xFF
        crc += 1
        return crc

    def measure(self) -> int:
        pass
