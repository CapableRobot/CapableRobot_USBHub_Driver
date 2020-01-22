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

class USBHubSPI(Lockable):

    CMD_SPI_ENABLE  = 0x60
    CMD_SPI_WRITE   = 0x61
    CMD_SPI_DISABLE = 0x62

    REG_SPI_DATA  = 0x2310

    def __init__(self, hub, enable=False):
        self.hub = hub
        self.enabled = False

        if enable:
            self.enable()

    def __enter__(self):
        while not self.try_lock():
            pass
        return self

    def __exit__(self, *exc):
        self.unlock()
        return False

    def enable(self):
        if self.enabled:
            return True

        try:
            self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_SPI_ENABLE, 0, 0, 0)
        except usb.core.USBError:
            logging.warn("USB Error in SPI Enable")
            return False

        self.enabled = True
        return True

    def disable(self):
        if not self.enabled:
            return True

        try:
            self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_SPI_DISABLE, 0, 0, 0)
        except usb.core.USBError:
            logging.warn("USB Error in SPI Disable")
            return False

        self.enabled = False
        return True

    def write(self, buf, start=0, end=None):
        if not self.enabled:
            self.enable()

        if not buf:
            return

        if end is None:
            end = len(buf)

        if start-end >= 256:
            raise ValueError('SPI interface cannot write a buffer longer than 256 elements')
            return False

        logging.debug("SPI Write : [{}]".format(" ".join([hex(v) for v in list(buf[start:end])])))

        value = end - start
        length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_SPI_WRITE, value, 0, buf[start:end], value)
        return length

    def readinto(self, buf, start=0, end=None, addr=''):
        if not self.enabled:
            self.enable()

        if not buf:
            return

        if end is None:
            end = len(buf)

        length = end - start 

        ## Need to offset the address for USB access
        address = self.REG_SPI_DATA + self.hub.REG_BASE_ALT

        ## Split 32 bit register address into the 16 bit value & index fields
        value = address & 0xFFFF
        index = address >> 16

        data = list(self.hub.handle.ctrl_transfer(REQ_IN, self.hub.CMD_REG_READ, value, index, length))

        if length != len(data):
            raise OSError('Incorrect data length')

        # 'readinto' the given buffer
        for i in range(end-start):  
            buf[start+i] = data[i]
        
        logging.debug("SPI Read [{}] : [{}]".format(" ".join([hex(v) for v in addr]), " ".join([hex(v) for v in list(data)])))
        
        

    def write_readinto(self, buffer_out, buffer_in, out_start=0, out_end=None, in_start=0, in_end=None):
        if not self.enabled:
            self.enable()

        if not buffer_out or not buffer_in:
            return

        if out_end is None:
            out_end = len(buffer_out)    

        if in_end is None:
            in_end = len(buffer_in)

        in_length = in_end - in_start
        out_length = out_end - out_start 
        value = out_length + in_length

        try:
            length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_SPI_WRITE, value, 0, buffer_out[out_start:out_end], out_length)
        except usb.core.USBError:
            raise OSError('Unable to setup SPI write_readinto')

        if length != 1:
            raise OSError('Incorrect response in write_readinto')

        self.readinto(buffer_in, start=in_start, end=in_end, addr=list(buffer_out[out_start:out_end]))

