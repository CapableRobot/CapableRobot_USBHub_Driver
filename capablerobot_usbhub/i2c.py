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
import sys

import usb.core
import usb.util

from .util import *

class USBHubI2C(Lockable):

    CMD_I2C_ENTER = 0x70
    CMD_I2C_WRITE = 0x71
    CMD_I2C_READ  = 0x72

    def __init__(self, hub):
        self.hub = hub
        self.enabled = False

        self.enable()

    def enable(self, freq=100):

        if self.enabled:
            return True

        value = 0x3131
        # if freq == 100:
        #     value = 0x3131
        # elif freq == 400:
        #     value = 0x0A00
        # elif freq == 250:
        #     value = 0x081B
        # elif freq == 200:
        #     value = 0x1818
        # elif freq == 80:
        #     value = 0x3D3E
        # elif freq == 50:
        #     value = 0x6363

        if freq != 100:
            raise ValueError('Currently only 100 kHz I2C operation is supported')

        try:
            self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_ENTER, value, 0, 0)
        except usb.core.USBError:
            logging.warn("USB Error in I2C Enable")
            return False

        self.enabled = True

        return True


    def write_bytes(self, addr, buf):
        """Write many bytes to the specified device. buf is a bytearray"""

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        cmd = build_value(addr=(addr << 1))

        try:
            length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_WRITE, cmd, 0, list(buf))
        except usb.core.USBError:
            raise OSError('Unable to setup I2C write.  Likely that slave address is incorrect')

        return length

    def read_bytes(self, addr, number):
        """Read many bytes from the specified device."""

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        cmd = build_value(addr=(addr<<1)+1)

        return list(self.handle.ctrl_transfer(REQ_IN+1, self.CMD_I2C_READ, cmd, 0, number))

    def read_i2c_block_data(self, addr, register, number=32):
        """Perform a read from the specified cmd register of device.  Length number
        of bytes (default of 32) will be read and returned as a bytearray.
        """

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        i2c_addr = addr << 1
        cmd = build_value(addr=i2c_addr, nack=False)

        try:
            length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_WRITE, cmd, 0, [register])
        except usb.core.USBError as e:
            if "permission" in str(e):
                self.hub.main.print_permission_instructions()
                sys.exit(0)
            else:
                raise OSError('Unable to setup I2C read.  Likely that slave address is incorrect')

        if length != 1:
            raise OSError('Unable to setup I2C read')

        cmd = build_value(addr=i2c_addr+1)
        return list(self.hub.handle.ctrl_transfer(REQ_IN+1, self.CMD_I2C_READ, cmd, 0, number))

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        if end is None:
            end = len(buffer)
        self.write_bytes(address, buffer[start:end])

    def readfrom_into(self, address, buffer, *, start=0, end=None, stop=True):
        if end is None:
            end = len(buffer)

        readin = self.read_bytes(address, end-start)
        for i in range(end-start):
            buffer[i+start] = readin[i]

    def writeto_then_readfrom(self, address, buffer_out, buffer_in, *,
                       out_start=0, out_end=None,
                       in_start=0, in_end=None, stop=False):
        if out_end is None:
            out_end = len(buffer_out)
        if in_end is None:
            in_end = len(buffer_in)
        if stop:
            # To generate a stop in linux, do in two transactions
            self.writeto(address, buffer_out, start=out_start, end=out_end, stop=True)
            self.readfrom_into(address, buffer_in, start=in_start, end=in_end)
        else:
            # To generate without a stop, do in one block transaction
            if out_end-out_start != 1:
                raise NotImplementedError("Currently can only write a single byte in writeto_then_readfrom")
            readin = self.read_i2c_block_data(address, buffer_out[out_start:out_end][0], in_end-in_start)
            for i in range(in_end-in_start):
                buffer_in[i+in_start] = readin[i]