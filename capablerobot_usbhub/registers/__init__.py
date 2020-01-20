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

from .main import *
from .port import *
from .gpio import *

register = Struct(
    "addr" / Int16ub,
    "len" / Int8ub,
    "body" / Switch(this.addr, {
        0: main_revision,
        2304: gpio_output_enable,
        2320: gpio_input_enable,
        2336: gpio_output,
        2352: gpio_input,
        2368: gpio_pull_up,
        2384: gpio_pull_down,
        2400: gpio_open_drain,
        2528: gpio_debounce,
        2544: gpio_debounce_time,
        12288: main_vendor_id,
        12290: main_product_id,
        12292: main_device_id,
        12294: main_hub_configuration,
        12295: main_hub_configuration_2,
        12296: main_hub_configuration_3,
        12548: main_hub_control,
        12538: main_port_swap,
        12695: main_suspend,
        12517: port_power_status,
        12539: port_remap12,
        12540: port_remap34,
        12544: port_power_state,
        12692: port_connection,
        12693: port_device_speed,
        15360: port_power_select_1,
        15364: port_power_select_2,
        15368: port_power_select_3,
        15372: port_power_select_4,
    }),
)

registers = GreedyRange(register)
