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
import time

import usb.core
import usb.util

from .util import *

class USBHubI2C(Lockable):

    CMD_I2C_ENTER = 0x70
    CMD_I2C_WRITE = 0x71
    CMD_I2C_READ  = 0x72

    def __init__(self, hub, timeout=1000, attempts_max=5, attempt_delay=50, fake_probe=True):
        self.hub = hub
        self.enabled = False

        self.timeout = timeout

        ## Convert from milliseconds to seconds for sleep call
        self.attempt_delay = float(attempt_delay)/1000.0
        self.attempts_max = attempts_max

        self.fake_probe = fake_probe

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

        self.acquire_lock()

        try:
            self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_ENTER, value, 0, 0, timeout=self.timeout)
        except usb.core.USBError:
            self.release_lock()
            return False

        self.enabled = True

        self.release_lock()
        return True


    def write_bytes(self, addr, buf):
        """Write many bytes to the specified device. buf is a bytearray"""

        self.acquire_lock()

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        cmd = build_value(addr=(addr << 1))

        attempts = 0
        length = None

        while attempts < self.attempts_max:
            attempts += 1
            try:
                length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_WRITE, cmd, 0, list(buf), timeout=self.timeout)
                break
            except usb.core.USBError:
                time.sleep(self.attempt_delay)
                
                if attempts >= self.attempts_max:
                    self.release_lock()
                    raise OSError('Unable to perform sucessful I2C write')
                if attempts == 1:
                    logging.debug("I2C : Retry Write")

        self.release_lock()
        return length

    def read_bytes(self, addr, number, try_lock=True):
        """Read many bytes from the specified device."""

        if try_lock:
            self.acquire_lock()

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        cmd = build_value(addr=(addr<<1)+1)
        
        attempts = 0
        data = None

        while attempts < self.attempts_max:
            attempts += 1
            try:
                data = list(self.hub.handle.ctrl_transfer(REQ_IN+1, self.CMD_I2C_READ, cmd, 0, number, timeout=self.timeout))
                break
            except usb.core.USBError:
                time.sleep(self.attempt_delay)
                
                if attempts >= self.attempts_max:
                    self.release_lock()
                    raise OSError('Unable to perform sucessful I2C read')
                if attempts == 1:
                    logging.debug("I2C : Retry Read")

        self.release_lock()
        return data 

    def read_i2c_block_data(self, addr, register, number=32):
        """Perform a read from the specified cmd register of device.  Length number
        of bytes (default of 32) will be read and returned as a bytearray.
        """

        self.acquire_lock()

        # Passed in address is in 7-bit form, so shift it
        # and add the start / stop flags
        i2c_addr = addr << 1
        cmd = build_value(addr=i2c_addr, nack=False)

        attempts = 0
        
        while attempts < self.attempts_max:
            attempts += 1
            try:
                length = self.hub.handle.ctrl_transfer(REQ_OUT+1, self.CMD_I2C_WRITE, cmd, 0, [register], timeout=self.timeout)
                break
            except usb.core.USBError as e:
                if "permission" in str(e):
                    self.hub.main.print_permission_instructions()
                    self.release_lock()
                    sys.exit(0)

                time.sleep(self.attempt_delay)
                
                if attempts >= self.attempts_max:
                    self.release_lock()
                    raise OSError('Unable to perform sucessful I2C read block data')
                if attempts == 1:
                    logging.debug("I2C : Retry Read Block")

        if length != 1:
            self.release_lock()
            raise OSError('Unable to perform sucessful I2C read block data')
            
        ## read_bytes will release the lock created here, and
        ## we have not release it, so there is no need to grab a new one
        return self.read_bytes(addr, number, try_lock=False)

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        if end is None:
            end = len(buffer)

        if self.fake_probe and buffer == b'':
            logging.debug("I2C : skipping probe of {}".format(address))
            return

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