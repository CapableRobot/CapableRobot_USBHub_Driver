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

def bits_to_bytes(bits):
    return int(bits / 8)

def int_from_bytes(xbytes, endian='big'):
    return int.from_bytes(xbytes, endian)

def hexstr(value):
    return hex(value).upper().replace("0X","")

def split(value):
    return [value & 0xFF, value >> 8]

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