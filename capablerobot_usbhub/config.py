# The MIT License (MIT)
#
# Copyright (c) 2019 Chris Osterwood for Capable Robot Components
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import time

import usb.core
import usb.util

from .util import *

_MEM_IDENT = 0x0904
_MEM_WRITE = 0x0914
_MEM_READ  = 0x0924

_CRC8_POLYNOMIAL = 0x31
_CRC8_INIT = 0xFF

_CMD_NOOP   = 0b000
_CMD_GET    = 0b001
_CMD_SET    = 0b010
_CMD_SAVE   = 0b100
_CMD_RESET  = 0b111

_WAIT = 0.1

_NAME_RO = [
    'power_errors',
    'power_measure_12',
    'power_measure_34',
]

_NAME_ADDR = dict(
    data_state          = 0x05,
    # power_errors        = 0x06,
    power_limits        = 0x07,
    power_measure_12    = 0x08,
    power_measure_34    = 0x09,
    highspeed_disable   = 0x10,
    loop_delay          = 0x11,
    external_heartbeat  = 0x12,
)

def _generate_crc(data):
    crc = _CRC8_INIT

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ _CRC8_POLYNOMIAL
            else:
                crc <<= 1

    return crc & 0xFF

class USBHubConfig:

    def __init__(self, hub, clear=False):
        self.hub = hub
        self._version = None

        if clear:
            self.clear()

    @property
    def version(self):
        if self._version is None:
            buf, _ = self.hub.register_read(addr=_MEM_IDENT, length=4)
            self._version = buf

        return self._version[0]

    @property
    def circuitpython_version(self):
        if self._version is None:
            buf, _ = self.hub.register_read(addr=_MEM_IDENT, length=4)
            self._version = buf

        return ".".join([str(v) for v in self._version[1:4]])

    def _read(self):
        buf, _ = self.hub.register_read(addr=_MEM_READ, length=4)
        crc = _generate_crc(buf[0:3])

        if crc == buf[3]:
            self.hub.register_write(addr=_MEM_READ, buf=[0,0,0,0])
            return buf[0:3]
        
        return None

    def _write_okay(self):
        buf, _ = self.hub.register_read(addr=_MEM_WRITE, length=4)

        if buf[0] >> 5 == _CMD_NOOP:
            return True

        return False

    def _write(self, buf):    
        crc = _generate_crc(buf[0:3])
        buf = buf[0:3] + [crc]
        return self.hub.register_write(addr=_MEM_WRITE, buf=buf)

    def read(self):
        buf   = self._read()

        if buf is None:
            return _CMD_NOOP, None, None

        cmd   = buf[0] >> 5
        name  = buf[0] & 0b11111
        value = buf[1] << 8 | buf[2]

        return cmd, name, value

    def write(self, cmd, name=None, value=0):
        if name is None:
            name_addr = 0
        else:
            name_addr = _NAME_ADDR[name]

        if name_addr > 0b11111:
            logging.error("Address of name '{}' is above 5 bit limit".format(name))

        while not self._write_okay():
            time.sleep(_WAIT)

        self._write([cmd << 5 | name_addr, (value >> 8) & 0xFF, value & 0xFF])

    def clear(self):
        self.hub.register_write(addr=_MEM_READ,  buf=[0,0,0,0])
        self.hub.register_write(addr=_MEM_WRITE, buf=[0,0,0,0])

    def device_info(self):
        return dict(
            firmware = self.version,
            circuitpython = self.circuitpython_version.split(".")
        )

    def reset(self, target="usb"):
        targets = ["usb", "mcu", "bootloader"]
        self.write(_CMD_RESET, value=targets.index(target))

    def save(self):
        info = self.device_info()

        if info["circuitpython"][0] == 5 and info["circuitpython"][1] < 2:
            logging.error("MCU must be upgraded to CircuitPython 5.2.0 or newer for filesystem saves to work.")
            return

        self.write(_CMD_SAVE)

        out = self.read()
        while out[0] != _CMD_SAVE:
            time.sleep(_WAIT)
            out = self.read()

        if out[2] == 0:
            logging.error("Save of the config.ini file failed.")
            logging.error("Please unmount the CIRCUITPY volume and try again.")

        return out[2]

    def get(self, name):
        self.write(_CMD_GET, name=name)

        out = self.read()
        while out[0] != _CMD_GET:
            time.sleep(_WAIT)
            out = self.read()

        return out[2]

    def set(self, name, value):
        if name in _NAME_RO:
            raise ValueError("Cannot set read-only parameter '{}'".format(name))

        self.write(_CMD_SET, name=name, value=value)

        out = self.read()
        while out[0] != _CMD_SET:
            time.sleep(_WAIT)
            out = self.read()

        return out[2]
