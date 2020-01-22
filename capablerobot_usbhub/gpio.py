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

import usb.core
import usb.util

from .util import *

_OUTPUT_ENABLE  = 0x0900
_INPUT_ENABLE   = 0x0910
_OUTPUT         = 0x0920
_INPUT          = 0x0930
_PULL_UP        = 0x0940
_PULL_DOWN      = 0x0950
_OPEN_DRAIN     = 0x0960
_DEBOUNCE       = 0x09E0
_DEBOUNCE_TIME  = 0x09F0

## GPIO 0 is interally GPIO6,  so it's on the  6th bit
## GPIO 1 is interally GPIO11, so it's on the 11th bit
_GPIO0_BIT = [0, 6]
_GPIO1_BIT = [1, 3]
_GPIOS = [_GPIO0_BIT, _GPIO1_BIT]

class USBHubGPIO:

    def __init__(self, hub):
        self.hub = hub

        self._io0_output_config = None
        self._io0_input_config  = None
    
        self._io1_output_config = None
        self._io1_input_config  = None

    def _read(self, addr):
        data, _ = self.hub.register_read(addr=addr, length=4)
        return data

    def configure(self, ios=[], output=None, input=None, pull_down=None, pull_up=None, open_drain=None):
        
        if output is not None:
            self.configure_output(ios=ios, value=output)

        if input is not None:
            self.configure_input(ios=ios, value=input)

        if pull_down is not None:
            self.configure_pull_down(ios=ios, value=pull_down)

        if pull_up is not None:
            self.configure_pull_up(ios=ios, value=pull_up)

        if open_drain is not None:
            self.configure_open_drain(ios=ios, value=open_drain)

    def _generic_configure(self, addr, ios, value):
        current = self._read(addr=addr)
        desired = current.copy()

        if 0 in ios:
            if addr == _OUTPUT_ENABLE:
                self._io0_output_config = value
            if addr == _INPUT_ENABLE:
                self._io0_input_config = value

            desired[_GPIO0_BIT[0]] = set_bit_to(desired[_GPIO0_BIT[0]], _GPIO0_BIT[1], value)            

        if 1 in ios:
            if addr == _OUTPUT_ENABLE:
                self._io1_output_config = value
            if addr == _INPUT_ENABLE:
                self._io1_input_config = value

            desired[_GPIO1_BIT[0]] = set_bit_to(desired[_GPIO1_BIT[0]], _GPIO1_BIT[1], value)

        if current != desired:
            self.hub.register_write(addr=addr, buf=desired)

    def configure_output(self, ios, value):
        self._generic_configure(_OUTPUT_ENABLE, ios, value)

    def configure_input(self, ios, value):
        self._generic_configure(_INPUT_ENABLE, ios, value)

    def configure_pull_up(self, ios, value):
        self._generic_configure(_PULL_UP, ios, value)

    def configure_pull_down(self, ios, value):
        self._generic_configure(_PULL_DOWN, ios, value)

    def configure_open_drain(self, ios, value):
        self._generic_configure(_OPEN_DRAIN, ios, value)

    @property
    def io(self):
        if not self._io0_input_config:
            logging.warn("IO0 is not configured as an input, but is being read")

        if not self._io1_input_config:
            logging.warn("IO1 is not configured as an input, but is being read")
    
        value = self._read(addr=_INPUT)
        io0 = get_bit(value[_GPIO0_BIT[0]], _GPIO0_BIT[1])
        io1 = get_bit(value[_GPIO1_BIT[0]], _GPIO1_BIT[1])

        return (io0, io1)

    @property
    def io0(self):
        if not self._io0_input_config:
            logging.warn("IO0 is not configured as an input, but is being read")

        value = self._read(addr=_INPUT)
        return get_bit(value[_GPIO0_BIT[0]], _GPIO0_BIT[1])

    @io0.setter
    def io0(self, value):
        if not self._io0_output_config:
            logging.warn("IO0 is not configured as an output, but is being set")

        current = self._read(addr=_OUTPUT)
        desired = current.copy()
        desired[_GPIO0_BIT[0]] = set_bit_to(desired[_GPIO0_BIT[0]], _GPIO0_BIT[1], value)

        if current != desired:
            self.hub.register_write(addr=_OUTPUT, buf=desired)

    @property
    def io1(self):
        if not self._io1_input_config:
            logging.warn("IO1 is not configured as an input, but is being read")

        value = self._read(addr=_INPUT)
        return get_bit(value[_GPIO1_BIT[0]], _GPIO1_BIT[1])

    @io1.setter
    def io1(self, value):
        if not self._io1_output_config:
            logging.warn("IO1 is not configured as an output, but is being set")

        current = self._read(addr=_OUTPUT)
        desired = current.copy()
        desired[_GPIO1_BIT[0]] = set_bit_to(desired[_GPIO1_BIT[0]], _GPIO1_BIT[1], value)

        if current != desired:
            self.hub.register_write(addr=_OUTPUT, buf=desired)
