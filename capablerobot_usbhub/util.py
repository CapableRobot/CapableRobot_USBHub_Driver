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

import usb.util

REQ_OUT = usb.util.build_request_type(
    usb.util.CTRL_OUT,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

REQ_IN = usb.util.build_request_type(
    usb.util.CTRL_IN,
    usb.util.CTRL_TYPE_VENDOR,
    usb.util.CTRL_RECIPIENT_DEVICE)

class Lockable():
    """An object that must be locked to prevent collisions on a microcontroller resource."""
    _locked = False

    def try_lock(self):
        """Attempt to grab the lock. Return True on success, False if the lock is already taken."""
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self):
        """Release the lock so others may use the resource."""
        if self._locked:
            self._locked = False
        else:
            raise ValueError("Not locked")

def bits_to_bytes(bits):
    return int(bits / 8)

def int_from_bytes(xbytes, endian='big'):
    return int.from_bytes(xbytes, endian)

def hexstr(value):
    return hex(value).upper().replace("0X","")

def build_value(start=True, stop=True, nack=True, addr=0):
    flags = 0
    if nack:
        flags += 4
    if start:
        flags += 2
    if stop:
        flags += 1

    return (flags << 8) + addr

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def get_bit(value, bit):
    return (value & (1<<bit)) > 0

def set_bit_to(value, bit, state):
    if state:
        return value | (1<<bit)
        
    return value & ~(1<<bit)


def register_keys(parsed, sort=True):
    if sort:
        keys = sorted(parsed.body.keys())
    else:
        parsed.body.keys()

    ## Remove any key which starts with 'reserved' or '_'
    return list(filter(lambda key: key[0] != '_' and ~key.startswith("reserved") , keys))


import math

class BitVector:
    def __init__(self, val):
        self._val = val

    def __setitem__(self, item, value):
        if isinstance(item, slice):
            if item.step not in (1, None):
                raise ValueError('only step=1 supported')

            # clear out bit slice
            clean_mask = (2**(item.stop+1)-1)^(2**(item.start)-1)
            self._val = self._val ^ (self._val & clean_mask)

            # set new value
            self._val = self._val | (value<<item.start)
        else:
            raise TypeError('non-slice indexing not supported')

    def __getitem__(self, item):
        if isinstance(item, slice):
            if item.step not in (1, None):
                raise ValueError('only step=1 supported')

            return (self._val>>item.start)&(2**(item.stop-item.start+1)-1)
        else:
            raise TypeError('non-slice indexing not supported')

    def __int__(self):
        return self._val
