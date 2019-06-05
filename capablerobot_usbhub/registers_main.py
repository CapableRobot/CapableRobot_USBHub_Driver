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

main_revision = BitStruct(
    "device_id" / BitsInteger(16),
    Padding(8),
    "revision_id" / BitsInteger(8),
)

main_vendor_id = BitStruct(
    "value" / BitsInteger(16),
)

main_product_id = BitStruct(
    "value" / BitsInteger(16),
)

main_device_id = BitStruct(
    "value" / BitsInteger(16),
)

main_hub_configuration = BitStruct(
    "self_power" / BitsInteger(1),
    "vsm_disable" / BitsInteger(1),
    "hs_disable" / BitsInteger(1),
    "mtt_enable" / BitsInteger(1),
    "eop_disable" / BitsInteger(1),
    "current_sense" / BitsInteger(2),
    "port_power" / BitsInteger(1),
    Padding(2),
    "oc_timer" / BitsInteger(2),
    "compound" / BitsInteger(1),
    Padding(3),
    Padding(4),
    "prtmap_enable" / BitsInteger(1),
    Padding(2),
    "string_enable" / BitsInteger(1),
)

main_hub_configuration_1 = BitStruct(
    "self_power" / BitsInteger(1),
    "vsm_disable" / BitsInteger(1),
    "hs_disable" / BitsInteger(1),
    "mtt_enable" / BitsInteger(1),
    "eop_disable" / BitsInteger(1),
    "current_sense" / BitsInteger(2),
    "port_power" / BitsInteger(1),
)

main_hub_configuration_2 = BitStruct(
    Padding(2),
    "oc_timer" / BitsInteger(2),
    "compound" / BitsInteger(1),
    Padding(3),
)

main_hub_configuration_3 = BitStruct(
    Padding(4),
    "prtmap_enable" / BitsInteger(1),
    Padding(2),
    "string_enable" / BitsInteger(1),
)

main_port_swap = BitStruct(
    Padding(3),
    "port4" / BitsInteger(1),
    "port3" / BitsInteger(1),
    "port2" / BitsInteger(1),
    "port1" / BitsInteger(1),
    "port0" / BitsInteger(1),
)

main_hub_control = BitStruct(
    Padding(6),
    "lpm_disable" / BitsInteger(1),
    "reset" / BitsInteger(1),
)

main_suspend = BitStruct(
    Padding(7),
    "suspend" / BitsInteger(1),
)

