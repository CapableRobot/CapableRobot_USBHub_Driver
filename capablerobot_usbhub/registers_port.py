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

from construct import *

port_power_status = BitStruct(
    Padding(3),
    "port4" / BitsInteger(1),
    "port3" / BitsInteger(1),
    "port2" / BitsInteger(1),
    "port1" / BitsInteger(1),
    Padding(1),
)

port_remap12 = BitStruct(
    "port2" / BitsInteger(4),
    "port1" / BitsInteger(4),
)

port_remap34 = BitStruct(
    "port4" / BitsInteger(4),
    "port3" / BitsInteger(4),
)

port_power_state = BitStruct(
    "port3" / BitsInteger(2),
    "port2" / BitsInteger(2),
    "port1" / BitsInteger(2),
    "port0" / BitsInteger(2),
    Padding(6),
    "port4" / BitsInteger(2),
)

port_connection = BitStruct(
    Padding(3),
    "port4" / BitsInteger(1),
    "port3" / BitsInteger(1),
    "port2" / BitsInteger(1),
    "port1" / BitsInteger(1),
    "port0" / BitsInteger(1),
)

port_device_speed = BitStruct(
    "port4" / BitsInteger(2),
    "port3" / BitsInteger(2),
    "port2" / BitsInteger(2),
    "port1" / BitsInteger(2),
)

port_power_select_1 = BitStruct(
    "combined_mode" / BitsInteger(1),
    "gang_mode" / BitsInteger(1),
    Padding(2),
    "source" / BitsInteger(4),
)

port_power_select_2 = BitStruct(
    "combined_mode" / BitsInteger(1),
    "gang_mode" / BitsInteger(1),
    Padding(2),
    "source" / BitsInteger(4),
)

port_power_select_3 = BitStruct(
    "combined_mode" / BitsInteger(1),
    "gang_mode" / BitsInteger(1),
    Padding(2),
    "source" / BitsInteger(4),
)

port_power_select_4 = BitStruct(
    "combined_mode" / BitsInteger(1),
    "gang_mode" / BitsInteger(1),
    Padding(2),
    "source" / BitsInteger(4),
)

